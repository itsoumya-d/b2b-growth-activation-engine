from dataclasses import dataclass
from enum import Enum
from typing import Optional, List

class ActivationStage(str, Enum):
    WORKSPACE_SETUP = "WORKSPACE_SETUP"
    ERP_DISCOVERY = "ERP_DISCOVERY"
    PILOT_EXECUTION = "PILOT_EXECUTION"
    ACTIVATED = "ACTIVATED"
    CHURN_RISK = "CHURN_RISK"

@dataclass
class WorkspaceProfile:
    tenant_id: str
    org_name: str
    industry: str
    created_at_ts: float
    current_stage: ActivationStage = ActivationStage.WORKSPACE_SETUP
    ttfv_seconds: Optional[float] = None
    actions_completed: int = 0

@dataclass
class OperationalOrder:
    order_id: str
    sku: str
    quantity_ordered: int
    quantity_available: int
    unit_price: float
    supplier_price: float

class TriageAction(str, Enum):
    AUTO_RECONCILE = "AUTO_RECONCILE"
    BACKORDER_SPLIT = "BACKORDER_SPLIT"
    DISCREPANCY_FLAG = "DISCREPANCY_FLAG"

@dataclass
class TriageDecision:
    order_id: str
    action: TriageAction
    explanation: str
    fulfilled_qty: int
    backorder_qty: int
    cost_impact_cents: int
