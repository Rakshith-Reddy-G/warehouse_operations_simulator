# Supplier Model
class Supplier:
    def __init__(self, supplier_id=None, supplier_name="", contact_name="", email="", phone="", address="", performance_rating=5.00):
        self.supplier_id = supplier_id
        self.supplier_name = supplier_name
        self.contact_name = contact_name
        self.email = email
        self.phone = phone
        self.address = address
        self.performance_rating = float(performance_rating)

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            supplier_id=row.get("supplier_id"),
            supplier_name=row.get("supplier_name"),
            contact_name=row.get("contact_name"),
            email=row.get("email"),
            phone=row.get("phone"),
            address=row.get("address"),
            performance_rating=row.get("performance_rating", 5.00)
        )

    def to_dict(self):
        return {
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier_name,
            "contact_name": self.contact_name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "performance_rating": self.performance_rating
        }
