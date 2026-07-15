# Shipment Model
class Shipment:
    def __init__(self, shipment_id=None, order_id=None, tracking_number="", carrier="", shipping_cost=0.00, ship_date=None, delivery_date=None, status="In Transit"):
        self.shipment_id = shipment_id
        self.order_id = order_id
        self.tracking_number = tracking_number
        self.carrier = carrier
        self.shipping_cost = float(shipping_cost)
        self.ship_date = ship_date
        self.delivery_date = delivery_date
        self.status = status

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            shipment_id=row.get("shipment_id"),
            order_id=row.get("order_id"),
            tracking_number=row.get("tracking_number"),
            carrier=row.get("carrier"),
            shipping_cost=row.get("shipping_cost", 0.00),
            ship_date=row.get("ship_date"),
            delivery_date=row.get("delivery_date"),
            status=row.get("status", "In Transit")
        )

    def to_dict(self):
        return {
            "shipment_id": self.shipment_id,
            "order_id": self.order_id,
            "tracking_number": self.tracking_number,
            "carrier": self.carrier,
            "shipping_cost": self.shipping_cost,
            "ship_date": self.ship_date,
            "delivery_date": self.delivery_date,
            "status": self.status
        }
