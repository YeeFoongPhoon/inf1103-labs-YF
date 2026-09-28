
import json
def load_inventory(filename="inventory.json"):
   
   try:
       with open(filename, "r") as file:
           return json.load(file)
       return {
                "transactions": data.get("transactions", []),
                "total": data.get("total", 0),
                "error_count": data.get("error_count", 0),
                "current_total": data.get("current_total", 0),
                "order_number": data.get("order_number", 1)
            }
   except FileNotFoundError:
       return {"transactions": [], "total": 0, "error_count": 0, "current_total": 0, "order_number": 1}
   except json.JSONDecodeError:
       print(f"Error: {filename} is not a valid JSON file. Starting with empty inventory.")
       return {"transactions": [], "total": 0, "error_count": 0, "current_total": 0, "order_number": 1}


  
def get_valid_input(product_name, user_input, total, error_count, tax_amount, current_total, transactions, order_number): 
  if user_input.lower() == "q" or product_name.lower() == "q":
     return save_inventory(total, error_count, tax_amount, current_total, transactions, order_number)
  try:
    inventory = int(user_input)
    print(f"Success! You entered the integer of the stock count {inventory}")
    if inventory < 0:
      raise ValueError
    if inventory > 500:
        print("Inventory count is too high. Please enter a value less than or equal to 500.\n")
        return total, error_count, False,0,transactions,order_number
    total += inventory
    transaction = {
            "product_name": product_name,
            "number_of_items": inventory,
            "order_number": order_number
        }
    transactions.append(transaction)
    order_number += 1
    print(f"-> Added {inventory}. Current total stock count: {total}\n")
    return total, error_count, True, inventory,transactions,order_number
  except ValueError:
    print("Inventory Invalid or you have entered a non integer value. Please enter a valid integer of the stock count or 'q' to quit.\n")
    error_count += 1
    return total, error_count, True, 0,transactions,order_number


def process_delivery(current_total, inventory):
  delivery_cost = inventory * 10
  current_total += delivery_cost
  print(f"-> Delivery Cost Added: ${delivery_cost} (based on {inventory} stock units). Cumulative Delivery Cost: ${current_total}\n")
  return current_total

def calculate_tax(amount):
  current_total = amount
  tax_rate = 0.10
  tax_amount = current_total * tax_rate
  print(f"Tax amount for the total deliveries processed: {tax_amount:.2f}\n")
  return tax_amount


def save_inventory(total, error_count, tax_amount, current_total, transactions, order_number):
    saved_data = {
        "transactions": transactions,
        "total": total,
        "error_count": error_count,
        "current_total": current_total,
        "order_number": order_number,
        "tax_amount": tax_amount
    }
    with open("inventory.json", "w") as json_file:
        json.dump(saved_data, json_file, indent=4)
    with open("inventory.txt", "a") as f:
        f.write("\n=== Inventory & Delivery Management System Report ===\n\n")
        f.write("--- Transaction History ---\n")
        for tx in transactions:
            f.write(f"Product Name: {tx['product_name']}, Number of items: {tx['number_of_items']}, Order Number: {tx['order_number']}\n")
        f.write("\n=== Final Report ===\n")
        f.write(f"Exiting... Total Deliveries Processed {total}\n")
        f.write(f"Number of Failed/Rejected Entries: {error_count}\n")
        f.write(f"Total Tax Amount: {tax_amount:.2f}\n")
        f.write(f"Final Total Amount: {current_total + tax_amount:.2f}\n")
        f.write("="*50 + "\n")
    return True

def main():
    with open("inventory.txt", "w") as f:
        f.write("=== Inventory & Delivery Management System Log ===\n")

    saved_state = load_inventory()
    total = saved_state["total"]
    error_count = saved_state["error_count"]
    current_total = saved_state["current_total"]
    transactions = saved_state["transactions"]
    order_number = saved_state["order_number"]
    tax_amount = current_total * 0.10
    
    with open("inventory.txt", "a") as f:
        f.write("\n=== Session Started ===\n")

    print("=== Inventory & Delivery Management System ===")
    print(f"Loaded previous state: {len(transactions)} transactions found. Total items so far: {total}")
    print("Type 'q' at any prompt to quit and view the final report.\n")
    
    while True:
        product_name = input("Enter product name: ")
        if product_name.lower() == "q":
            save_inventory(total, error_count, tax_amount, current_total, transactions, order_number)
            break
            
        user_input = input("Enter inventory count: ")
        
        result = get_valid_input(product_name, user_input, total, error_count, tax_amount, current_total, transactions, order_number) 
        
        if result is True:
            break
            
        total, error_count, success, inventory, transactions, order_number = result
        
        if success and user_input.lower() != "q" and inventory > 0: 
            current_total = process_delivery(current_total, inventory) 
            tax_amount = calculate_tax(current_total)
      
      

if __name__ == "__main__":
    main()