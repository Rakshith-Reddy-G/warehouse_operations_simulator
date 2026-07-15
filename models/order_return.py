# Return Model
# Named OrderReturn to avoid python 'return' keyword clash
class OrderReturn:
    def __init__(self, return_id=None, order_id=None, product_id=None, quantity=0, return_reason="", return_date=None, refund_amount=0.00, status="Pending"):
        self.return_id = return_id
        self.order_id = order_id
        self.product_id = product_id
        self.quantity = int(quantity)
        self.return_reason = return_reason
        self.return_date = return_date
        self.refund_amount = float(refund_amount)
        self.status = status

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            return_id=row.get("return_id"),
            order_id=row.get("order_id"),
            product_id=row.get("product_id"),
            quantity=row.get("quantity", 0),
            return_reason=row.get("return_reason"),
            return_date=row.get("return_date"),
            refund_amount=row.get("refund_amount", 0.00),
            status=row.get("status", "Pending")
        )

    def to_dict(self):
        return {
            "return_id": self.return_id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "return_reason": self.return_reason,
            "return_date": self.return_date,
            "refund_amount": self.refund_amount,
            "status": self.status
        }
