import json
import os
from abc import ABC, abstractmethod 

class Product(ABC):
    def __init__(self, product_id, name, price, stock, transactions=None):
        self.product_id = product_id
        self.name = name
        self.price = price
        self.__stock = stock
        self.transactions = transactions if transactions is not None else [stock]

    @property
    def stock(self):
        return self.__stock

    def update_stock(self, quantity):
        self.__stock += quantity
        self.transactions.append(quantity)

    @abstractmethod
    def get_fulfilment_info(self):
        pass

    def display_information(self):
        history_formatted = ", ".join(
            f"+{t}" if t > 0 else str(t) for t in self.transactions
        )
        print(
            f"ID: {self.product_id} | {self.name} | Unit Price: ${self.price:.2f} | "
            f"Stock: {self.stock} | History: [{history_formatted}]",
            end=""
        )

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "name": self.name,
            "price": self.price,
            "stock": self.__stock,
            "transactions": self.transactions,
            "weight": getattr(self, 'weight', None),
            "download_size": getattr(self, 'download_size', None)
        }


class PhysicalProduct(Product):
    def __init__(self, product_id, name, price, stock, weight, transactions=None):
        super().__init__(product_id, name, price, stock, transactions)
        self.weight = weight

    def display_information(self):
        super().display_information()
        print(f" | Type: Physical | Weight: {self.weight} kg")
    def to_dict(self):
        data = super().to_dict()
        data["type"] = "physical"
        data["weight"] = self.weight
        return data
    def get_fulfilment_info(self):
        return f"Physical shipping via courier (Weight: {self.weight} kg)"

class DigitalProduct(Product):
    def __init__(self, product_id, name, price, stock, download_size, transactions=None):
        super().__init__(product_id, name, price, stock, transactions)
        self.download_size = download_size

    def display_information(self):
        super().display_information()
        print(f" | Type: Digital | File Size: {self.download_size} MB")

    def to_dict(self):
        data = super().to_dict()
        data["type"] = "digital"
        data["download_size"] = self.download_size
        return data
    def get_fulfilment_info(self):
        return f"Digital download available (File Size: {self.download_size} MB)"

class Inventory:
    def __init__(self):
        self.products = []
        self.total_tax = 0.0
        self.total_cost = 0.0

    def add_product(self, product):
        self.products.append(product)

    def search_product(self, name):
        for product in self.products:
            if product.name.lower() == name.lower():
                return product
        return None

    def display_all(self):
        if not self.products:
            print("-> The inventory is currently empty.\n")
            return
            
        print("\n--- Current Inventory ---")
        for i, product in enumerate(self.products, 1):
            print(f"{i}. ", end="")
            product.display_information()
        
        print("-" * 40)
        print(f"Total Tax Paid (All Purchases) : ${self.total_tax:,.2f}")
        print(f"Total Inventory Cost (Incl Tax) : ${self.total_cost:,.2f}")
        print("-" * 40 + "\n")

def load_inventory(filename="inventory.json"):
    inventory = Inventory()
    if os.path.exists(filename):
        try:
            with open(filename, "r") as file:
                data = json.load(file)
                
                if isinstance(data, list):
                    raw_products = data
                else:
                    raw_products = data.get("products", [])
                    inventory.total_tax = data.get("total_tax", 0.0)
                    inventory.total_cost = data.get("total_cost", 0.0)

                for i, item in enumerate(raw_products):
                    pid = item.get("product_id", f"P{i+1:03d}")
                    name = item.get("name", "Unknown")
                    stock = item.get("stock", 0)
                    transactions = item.get("transactions", [item.get("stock", 0)])
                    price = item.get("price", 1.00)

                    product_type = item.get("type")
                    
                    if product_type == "digital" or "download_size" in item:
                        download_size = item.get("download_size", 0.0)
                        product = DigitalProduct(pid, name, price, stock, download_size, transactions)
                    else:
                        # Fallback for older files or explicitly physical products
                        weight = item.get("weight", 0.0)  # Default weight if missing in old files
                        product = PhysicalProduct(pid, name, price, stock, weight, transactions)
                        
                    inventory.add_product(product)

            print(f"Successfully loaded data from {filename}.")
            return inventory
        except json.JSONDecodeError:
            print(f"Error: {filename} is not a valid JSON file. Starting with empty inventory.")
    return inventory

