from .models import OperationalOrder, TriageDecision, TriageAction

class OpsTriageAgent:
    """
    Autonomous operational agent for physical goods supply chain triage.
    """
    PRICE_TOLERANCE_PCT = 0.05  # 5% acceptable price discrepancy

    @classmethod
    def triage_order(cls, order: OperationalOrder) -> TriageDecision:
        # 1. Price discrepancy check
        price_diff = abs(order.unit_price - order.supplier_price)
        max_allowed_diff = order.unit_price * cls.PRICE_TOLERANCE_PCT

        if price_diff > max_allowed_diff:
            diff_pct = round((price_diff / order.unit_price) * 100, 1)
            cost_impact = int(price_diff * order.quantity_ordered * 100)
            return TriageDecision(
                order_id=order.order_id,
                action=TriageAction.DISCREPANCY_FLAG,
                explanation=f"Supplier price variance ({diff_pct}%) exceeds 5% threshold",
                fulfilled_qty=0,
                backorder_qty=order.quantity_ordered,
                cost_impact_cents=cost_impact
            )

        # 2. Inventory fulfillment triage
        if order.quantity_available >= order.quantity_ordered:
            return TriageDecision(
                order_id=order.order_id,
                action=TriageAction.AUTO_RECONCILE,
                explanation="Inventory fully matches order quantity and price matches PO",
                fulfilled_qty=order.quantity_ordered,
                backorder_qty=0,
                cost_impact_cents=0
            )

        # 3. Partial backorder split
        backorder = order.quantity_ordered - order.quantity_available
        return TriageDecision(
            order_id=order.order_id,
            action=TriageAction.BACKORDER_SPLIT,
            explanation=f"Partial stock allocated ({order.quantity_available}/{order.quantity_ordered}); backorder created",
            fulfilled_qty=order.quantity_available,
            backorder_qty=backorder,
            cost_impact_cents=0
        )
