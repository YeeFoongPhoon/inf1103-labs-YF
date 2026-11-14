import json
import os
from abc import ABC, abstractmethod


class Supplier:
    def __init__(self, supplier_id: str, name: str, contact_email: str) -> None:
        self.supplier_id: str = supplier_id
        self.name: str = name
        self.contact_email: str = contact_email

    def display_information(self) -> None:
        print(f"Supplier ID: {self.supplier_id} | Name: {self.name} | Email: {self.contact_email}")

    def to_dict(self) -> dict[str, str]:
        return {
            "supplier_id": self.supplier_id,
            "name": self.name,
            "contact_email": self.contact_email
        }


class Product(ABC):
    def __init__(
        self,
        product_id: str,
        name: str,
        price: float,
        stock: int,
        supplier: Supplier,
        transactions: list[int] | None = None
    ) -> None:
        self.product_id: str = product_id
        self.name: str = name
        self.price: float = price
        self.__stock: int = stock
        self.supplier: Supplier = supplier
        self.transactions: list[int] = transactions if transactions is not None else [stock]

    @property
    def stock(self) -> int:
        return self.__stock

    def update_stock(self, quantity: int) -> None:
        self.__stock += quantity
        self.transactions.append(quantity)

    @abstractmethod
    def get_fulfilment_info(self) -> str:
        pass

    def display_information(self) -> None:
        history_formatted = ", ".join(
            f"+{t}" if t > 0 else str(t) for t in self.transactions
        )
        print(
            f"ID: {self.product_id} | {self.name} | Unit Price: ${self.price:.2f} | "
            f"Stock: {self.stock} | Supplier: {self.supplier.name} | "
            f"History: [{history_formatted}]",
            end=""
        )

    def to_dict(self) -> dict:
        return {
            "product_id": self.product_id,
            "name": self.name,
            "price": self.price,
            "stock": self.__stock,
            "supplier": self.supplier.to_dict(),
            "transactions": self.transactions,
            "weight": getattr(self, 'weight', None),
            "download_size": getattr(self, 'download_size', None)
        }


class PhysicalProduct(Product):
    def __init__(
        self,
        product_id: str,
        name: str,
        price: float,
        stock: int,
        weight: float,
        supplier: Supplier,
        transactions: list[int] | None = None
    ) -> None:
        super().__init__(product_id, name, price, stock, supplier, transactions)
        self.weight: float = weight

    def display_information(self) -> None:
        super().display_information()
        print(f" | Type: Physical | Weight: {self.weight} kg")

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["type"] = "physical"
        data["weight"] = self.weight
        return data

    def get_fulfilment_info(self) -> str:
        return f"Physical shipping via courier (Weight: {self.weight} kg)"


class DigitalProduct(Product):
    def __init__(
        self,
        product_id: str,
        name: str,
        price: float,
        stock: int,
        download_size: float,
        supplier: Supplier,
        transactions: list[int] | None = None
    ) -> None:
        super().__init__(product_id, name, price, stock, supplier, transactions)
        self.download_size: float = download_size

    def display_information(self) -> None:
        super().display_information()
        print(f" | Type: Digital | File Size: {self.download_size} MB")

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["type"] = "digital"
        data["download_size"] = self.download_size
        return data

    def get_fulfilment_info(self) -> str:
        return f"Digital download available (File Size: {self.download_size} MB)"


class Inventory:
    def __init__(self) -> None:
        self.products: list[Product] = []
        self.total_tax: float = 0.0
        self.total_cost: float = 0.0

    def add_product(self, product: Product) -> None:
        self.products.append(product)

    def remove_product(self, product_id: str) -> Product | None:
        product = self.find_product(product_id)
        if product:
            self.products.remove(product)
            return product
        return None

    def find_product(self, product_id: str) -> Product | None:
        for product in self.products:
            if product.product_id.lower() == product_id.lower():
                return product
        return None

    def search_product(self, name: str) -> Product | None:
        for product in self.products:
            if product.name.lower() == name.lower():
                return product
        return None

    def display_all(self) -> None:
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


class OrderLine:
    def __init__(self, product: Product, quantity: int) -> None:
        self.product: Product = product
        self.quantity: int = quantity

    def calculate_subtotal(self) -> float:
        return self.product.price * self.quantity

    def display_line(self) -> None:
        print(
            f"  - {self.product.name} (x{self.quantity}) @ ${self.product.price:.2f} "
            f"= ${self.calculate_subtotal():.2f}"
        )


