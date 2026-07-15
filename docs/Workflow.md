# Warehouse Operations Simulation Workflow

This document illustrates the lifecycle of items and orders moving through the simulated warehouse.

## 1. Operations Workflow Diagram

```mermaid
flowchart TD
    subgraph Inbound_Logistics [Inbound Stage]
        A[Supplier Shipment Check-In] --> B{QA Inspection}
        B -- Fail --> C[Scrapped / Returned to Supplier]
        B -- Pass --> D[Stored Procedure: AllocateInventoryLocation]
        D --> E[Stock Placed in Bins]
    end

    subgraph Outbound_Logistics [Outbound Stage]
        F[Customer Order Created] --> G[Stored Procedure: ReserveInventoryForOrder]
        G -- Stock Available --> H[Order Status: Picking]
        G -- Stockout --> I[Order Status: Pending Backorder]
        H --> J[Generate Sequence-Optimized Pick Path]
        J --> K[Picker Completes Item Picking]
        K --> L[Packing Stations: PackingManager]
        L --> M[Assigned Packer Cartonizes Items]
        M --> N[Order Status: Packed]
    end

    subgraph Shipping_Logistics [Shipping Stage]
        N --> O[Handover to Carrier FedEx/UPS/DHL]
        O --> P[Tracking Generated, Inventory Deducted]
        P --> Q[Order Status: Shipped]
        Q --> R[Simulate Transit & Delivery]
        R --> S[Order Status: Delivered]
    end

    subgraph Reverse_Logistics [Reverse Stage]
        S --> T{Customer Returns Item?}
        T -- No --> U[Order Finalized]
        T -- Yes --> V[Returns Intake & Evaluation]
        V --> W{QA Inspect Return}
        W -- Defective / Damaged --> X[Scrap / Write-off Item]
        W -- Buyer Remorse / Normal --> Y[Re-shelve Item to Inventory]
        X & Y --> Z[Refund Issued to Customer]
    end
```

## 2. Operational Event Triggers
*   **Receiving**: Triggers a `RECEIVING` transaction record + `PUT_AWAY` transaction. Increments `quantity_on_hand` in inventory.
*   **Reservation**: Triggers a `RESERVATION` transaction record. Moves items from `quantity_on_hand` to `quantity_reserved`.
*   **Picking**: Triggers a `PICKING` transaction record as the Picker moves items from the shelf to the cart.
*   **Packing**: Triggers a `PACKING` transaction record. Packer prepares the physical parcel and verifies order lines.
*   **Shipping**: Handover to carrier carrier. Triggers a `SHIPPING` transaction record. Deducts the quantities from `quantity_on_hand` and `quantity_reserved` completely.
*   **Delivery**: Simulates the customer receiving the order. Triggers a `DELIVERY` transaction.
*   **Returns**: Triggers a `RETURN_INSPECTED` transaction. Initiates restocking transactions if items pass inspection, otherwise registers quality write-off audits.
