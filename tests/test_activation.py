import pytest
from src.activation.models import (
    WorkspaceProfile,
    ActivationStage,
    OperationalOrder,
    TriageAction
)
from src.activation.funnel import ActivationFunnelGovernor
from src.activation.triage import OpsTriageAgent

def test_funnel_progression_and_ttfv():
    start_time = 1000.0
    profile = WorkspaceProfile(
        tenant_id="tenant-acme-123",
        org_name="Acme Wholesale",
        industry="Manufacturing",
        created_at_ts=start_time
    )

    assert profile.current_stage == ActivationStage.WORKSPACE_SETUP

    # Advance to ERP Discovery
    ActivationFunnelGovernor.advance_stage(profile, start_time + 300)
    assert profile.current_stage == ActivationStage.ERP_DISCOVERY

    # Advance to Pilot Execution
    ActivationFunnelGovernor.advance_stage(profile, start_time + 900)
    assert profile.current_stage == ActivationStage.PILOT_EXECUTION

    # Advance to Activated
    ActivationFunnelGovernor.advance_stage(profile, start_time + 1800)
    assert profile.current_stage == ActivationStage.ACTIVATED
    assert profile.ttfv_seconds == 1800.0

def test_health_evaluation_churn_risk():
    start_time = 1000.0
    profile = WorkspaceProfile(
        tenant_id="tenant-stalled-456",
        org_name="Slow Logistics",
        industry="Logistics",
        created_at_ts=start_time,
        actions_completed=1
    )

    # 3 days later without progress
    ActivationFunnelGovernor.evaluate_health(profile, current_time_ts=start_time + 260000.0)
    assert profile.current_stage == ActivationStage.CHURN_RISK

def test_cohort_metrics_aggregation():
    p1 = WorkspaceProfile(tenant_id="1", org_name="A", industry="Wholesale", created_at_ts=0, current_stage=ActivationStage.ACTIVATED, ttfv_seconds=3600)
    p2 = WorkspaceProfile(tenant_id="2", org_name="B", industry="Retail", created_at_ts=0, current_stage=ActivationStage.ACTIVATED, ttfv_seconds=7200)
    p3 = WorkspaceProfile(tenant_id="3", org_name="C", industry="Mfg", created_at_ts=0, current_stage=ActivationStage.ERP_DISCOVERY)

    metrics = ActivationFunnelGovernor.calculate_cohort_metrics([p1, p2, p3])
    assert metrics["total_tenants"] == 3
    assert metrics["activated_count"] == 2
    assert metrics["activation_rate_pct"] == 66.7
    assert metrics["avg_ttfv_hours"] == 1.5

def test_ops_triage_auto_reconcile():
    order = OperationalOrder(
        order_id="po-101",
        sku="SKU-STEEL-BOLT",
        quantity_ordered=500,
        quantity_available=1000,
        unit_price=10.0,
        supplier_price=10.2  # 2% diff within 5% tolerance
    )
    decision = OpsTriageAgent.triage_order(order)
    assert decision.action == TriageAction.AUTO_RECONCILE
    assert decision.fulfilled_qty == 500
    assert decision.backorder_qty == 0

def test_ops_triage_backorder_split():
    order = OperationalOrder(
        order_id="po-102",
        sku="SKU-HYDRAULIC-PUMP",
        quantity_ordered=50,
        quantity_available=20,
        unit_price=250.0,
        supplier_price=250.0
    )
    decision = OpsTriageAgent.triage_order(order)
    assert decision.action == TriageAction.BACKORDER_SPLIT
    assert decision.fulfilled_qty == 20
    assert decision.backorder_qty == 30

def test_ops_triage_price_discrepancy_flag():
    order = OperationalOrder(
        order_id="po-103",
        sku="SKU-VALVE-SEAL",
        quantity_ordered=100,
        quantity_available=500,
        unit_price=20.0,
        supplier_price=25.0  # 25% discrepancy
    )
    decision = OpsTriageAgent.triage_order(order)
    assert decision.action == TriageAction.DISCREPANCY_FLAG
    assert decision.cost_impact_cents == 50000
    assert "Supplier price variance" in decision.explanation
