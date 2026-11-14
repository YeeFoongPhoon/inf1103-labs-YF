# --- Imports --- #
import os
import json
import time
import re
import random
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Callable
from dotenv import load_dotenv
from google import genai
from google.genai import errors     

# ==========================================
# 1. ROBUST DATA MODELS
# ==========================================
class PipelineException(Exception): """Base exception for pipeline failures."""
class ClientException(PipelineException): """Raised when the LLM client fails."""
class ParseException(PipelineException): """Raised when parsing fails."""
class ValidationException(PipelineException): """Raised when validation fails."""

# ==========================================
# 2. DATA MODELS (SRP)
# ==========================================

class RecipeRecord:
    """Represents the input data with pre-flight validation."""
    def __init__(self, ingredients: Dict[str, str], allergies: List[str] = None, dietary_prefs: List[str] = None, pax: str = "1"):
        # Input Validation: Prevent bad data before it hits the API
        if not ingredients or not isinstance(ingredients, dict):
            raise ValueError("Ingredients must be a non-empty dictionary.")
        if not str(pax).isdigit() or int(pax) < 1:
            raise ValueError("Serving size (pax) must be a numeric string representing 1 or more.")

        self.ingredients = ingredients
        self.allergies = allergies or []
        self.dietary_preferences = dietary_prefs or []
        self.pax = pax
# ==========================================
# 3. OCP AND SRP
# ==========================================
class RetryStrategy(ABC):
    @abstractmethod
    def execute(self, action: Callable[[], Any]) -> Any:
        pass

class ExponentialBackoffRetry(RetryStrategy):
    def __init__(self, max_retries: int = 3, base_delay: int = 2):
        self.max_retries = max_retries
        self.base_delay = base_delay
       

    def execute(self, action: Callable[[], Any]) -> Any:
        for attempt in range(1, self.max_retries + 1):
            try:
                return action()
            except Exception as e:
            
                if attempt == self.max_retries:
                    raise ClientException(f"Max retries reached. Last error: {e}") from e
                
                sleep_time = (self.base_delay * (2 ** (attempt - 1))) + random.uniform(0.1, 1.5)
                time.sleep(sleep_time)

class ValidationRule(ABC):
    @abstractmethod
    def check(self, data: Dict[str, Any]) -> List[str]:
        pass

class RequiredKeysRule(ValidationRule):
    def __init__(self, required_keys: set):
        self.required_keys = required_keys

    def check(self, data: Dict[str, Any]) -> List[str]:
        missing = [key for key in self.required_keys if key not in data]
        return [f"Missing required keys: {', '.join(missing)}"] if missing else []

class FieldTypeRule(ValidationRule):
    def __init__(self, field_name: str, expected_type: type):
        self.field_name = field_name
        self.expected_type = expected_type

    def check(self, data: Dict[str, Any]) -> List[str]:
        val = data.get(self.field_name)
        if val is not None and not isinstance(val, self.expected_type):
            return [f"'{self.field_name}' must be of type {self.expected_type.__name__}."]
        return []

# ==========================================
# 4. STRICT INTERFACES (LSP)
# ==========================================
class PromptBuilder(ABC):
    """Interface for constructing LLM prompts from input records."""
    @abstractmethod
    def build(self, record: Dict[str, Any]) -> str:
        pass


class LLMClient(ABC):
    """Interface for calling an LLM API.""" 
    @abstractmethod
    def call(self, prompt: str) -> str:
        pass


class ResponseParser(ABC):
    # LSP check: The return type is strictly a Dictionary. Failures raise ParseException.
    @abstractmethod
    def parse(self, raw: str) -> Dict[str, Any]:
        pass


class ResponseValidator(ABC):
    # LSP check: The return type is strictly a Dictionary. Failures raise ValidationException.
    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pass
