import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Inventory_manager_updated import (
    Supplier,
    PhysicalProduct,
    DigitalProduct,
    ProductFactory,
    NoDiscount,
    PercentageDiscount,
    BulkDiscount,
    StudentDiscount,
    Inventory,
    OrderLine,
    Order,
    load_products,
)


class TestLab9DesignPatternsAndValidation(unittest.TestCase):
    def setUp(self) -> None:
        self.supplier = Supplier("S001", "Global Tech", "sales@globaltech.com")
        self.laptop = PhysicalProduct("P001", "Laptop", 250.00, 10, 2.0, self.supplier)
        self.ebook = DigitalProduct("D001", "Python Guide", 50.00, 20, 15.0, self.supplier)

    # --- Strategy Pattern Tests ---
    def test_order_default_no_discount(self) -> None:
        order = Order("ORD01")
        order.add_order_line(self.laptop, 1)
        self.assertAlmostEqual(order.calculate_total(), 250.00)

    def test_order_bulk_and_percentage_discount_switch(self) -> None:
        order = Order("ORD02", BulkDiscount(200, 20))
        order.add_order_line(self.laptop, 1)  # Subtotal = 250
        self.assertAlmostEqual(order.calculate_total(), 230.00)

        order.set_discount(PercentageDiscount(10))
        self.assertAlmostEqual(order.calculate_total(), 225.00)

    def test_student_discount_strategy(self) -> None:
        order = Order("ORD03", StudentDiscount(5))
        order.add_order_line(self.ebook, 2)  # Subtotal = 100
        self.assertAlmostEqual(order.calculate_total(), 95.00)

    # --- Factory Pattern Tests ---
    def test_product_factory_creates_subclasses(self) -> None:
        p = ProductFactory.create("physical", "P010", "Desk", 120.0, 5, self.supplier, 10.5)
        d = ProductFactory.create("digital", "D010", "IDE", 80.0, 50, self.supplier, 300.0)
        self.assertIsInstance(p, PhysicalProduct)
        self.assertIsInstance(d, DigitalProduct)

    def test_product_factory_rejects_unknown_type(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            ProductFactory.create("service", "S001", "Consulting", 100.0, 1, self.supplier)
        self.assertIn("Unknown product type: service", str(ctx.exception))

    # --- Validation Tests ---
    def test_invalid_product_price_and_stock_rejected(self) -> None:
        with self.assertRaises(ValueError):
            PhysicalProduct("P099", "Bad Price", 0.0, 5, 1.0, self.supplier)
        with self.assertRaises(ValueError):
            DigitalProduct("D099", "Neg Stock", 10.0, -1, 5.0, self.supplier)

    def test_invalid_order_line_quantity_rejected(self) -> None:
        with self.assertRaises(ValueError):
            OrderLine(self.laptop, 0)
        with self.assertRaises(ValueError):
            OrderLine(self.laptop, -3)

    # --- CSV Loader & Exception Handling Tests ---
    def test_load_products_skips_bad_rows_and_handles_missing_file(self) -> None:
        inv = Inventory()
        # Missing file should not raise FileNotFoundError
        load_products("non_existent_file.csv", inv, self.supplier)
        self.assertEqual(len(inv.products), 0)

        # CSV with 3 valid rows and 2 invalid rows
        csv_content = (
            "product_type,product_id,name,price,stock_quantity\n"
            "physical,P001,Desk Lamp,25.00,10\n"
            "digital,D001,Photo Editor,49.90,100\n"
            "service,S001,Installation,30.00,5\n"
            "physical,P002,Office Chair,abc,3\n"
            "physical,P003,Monitor Stand,39.50,7\n"
        )
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv", newline="") as tmp:
            tmp.write(csv_content)
            tmp_path = tmp.name

        try:
            load_products(tmp_path, inv, self.supplier)
            self.assertEqual(len(inv.products), 3)
            self.assertEqual([p.product_id for p in inv.products], ["P001", "D001", "P003"])
        finally:
            os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()