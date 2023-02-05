"""
Utility functionality to be leveraged for the Quote API
"""
import dataclasses
import json
import typing as t
from decimal import Decimal

from quote.constants import STATE_MAPPING_COSTS


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


def calculate_quote_cost(
    state: str,
    flat_cost_coverages: dict[str, t.Any],
    percentage_cost_coverages: dict[str, t.Any],
) -> tuple[Decimal, Decimal, Decimal]:
    """Takes the quote's state and coverages and returns the subtotal and taxes for a quote"""
    monthly_subtotal = 0.0
    monthly_taxes = 0.0
    monthly_total = 0.0

    state_coverage_cost = STATE_MAPPING_COSTS.get(state)

    if state_coverage_cost is None:
        raise ValueError(f"There is no coverage cost specified for: {state}")

    for k, v in flat_cost_coverages.items():
        attribute_name = f"{k}_cost"
        if type(v) is bool and v is True:
            attr_cost = getattr(state_coverage_cost, attribute_name)
            monthly_subtotal += attr_cost

        elif type(v) is str:
            attr_class = getattr(state_coverage_cost, attribute_name)
            attr_cost = getattr(attr_class, v)
            monthly_subtotal += attr_cost

    for k, v in percentage_cost_coverages.items():
        attribute_name = f"{k}_percentage_cost"
        if type(v) is bool and v is True:
            attr_cost = getattr(state_coverage_cost, attribute_name)
            monthly_subtotal *= 1 + (attr_cost / 100)

        elif type(v) is str:
            attr_class = getattr(state_coverage_cost, attribute_name)
            attr_cost = getattr(attr_class, v)
            monthly_subtotal *= 1 + (attr_cost / 100)

    monthly_taxes = monthly_subtotal * (state_coverage_cost.tax_rate / 100)
    monthly_total = monthly_subtotal + monthly_taxes

    return (Decimal(monthly_subtotal), Decimal(monthly_taxes), Decimal(monthly_total))