# ==========================================
# 5. CONCRETE IMPLEMENTATIONS
# ==========================================
class RecipePromptBuilder(PromptBuilder):
      def build(self, record: RecipeRecord) -> str:
        return  f"""You are a recipe generator. Generate a recipe using this list of ingredients and their provided amounts. 
    Not all ingredients/amounts have to be used to completion for each recipe but do not include ingredients or 
    quantities not listed. Take into consideration the user's dietary preferences and allergies inputted below 
    as well. Include the serving sizes and time taken for each recipe. Convert any quantities of online recipes found 
    online to grams and millimeters. Do not include any suggestions to modify the recipes. Include a list of 
    utensils needed, and time taken for each step of the recipe. Include how much of each ingredient is used 
    in each step while describing the step. If there are not enough ingredients to make a legitimate recipe, 
    indicate true in the JSON file, otherwise indicate false. Remove any hazardous or inedible ingredients. 
    and write them at the bottom of the JSON file. Return the confidence level of the recipe recommendation 
    from 0 to 1 for evaluating it's usability. 

    If the recipe detects a conflict in dietary preferences/allergies and ingredients provided, try to avoid using them
    and put them into hazardous ingredients list. If it is possible to avoid the conflict, carry on as per 
    normal and return original outputs.
    
    However, if the recipe has to have ingredients provided that conflicts with dietary preferences/allergies, do not include 
    the conflicting dietary preferences/allergies within the response. The hazardous ingredients should also contain the 
    conflicting ingredients, then the confidence score should be strictly marked down in the case of conflict. 
    
    Ingredients: {', '.join(f"{k} ({v})" for k, v in record.ingredients.items())}, 
    Allergies: {', '.join(record.allergies) if record.allergies else 'None'},
    Dietary Preferences: {', '.join(record.dietary_preferences) if record.dietary_preferences else 'None'},
    Serving size: {record.pax},
  
    The response should be in strictly valid JSON format with the following keys and types: 
    recipe: str, ingredients: dict, instructions: dict, confidence: int or float, dietary_preferences: list, hazardous_ingredients: dict, equipment: list, insufficient_ingredients: bool

    Examples of instructions should be formatted as: 
    "instructions": {{
        "1": {{ "step": 'Instruction 1', "time_taken": '5min' }}, 
        "2": {{ "step": 'Instruction 2', "time_taken": '2min' }},
    }}

    Examples of dietary preferences/allergies should be formatted as:
    dietary_preferences: ['halal', 'vegetarian']
    allergies: ['fish', 'peanuts']"""


class GeminiLLMClient(LLMClient):
    def __init__(self, api_key: str, retry_strategy: RetryStrategy):
        self.client = genai.Client(api_key=api_key)
        self.retry_strategy = retry_strategy
        self.model = "gemini-3.1-flash-lite"    

    def call(self, prompt: str) -> str:
        # Client ONLY handles making the request. Retries are delegated to the strategy.
        def _make_request():
            response_text = ""
            interaction = self.client.interactions.create(model=self.model, input=prompt, stream=True)
            for event in interaction:
                if hasattr(event, "error") and event.error:
                    raise Exception(f"API Error ({event.error.code}): {event.error.message}")
                if hasattr(event, "delta") and hasattr(event.delta, "text") and event.delta.text:
                    response_text += event.delta.text
            return response_text

        return self.retry_strategy.execute(_make_request)

class JSONRecipeParser(ResponseParser):
    def parse(self, raw: str) -> Dict[str, Any]:
        if not raw:
            raise ParseException("No response received from the API.")

        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if not json_match:
            raise ParseException(f"No JSON object found in response. Snippet: {raw[:100]}...")

        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError as e:
            raise ParseException(f"JSON parsing error: {e}")

class RuleBaseValidator(ResponseValidator):
    def __init__(self, rules: List[ValidationRule]):
        self.rules = rules

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        for rule in self.rules:
            errors.extend(rule.check(data))
        
        if errors:
            raise ValidationException("Validation Failed:\n- " + "\n- ".join(errors))
        return data
# ==========================================
# 6. PIPELINE & APPLICATION BOOTSTRAPPING
# ==========================================
class RecipePipeline:
    """Coordinates the dependencies to process a recipe record."""
    def __init__(self, builder: PromptBuilder, client: LLMClient, parser: ResponseParser, validator: ResponseValidator):
        self.builder = builder
        self.client = client
        self.parser = parser
        self.validator = validator

    def process(self, record: RecipeRecord) -> Dict[str, Any]:
        
        
        prompt = self.builder.build(record)
        raw_response = self.client.call(prompt)
        parsed_response = self.parser.parse(raw_response)
        validated_response = self.validator.validate(parsed_response)
        
        
        return validated_response

class PipelineFactory:
   @staticmethod
   def create_recipe_pipeline(api_key: str) -> RecipePipeline:
        retry_strategy = ExponentialBackoffRetry(max_retries=3, base_delay=2)
        
        validation_rules = [
            RequiredKeysRule({"recipe", "ingredients", "instructions", "confidence"}),
            FieldTypeRule("recipe", str),
            FieldTypeRule("ingredients", dict),
            FieldTypeRule("equipment", list)
        ]

        return RecipePipeline(
            builder=RecipePromptBuilder(),
            client=GeminiLLMClient(api_key=api_key, retry_strategy=retry_strategy),
            parser=JSONRecipeParser(),
            validator=RuleBaseValidator(rules=validation_rules)
        )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    load_dotenv(dotenv_path="./.env")
    
    try:
        pipeline = PipelineFactory.create_recipe_pipeline(os.getenv("GENAI_API_KEY"))
        record = RecipeRecord(
            ingredients={"chicken": "500g"}, allergies=["peanuts"], dietary_prefs=["high protein"], pax="2"
        )
        
        result = pipeline.process(record)
        print(json.dumps(result, indent=2))
        
    except PipelineException as e:
       # TBA
    except Exception as e:
       # TBA