# Transaction Model (Audit log)
class Transaction:
    def __init__(self, transaction_id=None, transaction_type="", product_id=None, location_id=None, quantity=0, employee_id=None, reference_id="", transaction_date=None, notes=""):
        self.transaction_id = transaction_id
        self.transaction_type = transaction_type
        self.product_id = product_id
        self.location_id = location_id
        self.quantity = int(quantity)
        self.employee_id = employee_id
        self.reference_id = reference_id
        self.transaction_date = transaction_date
        self.notes = notes

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            transaction_id=row.get("transaction_id"),
            transaction_type=row.get("transaction_type"),
            product_id=row.get("product_id"),
            location_id=row.get("location_id"),
            quantity=row.get("quantity", 0),
            employee_id=row.get("employee_id"),
            reference_id=row.get("reference_id"),
            transaction_date=row.get("transaction_date"),
            notes=row.get("notes")
        )

    def to_dict(self):
        return {
            "transaction_id": self.transaction_id,
            "transaction_type": self.transaction_type,
            "product_id": self.product_id,
            "location_id": self.location_id,
            "quantity": self.quantity,
            "employee_id": self.employee_id,
            "reference_id": self.reference_id,
            "transaction_date": self.transaction_date,
            "notes": self.notes
        }
