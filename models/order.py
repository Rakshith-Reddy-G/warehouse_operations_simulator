# Order and OrderItem Models
class OrderItem:
    def __init__(self, order_item_id=None, order_id=None, product_id=None, quantity=0, unit_price=0.00, item_status="Pending"):
        self.order_item_id = order_item_id
        self.order_id = order_id
        self.product_id = product_id
        self.quantity = int(quantity)
        self.unit_price = float(unit_price)
        self.item_status = item_status

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            order_item_id=row.get("order_item_id"),
            order_id=row.get("order_id"),
            product_id=row.get("product_id"),
            quantity=row.get("quantity", 0),
            unit_price=row.get("unit_price", 0.00),
            item_status=row.get("item_status", "Pending")
        )

    def to_dict(self):
        return {
            "order_item_id": self.order_item_id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "item_status": self.item_status
        }


class Order:
    def __init__(self, order_id=None, customer_id=None, status="Pending", order_date=None, total_amount=0.00, picking_employee_id=None, packing_employee_id=None, updated_at=None, items=None):
        self.order_id = order_id
        self.customer_id = customer_id
        self.status = status
        self.order_date = order_date
        self.total_amount = float(total_amount)
        self.picking_employee_id = picking_employee_id
        self.packing_employee_id = packing_employee_id
        self.updated_at = updated_at
        self.items = items if items is not None else []

    @classmethod
    def from_row(cls, row, items=None):
        if not row:
            return None
        return cls(
            order_id=row.get("order_id"),
            customer_id=row.get("customer_id"),
            status=row.get("status", "Pending"),
            order_date=row.get("order_date"),
            total_amount=row.get("total_amount", 0.00),
            picking_employee_id=row.get("picking_employee_id"),
            packing_employee_id=row.get("packing_employee_id"),
            updated_at=row.get("updated_at"),
            items=items
        )

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "status": self.status,
            "order_date": self.order_date,
            "total_amount": self.total_amount,
            "picking_employee_id": self.picking_employee_id,
            "packing_employee_id": self.packing_employee_id,
            "updated_at": self.updated_at,
            "items": [item.to_dict() for item in self.items]
        }
