from typing import Sequence

from constructs import Construct

from imports.oci.budget_budget import BudgetBudget as OciBudget
from imports.oci.budget_alert_rule import BudgetAlertRule


class Budget(Construct):
    """
    Creates a monthly budget for an OCI Compartment.

    Args:
        name: the display name of the budget
        compartment_id: the OCID of the compartment to budget
        amount: the total amount of the budget
        forecasted_alert_thresholds: thresholds, as percentages, at which to
            alert on forecasted spend
        actual_alert_thresholds: thresholds, as percentages, at which to alert
            on actual spend
        alert_recipients: emails that should receive budget alerts
    """

    def __init__(
        self,
        scope: Construct,
        id_: str,
        *,
        name: str,
        compartment_id: str,
        amount: int,
        forecasted_alert_thresholds: Sequence[float],
        actual_alert_thresholds: Sequence[float],
        alert_recipients: Sequence[str],
    ):
        super().__init__(scope, id_)

        budget = OciBudget(
            self,
            f"budget-{name}",
            display_name=name,
            amount=amount,
            compartment_id=compartment_id,
            reset_period="MONTHLY",
            target_type="COMPARTMENT",
            targets=[compartment_id],
        )

        for threshold in forecasted_alert_thresholds:
            BudgetAlertRule(
                self,
                f"budget-{name}-forecasted-{threshold}",
                budget_id=budget.id,
                threshold=threshold,
                threshold_type="PERCENTAGE",
                type="FORECAST",
                recipients=",".join(alert_recipients),
            )

        for threshold in actual_alert_thresholds:
            BudgetAlertRule(
                self,
                f"budget-{name}-actual-{threshold}",
                budget_id=budget.id,
                threshold=threshold,
                threshold_type="PERCENTAGE",
                type="ACTUAL",
                recipients=",".join(alert_recipients),
            )