def save_inventory(inventory, filename="inventory.json"):
    try:
        data = {
            "products": [p.to_dict() for p in inventory.products],
            "total_tax": inventory.total_tax,
            "total_cost": inventory.total_cost
        }
        with open(filename, "w") as file:
            json.dump(data, file, indent=4)
        print(f"-> Inventory successfully saved to {filename}!\n")
    except Exception as e:
        print(f"-> Error saving inventory: {e}\n")

def main():
    print("=== Inventory Management System ===")
    inventory = load_inventory()
    
    while True:
        print("\nMenu Options:")
        print("1. Display All Products & Financials")
        print("2. Add a Product and its type (Purchase)")
        print("3. Update Stock (Record Transaction)")
        print("4. Search for a Product")
        print("5. Save Inventory")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == '1':
            inventory.display_all()
        elif choice == '2':
            name = input("Enter the new product name: ").strip()
            try:
                stock = int(input("Enter stock count: "))
                price = float(input("Enter unit price: $"))
                if stock < 0 or price < 0:
                    raise ValueError
                
                # Ask for product type
                p_type = input("Is this a physical or digital product? (p/d): ").strip().lower()
                
                product_id = f"P{len(inventory.products)+1:03d}"
                
                if p_type == 'd':
                    download_size = float(input("Enter download size (MB): "))
                    new_product = DigitalProduct(product_id, name, price, stock, download_size)
                else:
                    weight = float(input("Enter weight (kg): "))
                    new_product = PhysicalProduct(product_id, name, price, stock, weight)
                
                base_cost = stock * price
                tax_amount = base_cost * 0.10
                total_purchase_cost = base_cost + tax_amount

                inventory.total_tax += tax_amount
                inventory.total_cost += total_purchase_cost
                
                inventory.add_product(new_product)
                
                print(f"-> '{name}' added successfully! (Cost: ${base_cost:.2f} + 10% Tax: ${tax_amount:.2f} = Total: ${total_purchase_cost:.2f})\n")
            except ValueError:
                print("-> Invalid input! Please enter proper numbers for stock, price, and specs.\n")
        elif choice == '3':
            name = input("Enter the product name to update: ").strip()
            product = inventory.search_product(name)
            
            if product:
                try:
                    adj = int(input(f"Enter stock adjustment for {product.name} (e.g., 5 to add, -3 to remove): "))
                    
                    if product.stock + adj < 0:
                        print("-> Error: Transaction would reduce stock below 0. Action canceled.\n")
                        continue
                        
                    product.update_stock(adj)
                    
                    if adj > 0:
                        base_cost = adj * product.price
                        tax_amount = base_cost * 0.10
                        total_purchase_cost = base_cost + tax_amount
                        
                        inventory.total_tax += tax_amount
                        inventory.total_cost += total_purchase_cost
                        
                        print(f"-> Purchase logged: {adj} units at ${product.price:.2f} each.")
                        print(f"   Tax Added: ${tax_amount:.2f} | Total Cost to Inventory: ${total_purchase_cost:.2f}")
                    
                    change_str = f"+{adj}" if adj >= 0 else f"{adj}"
                    print(f"-> Transaction of {change_str} applied. New stock for '{product.name}' is {product.stock}.\n")
                except ValueError:
                    print("-> Invalid input! Adjustment must be a valid integer.\n")
            else:
                print(f"-> Product '{name}' not found in inventory.\n")
        elif choice == '4':
            name = input("Enter the product name to search for: ").strip()
            product = inventory.search_product(name)
            if product:
                print("-> Found: ", end="")
                product.display_information()
                print()
            else:
                print(f"-> Product '{name}' not found in inventory.\n")
        elif choice == '5':
            save_inventory(inventory)
        elif choice == '6':
            save_prompt = input("Do you want to save before exiting? (y/n): ").strip().lower()
            if save_prompt == 'y':
                save_inventory(inventory)
            print("Exiting program. Goodbye!")
            break
        else:
            print("-> Invalid choice. Please enter a number between 1 and 6.\n")

if __name__ == "__main__":
    main()