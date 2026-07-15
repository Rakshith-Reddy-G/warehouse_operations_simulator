# Inventory Model
class Inventory:
    def __init__(self, inventory_id=None, product_id=None, location_id=None, quantity_on_hand=0, quantity_reserved=0, quantity_allocated=0, last_updated=None):
        self.inventory_id = inventory_id
        self.product_id = product_id
        self.location_id = location_id
        self.quantity_on_hand = int(quantity_on_hand)
        self.quantity_reserved = int(quantity_reserved)
        self.quantity_allocated = int(quantity_allocated)
        self.last_updated = last_updated

    @property
    def quantity_available(self):
        return self.quantity_on_hand - self.quantity_reserved

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            inventory_id=row.get("inventory_id"),
            product_id=row.get("product_id"),
            location_id=row.get("location_id"),
            quantity_on_hand=row.get("quantity_on_hand", 0),
            quantity_reserved=row.get("quantity_reserved", 0),
            quantity_allocated=row.get("quantity_allocated", 0),
            last_updated=row.get("last_updated")
        )

    def to_dict(self):
        return {
            "inventory_id": self.inventory_id,
            "product_id": self.product_id,
            "location_id": self.location_id,
            "quantity_on_hand": self.quantity_on_hand,
            "quantity_reserved": self.quantity_reserved,
            "quantity_allocated": self.quantity_allocated,
            "last_updated": self.last_updated
        }
