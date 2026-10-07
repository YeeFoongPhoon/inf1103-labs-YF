
import json
import os

def load_inventory(filename="inventory.json"):
  if os.path.exists(filename):
        try:
            with open(filename, "r") as file:
                data = json.load(file)
                
                # Migration: if the old file is just a list, wrap it in our new dict structure
                if isinstance(data, list):
                    inventory = {
                        "products": data,
                        "total_tax": 0.0,
                        "total_cost": 0.0
                    }
                else:
                    inventory = data
                if "total_tax" not in inventory:
                    inventory["total_tax"] = 0.0
                if "total_cost" not in inventory:
                    inventory["total_cost"] = 0.0
                if "products" not in inventory:
                    inventory["products"] = []

            for item in inventory.get("products", []):
                    if "transactions" not in item:
                        item["transactions"] = [item["stock"]]
                    if "price" not in item:
                        item["price"] = 1.00
            print(f"Successfully loaded data from {filename}.")
            return inventory
        except json.JSONDecodeError:
         print(f"Error: {filename} is not a valid JSON file. Starting with empty inventory.")
  return {"products": [], "total_tax": 0.0, "total_cost": 0.0}

def save_inventory(inventory, filename="inventory.json"):
    try:
        with open(filename, "w") as file:
            json.dump(inventory, file, indent=4)
        print(f"-> Inventory successfully saved to {filename}!\n")
    except Exception as e:
        print(f"-> Error saving inventory: {e}\n")

def add_product(inventory):
    """Adds a new product (dictionary) to the inventory list."""
    name = input("Enter the new product name: ").strip()
    try:
        stock = int(input("Enter stock count: "))
        price = float(input("Enter unit price: $"))
        if stock < 0 or price < 0:
            raise ValueError
        
        base_cost = stock * price
        tax_amount = base_cost * 0.10
        total_purchase_cost = base_cost + tax_amount

        inventory["total_tax"] += tax_amount
        inventory["total_cost"] += total_purchase_cost
        
        new_product = {
            "name": name,
            "price": price,
            "stock": stock,
            "transactions": [stock]
        }
        inventory["products"].append(new_product)
        print(f"-> '{name}' added successfully! (Cost: ${base_cost:.2f} + 10% Tax: ${tax_amount:.2f} = Total: ${total_purchase_cost:.2f})\n")
    except ValueError:
        print("-> Invalid input! Stock and price must be positive numbers.\n")

def search_product(inventory):
    """Searches for a product by name and displays its details."""
    name = input("Enter the product name to search for: ").strip()
    for product in inventory["products"]:
        if product["name"].lower() == name.lower():
            print(f"-> Found: {product['name']} | Price: ${product['price']:.2f} | Current Stock: {product['stock']}")
            print(f"   Transaction History: {product['transactions']}\n")
            return
    print(f"-> Product '{name}' not found in inventory.\n")

def update_stock(inventory):
    """Updates the stock count of an existing product."""
    name = input("Enter the product name to update: ").strip()
    for product in inventory["products"]:
        if product["name"].lower() == name.lower():
            try:
                adj = int(input(f"Enter stock adjustment for {product['name']} (e.g., 5 to add, -3 to remove): "))
                
                if product["stock"] + adj < 0:
                    print("-> Error: Transaction would reduce stock below 0. Action canceled.\n")
                    return
                
                # Update running total and append the transaction amount to history
                product["stock"] += adj
                product["transactions"].append(adj)
                
                if adj > 0:
                    base_cost = adj * product["price"]
                    tax_amount = base_cost * 0.10
                    total_purchase_cost = base_cost + tax_amount
                    
                    inventory["total_tax"] += tax_amount
                    inventory["total_cost"] += total_purchase_cost
                    
                    print(f"-> Purchase logged: {adj} units at ${product['price']:.2f} each.")
                    print(f"   Tax Added: ${tax_amount:.2f} | Total Cost to Inventory: ${total_purchase_cost:.2f}")
                
                change_str = f"+{adj}" if adj >= 0 else f"{adj}"
                print(f"-> Transaction of {change_str} applied. New stock for '{product['name']}' is {product['stock']}.\n")
                return
            except ValueError:
                print("-> Invalid input! Adjustment must be a valid integer.\n")
                return
    print(f"-> Product '{name}' not found in inventory.\n")

def display_all(inventory):
    products = inventory["products"]
    
    if not products:
        print("-> The inventory is currently empty.\n")
        return
        
    print("\n--- Current Inventory ---")
    for i, product in enumerate(products, 1):
        history_formatted = ", ".join([f"+{t}" if t > 0 else str(t) for t in product['transactions']])
        print(f"{i}. {product['name']} | Unit Price: ${product['price']:.2f} | Stock: {product['stock']} | History: [{history_formatted}]")
    
    print("-" * 40)
    print(f"Total Tax Paid (All Purchases) : ${inventory['total_tax']:,.2f}")
    print(f"Total Inventory Cost (Incl Tax) : ${inventory['total_cost']:,.2f}")
    print("-" * 40 + "\n")



def main():
    print("=== Inventory Management System ===")
    
    # Load existing data or start with an empty dictionary structure
    inventory = load_inventory()
    
    while True:
        print("\nMenu Options:")
        print("1. Display All Products & Financials")
        print("2. Add a Product (Purchase)")
        print("3. Update Stock (Record Transaction)")
        print("4. Search for a Product")
        print("5. Save Inventory")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == '1':
            display_all(inventory)
        elif choice == '2':
            add_product(inventory)
        elif choice == '3':
            update_stock(inventory)
        elif choice == '4':
            search_product(inventory)
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