from inventory_system import (
    Supplier,
    Product,
    PhysicalProduct,
    DigitalProduct,
    Inventory,
    Order,
    show_product_details,
)

# 1. Test Association (Supplier & Product)
print("--- 1. Testing Association ---")
sup = Supplier("S100", "Acme Hardware", "contact@acme.com")
laptop = PhysicalProduct("P101", "Laptop", 1200.00, 10, 2.1, sup)
ebook = DigitalProduct("P102", "Python Guide", 30.00, 50, 15.5, sup)

del sup  # Delete local reference
laptop.display_information()
ebook.display_information()
print("Supplier accessed after deleting variable:", laptop.supplier.name)

# 2. Test Aggregation (Inventory & Product)
print("\n--- 2. Testing Aggregation ---")
inv_a = Inventory()
inv_b = Inventory()
inv_a.add_product(laptop)

removed = inv_a.remove_product("P101")
assert removed is laptop
inv_b.add_product(removed)
print("Laptop moved from Inventory A to Inventory B without destruction.")

# 3. Test Composition (Order & OrderLine)
print("\n--- 3. Testing Composition ---")
order1 = Order("ORD01")
order1.add_order_line(laptop, 1)
order1.add_order_line(ebook, 2)
order1.display_order()

order2 = Order("ORD02")
order2.add_order_line(laptop, 2)
order2.display_order()

assert order1.order_lines[0] is not order2.order_lines[0]
assert order1.order_lines[0].product is order2.order_lines[0].product
print("Verified distinct OrderLine objects referencing the same Product object.")

# 4. Test LSP & Polymorphism
print("\n--- 4. Testing LSP & Polymorphism ---")
inv_b.add_product(ebook)
for item in inv_b.products:
    show_product_details(item)