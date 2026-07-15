# Product Model
class Product:
    def __init__(self, product_id=None, sku="", product_name="", category_id=None, supplier_id=None, cost_price=0.00, sale_price=0.00, reorder_level=10, created_at=None):
        self.product_id = product_id
        self.sku = sku
        self.product_name = product_name
        self.category_id = category_id
        self.supplier_id = supplier_id
        self.cost_price = float(cost_price)
        self.sale_price = float(sale_price)
        self.reorder_level = int(reorder_level)
        self.created_at = created_at

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            product_id=row.get("product_id"),
            sku=row.get("sku"),
            product_name=row.get("product_name"),
            category_id=row.get("category_id"),
            supplier_id=row.get("supplier_id"),
            cost_price=row.get("cost_price", 0.00),
            sale_price=row.get("sale_price", 0.00),
            reorder_level=row.get("reorder_level", 10),
            created_at=row.get("created_at")
        )

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "sku": self.sku,
            "product_name": self.product_name,
            "category_id": self.category_id,
            "supplier_id": self.supplier_id,
            "cost_price": self.cost_price,
            "sale_price": self.sale_price,
            "reorder_level": self.reorder_level,
            "created_at": self.created_at
        }
