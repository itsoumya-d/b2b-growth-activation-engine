from typing import List, Dict, Any
from .models import WorkspaceProfile, ActivationStage

class ActivationFunnelGovernor:
    """
    Tracks self-serve onboarding velocity, activation milestones, and churn risks.
    """
    STAGE_ORDER = [
        ActivationStage.WORKSPACE_SETUP,
        ActivationStage.ERP_DISCOVERY,
        ActivationStage.PILOT_EXECUTION,
        ActivationStage.ACTIVATED
    ]

    @classmethod
    def advance_stage(cls, profile: WorkspaceProfile, current_time_ts: float) -> WorkspaceProfile:
        profile.actions_completed += 1
        if profile.current_stage == ActivationStage.ACTIVATED:
            return profile

        if profile.current_stage == ActivationStage.CHURN_RISK:
            profile.current_stage = ActivationStage.PILOT_EXECUTION
            return profile

        current_idx = cls.STAGE_ORDER.index(profile.current_stage)
        next_stage = cls.STAGE_ORDER[current_idx + 1]
        profile.current_stage = next_stage

        if next_stage == ActivationStage.ACTIVATED and profile.ttfv_seconds is None:
            profile.ttfv_seconds = max(1.0, current_time_ts - profile.created_at_ts)

        return profile

    @classmethod
    def evaluate_health(cls, profile: WorkspaceProfile, current_time_ts: float, max_idle_seconds: float = 172800.0) -> WorkspaceProfile:
        """
        Flags churn risk if a tenant is stalled without reaching activation.
        Default max idle is 48 hours.
        """
        if profile.current_stage != ActivationStage.ACTIVATED:
            elapsed = current_time_ts - profile.created_at_ts
            if elapsed > max_idle_seconds and profile.actions_completed < 2:
                profile.current_stage = ActivationStage.CHURN_RISK
        return profile

    @classmethod
    def calculate_cohort_metrics(cls, profiles: List[WorkspaceProfile]) -> Dict[str, Any]:
        if not profiles:
            return {"total_tenants": 0, "activation_rate_pct": 0.0, "avg_ttfv_hours": 0.0}

        activated = [p for p in profiles if p.current_stage == ActivationStage.ACTIVATED and p.ttfv_seconds is not None]
        rate = round((len(activated) / len(profiles)) * 100.0, 1)
        avg_ttfv = round(sum(p.ttfv_seconds for p in activated) / len(activated) / 3600.0, 2) if activated else 0.0

        return {
            "total_tenants": len(profiles),
            "activated_count": len(activated),
            "activation_rate_pct": rate,
            "avg_ttfv_hours": avg_ttfv
        }
