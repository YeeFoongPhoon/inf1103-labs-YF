import csv 
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
        if price <= 0:
            raise ValueError("Product price must be greater than zero.")
        if stock < 0:
            raise ValueError("Product stock quantity cannot be negative.")

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
        if self.__stock + quantity < 0:
            raise ValueError("Product stock quantity cannot be negative.")
        self.__stock += quantity
        self.transactions.append(quantity)
        
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
    
class ProductFactory:
    @staticmethod
    def create(
        product_type: str,
        product_id: str,
        name: str,
        price: float,
        stock_quantity: int,
        supplier: Supplier,
        spec_value: float = 0.0,
        transactions: list[int] | None = None
    ) -> Product:
        normalized_type = product_type.strip().lower()
        if normalized_type in ("physical", "p"):
            return PhysicalProduct(
                product_id, name, price, stock_quantity, spec_value, supplier, transactions
            )
        elif normalized_type in ("digital", "d"):
            return DigitalProduct(
                product_id, name, price, stock_quantity, spec_value, supplier, transactions
            )
        else:
            raise ValueError(f"Unknown product type: {product_type}")
        
class DiscountStrategy(ABC):
    @abstractmethod
    def apply(self, total: float) -> float:
        pass


class NoDiscount(DiscountStrategy):
    def apply(self, total: float) -> float:
        return total


class PercentageDiscount(DiscountStrategy):
    def __init__(self, percentage: float) -> None:
        if percentage < 0 or percentage > 100:
            raise ValueError("Discount percentage must be between 0 and 100.")
        self.percentage: float = percentage

    def apply(self, total: float) -> float:
        return total * (1 - self.percentage / 100)


class BulkDiscount(DiscountStrategy):
    def __init__(self, threshold: float, amount: float) -> None:
        if threshold < 0 or amount < 0:
            raise ValueError("Threshold and discount amount cannot be negative.")
        self.threshold: float = threshold
        self.amount: float = amount

    def apply(self, total: float) -> float:
        if total >= self.threshold:
            return max(0.0, total - self.amount)
        return total


class StudentDiscount(DiscountStrategy):
    def __init__(self, percentage: float = 5.0) -> None:
        self.percentage: float = percentage

    def apply(self, total: float) -> float:
        return total * (1 - self.percentage / 100)

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
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")
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
    def __init__(self, order_id: str, discount: DiscountStrategy | None = None) -> None:
        self.order_id: str = order_id
        self.order_lines: list[OrderLine] = []
        self.discount: DiscountStrategy = discount if discount is not None else NoDiscount()

    def set_discount(self, discount: DiscountStrategy) -> None:
        self.discount = discount

    def add_order_line(self, product: Product, quantity: int) -> None:
        order_line = OrderLine(product, quantity)
        if product.stock < quantity:
            raise ValueError(f"Insufficient stock for {product.name}.")
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
        total = sum(line.calculate_subtotal() for line in self.order_lines)
        return self.discount.apply(total)

    def display_order(self) -> None:
        print(f"\n=== Order ID: {self.order_id} ===")
        if not self.order_lines:
            print("  (No items in this order)")
        else:
            for line in self.order_lines:
                line.display_line()
        raw_total = sum(line.calculate_subtotal() for line in self.order_lines)
        final_total = self.calculate_total()
        print(f"Subtotal           : ${raw_total:.2f}")
        print(f"Total After Discount: ${final_total:.2f}\n")

def show_product_details(product: Product) -> None:
    product.display_information()
    print(f"   Fulfilment: {product.get_fulfilment_info()}")

def get_positive_float(prompt: str) -> float:
    while True:
        try:
            value = float(input(prompt))
            if value <= 0:
                print("Please enter a number greater than zero.")
                continue
            return value
        except ValueError:
            print("Please enter a valid number, e.g. 12.50")


def get_non_negative_int(prompt: str) -> int:
    while True:
        try:
            value = int(input(prompt))
            if value < 0:
                print("Please enter a whole number that is zero or greater.")
                continue
            return value
        except ValueError:
            print("Please enter a valid whole number, e.g. 10")


def get_non_negative_float(prompt: str) -> float:
    while True:
        try:
            value = float(input(prompt))
            if value < 0:
                print("Please enter a number that is zero or greater.")
                continue
            return value
        except ValueError:
            print("Please enter a valid number, e.g. 2.5")


