# Employee Model
class Employee:
    def __init__(self, employee_id=None, first_name="", last_name="", email="", role="", status="Active", hire_date=None):
        self.employee_id = employee_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.role = role
        self.status = status
        self.hire_date = hire_date

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            employee_id=row.get("employee_id"),
            first_name=row.get("first_name"),
            last_name=row.get("last_name"),
            email=row.get("email"),
            role=row.get("role"),
            status=row.get("status", "Active"),
            hire_date=row.get("hire_date")
        )

    def to_dict(self):
        return {
            "employee_id": self.employee_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "role": self.role,
            "status": self.status,
            "hire_date": self.hire_date
        }