class Order:
    def __init__(self, order_id: str) -> None:
        self.order_id: str = order_id
        self.order_lines: list[OrderLine] = []

    def add_order_line(self, product: Product, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Order quantity must be greater than zero.")
        if product.stock < quantity:
            raise ValueError(f"Insufficient stock for {product.name}.")
        order_line = OrderLine(product, quantity)
        self.order_lines.append(order_line)
        product.update_stock(-quantity)

    def remove_order_line(self, product_id: str) -> bool:
        for line in self.order_lines:
            if line.product.product_id.lower() == product_id.lower():
                line.product.update_stock(line.quantity)
                self.order_lines.remove(line)
                return True
        return False

    def calculate_total(self) -> float:
        return sum(line.calculate_subtotal() for line in self.order_lines)

    def display_order(self) -> None:
        print(f"\n=== Order ID: {self.order_id} ===")
        if not self.order_lines:
            print("  (No items in this order)")
        else:
            for line in self.order_lines:
                line.display_line()
        print(f"Total Order Amount: ${self.calculate_total():.2f}\n")

def show_product_details(product: Product) -> None:
    product.display_information()
    print(f"   Fulfilment: {product.get_fulfilment_info()}")
    
def load_inventory(filename: str = "inventory.json") -> Inventory:
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

                    sup_data = item.get("supplier", {})
                    supplier = Supplier(
                        sup_data.get("supplier_id", "S000"),
                        sup_data.get("name", "Default Supplier"),
                        sup_data.get("contact_email", "support@supplier.com")
                    )

                    product_type = item.get("type")
                    if product_type == "digital" or "download_size" in item:
                        download_size = item.get("download_size", 0.0)
                        product: Product = DigitalProduct(
                            pid, name, price, stock, download_size, supplier, transactions
                        )
                    else:
                        weight = item.get("weight", 0.0)
                        product = PhysicalProduct(
                            pid, name, price, stock, weight, supplier, transactions
                        )

                    inventory.add_product(product)

            print(f"Successfully loaded data from {filename}.")
            return inventory
        except json.JSONDecodeError:
            print(f"Error: {filename} is not a valid JSON file. Starting with empty inventory.")
    return inventory


def save_inventory(inventory: Inventory, filename: str = "inventory.json") -> None:
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


def main() -> None:
    print("=== Inventory Management System ===")
    inventory = load_inventory()
    orders: list[Order] = []
    suppliers: dict[str, Supplier] = {
        "S001": Supplier("S001", "Global Tech Supplies", "sales@globaltech.com")
    }

    while True:
        print("\nMenu Options:")
        print("1. Display All Products & Financials")
        print("2. Add a Product and its type (Purchase)")
        print("3. Update Stock (Record Transaction)")
        print("4. Search & Inspect Product (Polymorphic Details)")
        print("5. Remove Product from Inventory")
        print("6. Create Customer Order")
        print("7. Save Inventory")
        print("8. Exit")

        choice = input("\nEnter your choice (1-8): ").strip()

        if choice == '1':
            inventory.display_all()
        elif choice == '2':
            name = input("Enter the new product name: ").strip()
            try:
                stock = int(input("Enter stock count: "))
                price = float(input("Enter unit price: $"))
                if stock < 0 or price < 0:
                    raise ValueError

                sup_id = input("Enter Supplier ID (e.g., S001): ").strip() or "S001"
                if sup_id not in suppliers:
                    sup_name = input("New Supplier Name: ").strip()
                    sup_email = input("New Supplier Email: ").strip()
                    suppliers[sup_id] = Supplier(sup_id, sup_name, sup_email)
                supplier = suppliers[sup_id]

                p_type = input("Is this a physical or digital product? (p/d): ").strip().lower()
                product_id = f"P{len(inventory.products)+1:03d}"

                if p_type == 'd':
                    download_size = float(input("Enter download size (MB): "))
                    new_product: Product = DigitalProduct(
                        product_id, name, price, stock, download_size, supplier
                    )
                else:
                    weight = float(input("Enter weight (kg): "))
                    new_product = PhysicalProduct(
                        product_id, name, price, stock, weight, supplier
                    )

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
                print("-> Found: ")
                show_product_details(product)
                print()
            else:
                print(f"-> Product '{name}' not found in inventory.\n")
        elif choice == '5':
            pid = input("Enter Product ID to remove (e.g., P001): ").strip()
            removed = inventory.remove_product(pid)
            if removed:
                print(f"-> Removed '{removed.name}' from inventory (object still exists independently).\n")
            else:
                print(f"-> Product ID '{pid}' not found.\n")
        elif choice == '6':
            order_id = f"ORD{len(orders)+1:03d}"
            order = Order(order_id)
            while True:
                pid = input("Enter Product ID to add to order (or 'done'): ").strip()
                if pid.lower() == 'done':
                    break
                product = inventory.find_product(pid)
                if not product:
                    print("-> Product ID not found.")
                    continue
                try:
                    qty = int(input(f"Enter quantity for {product.name}: "))
                    order.add_order_line(product, qty)
                    print(f"-> Added {qty}x {product.name} to order.")
                except ValueError as e:
                    print(f"-> Error: {e}")
            orders.append(order)
            order.display_order()
        elif choice == '7':
            save_inventory(inventory)
        elif choice == '8':
            save_prompt = input("Do you want to save before exiting? (y/n): ").strip().lower()
            if save_prompt == 'y':
                save_inventory(inventory)
            print("Exiting program. Goodbye!")
            break
        else:
            print("-> Invalid choice. Please enter a number between 1 and 8.\n")


if __name__ == "__main__":
    main()