def load_products(path: str, inventory: Inventory, supplier: Supplier) -> None:
    try:
        file = open(path, newline="")
    except FileNotFoundError:
        print(f"Products file not found: {path}")
    else:
        with file:
            reader = csv.reader(file)
            next(reader, None)  # Skip header row
            loaded = 0
            for row_num, row in enumerate(reader, start=2):
                if not row or len(row) < 5:
                    continue
                try:
                    p_type = row[0].strip()
                    pid = row[1].strip()
                    name = row[2].strip()
                    price = float(row[3].strip())
                    stock_qty = int(row[4].strip())
                    product = ProductFactory.create(p_type, pid, name, price, stock_qty, supplier)
                    inventory.add_product(product)
                    loaded += 1
                except ValueError as e:
                    print(f"Skipping invalid row {row_num} ({row}): {e}")
            print(f"{loaded} products loaded.")
    finally:
        print("Load attempt finished.")
           
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
                    if product_type == "digital" or item.get("download_size") is not None:
                        spec = item.get("download_size", 0.0)
                        p_type = "digital"
                    else:
                        spec = item.get("weight", 0.0)
                        p_type = "physical"

                    product = ProductFactory.create(
                        p_type, pid, name, price, stock, supplier, spec, transactions
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
    except OSError as e:
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
        print("6. Create Customer Order (with Discount Strategy)")
        print("7. Import Products from CSV")
        print("8. Save Inventory")
        print("9. Exit")

        choice = input("\nEnter your choice (1-9): ").strip()

        if choice == '1':
            inventory.display_all()
        elif choice == '2':
            name = input("Enter the new product name: ").strip()
            stock = get_non_negative_int("Enter stock count: ")
            price = get_positive_float("Enter unit price: $")

            sup_id = input("Enter Supplier ID (e.g., S001): ").strip() or "S001"
            if sup_id not in suppliers:
                sup_name = input("New Supplier Name: ").strip()
                sup_email = input("New Supplier Email: ").strip()
                suppliers[sup_id] = Supplier(sup_id, sup_name, sup_email)
            supplier = suppliers[sup_id]

            while True:
                p_type = input("Is this a physical or digital product? (physical/digital): ").strip().lower()
                if p_type in ("physical", "digital", "p", "d"):
                    break
                print("Please enter 'physical' or 'digital'.")

            product_id = f"P{len(inventory.products)+1:03d}"
            if p_type in ("digital", "d"):
                spec = get_non_negative_float("Enter download size (MB): ")
            else:
                spec = get_non_negative_float("Enter weight (kg): ")

            new_product = ProductFactory.create(
                p_type, product_id, name, price, stock, supplier, spec
            )

            base_cost = stock * price
            tax_amount = base_cost * 0.10
            total_purchase_cost = base_cost + tax_amount

            inventory.total_tax += tax_amount
            inventory.total_cost += total_purchase_cost

            inventory.add_product(new_product)
            print(f"-> '{name}' added successfully! (Cost: ${base_cost:.2f} + 10% Tax: ${tax_amount:.2f} = Total: ${total_purchase_cost:.2f})\n")
        elif choice == '3':
            name = input("Enter the product name to update: ").strip()
            product = inventory.search_product(name)

            if product:
                try:
                    adj = int(input(f"Enter stock adjustment for {product.name} (e.g., 5 to add, -3 to remove): "))
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
                except ValueError as e:
                    print(f"-> Invalid input or adjustment: {e}\n")
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

            print("\nSelect Discount Strategy:")
            print("1. No Discount")
            print("2. 10% Percentage Discount")
            print("3. Bulk Discount ($20 off orders >= $200)")
            print("4. 5% Student Discount")
            disc_choice = input("Enter choice (1-4): ").strip()
            if disc_choice == '2':
                order.set_discount(PercentageDiscount(10))
            elif disc_choice == '3':
                order.set_discount(BulkDiscount(200, 20))
            elif disc_choice == '4':
                order.set_discount(StudentDiscount(5))

            orders.append(order)
            order.display_order()
        elif choice == '7':
            csv_path = input("Enter CSV filename (default: products.csv): ").strip() or "products.csv"
            load_products(csv_path, inventory, suppliers["S001"])
        elif choice == '8':
            save_inventory(inventory)
        elif choice == '9':
            save_prompt = input("Do you want to save before exiting? (y/n): ").strip().lower()
            if save_prompt == 'y':
                save_inventory(inventory)
            print("Exiting program. Goodbye!")
            break
        else:
            print("-> Invalid choice. Please enter a number between 1 and 9.\n")


if __name__ == "__main__":
    main()