# Warehouse Location Model
class WarehouseLocation:
    def __init__(self, location_id=None, zone="", aisle=0, shelf=0, bin=0, max_capacity=100, current_capacity=0):
        self.location_id = location_id
        self.zone = zone
        self.aisle = int(aisle)
        self.shelf = int(shelf)
        self.bin = int(bin)
        self.max_capacity = int(max_capacity)
        self.current_capacity = int(current_capacity)

    @property
    def label(self):
        return f"{self.zone}-A{self.aisle}S{self.shelf}B{self.bin}"

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            location_id=row.get("location_id"),
            zone=row.get("zone"),
            aisle=row.get("aisle", 0),
            shelf=row.get("shelf", 0),
            bin=row.get("bin", 0),
            max_capacity=row.get("max_capacity", 100),
            current_capacity=row.get("current_capacity", 0)
        )

    def to_dict(self):
        return {
            "location_id": self.location_id,
            "zone": self.zone,
            "aisle": self.aisle,
            "shelf": self.shelf,
            "bin": self.bin,
            "max_capacity": self.max_capacity,
            "current_capacity": self.current_capacity
        }
