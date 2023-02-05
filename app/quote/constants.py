"""
Constant Classes/Values to be leveraged for the Quote API
"""
import json
import typing as t
from dataclasses import dataclass

from django.db import models as m
from django.utils.translation import gettext_lazy as _


class DataClassField(m.JSONField):
    """Map Python's dataclass to model"""

    def __init__(self, dataClass, *args, **kwargs):
        self.dataClass = dataClass
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["dataClass"] = self.dataClass
        return name, path, args, kwargs

    def from_db_value(self, value: str, expression, connection) -> dict[str, t.Any]:
        if value is None:
            return value
        obj = json.loads(value)
        return obj

    def to_python(self, value: str) -> dict[str, t.Any]:
        if isinstance(value, self.dataClass):
            return value
        if value is None:
            return value
        obj = json.loads(value)
        return obj

    def get_prep_value(self, value: dict[str, t.Any]) -> str:
        if value is None:
            return value
        return json.dumps(value)


class QuoteCoverageTypes(m.TextChoices):
    """Options for QuoteCoverageTypes"""

    Basic = "Basic", _("Basic")
    Premium = "Premium", _("Premium")


@dataclass
class QuoteCoverageTypesCost:
    """Dataclass to map the coverage type to the price"""

    Basic: int
    Premium: int


@dataclass
class QuoteFlatCostCoverages:
    """Dataclass to store flat cost coverages"""

    """
        Rules for adding a flat cost coverage:
        - Use naming convention:
            <attribute name>_coverage
        - Use a TextChoice and dataclass when the coverage requires
          multiple options
    """
    type_coverage: QuoteCoverageTypes
    pet_coverage: bool

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__)


@dataclass
class QuotePercentageCostCoverages:
    """Dataclass to store percentage cost coverages"""

    """
        Rules for adding a flat cost coverage:
        - Use naming convention:
            <attribute name>_coverage
        - Use a TextChoice and dataclass when the coverage requires
          multiple options
    """
    flood_coverage: bool

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__)


class States(m.TextChoices):
    """Options for States"""

    """
        Rules for adding a new state:
        - Use naming convention:
            <FSNV> = <2 letter state code>, _("<full state name>")
        - NOTE: FSNV stands for Full State Name as a Variable
        - NOTE: The variable should replace all spaces with `_`
    """

    California = "CA", _("California")
    Texas = "TX", _("Texas")
    New_York = "NY", _("New York")


@dataclass
class StateSpecificCosts:
    """Dataclass to store the cost of all coverages"""

    """
        Rules for adding a new cost coverage:
        - QuoteFlatCostCoverage will have a naming convention of:
            <attribute_name>_cost: int
        - QuotePercentageCostCoverages will have a naming convention of:
            <attribute_name>_percentage_cost: float
    """
    type_coverage_cost: QuoteCoverageTypesCost
    pet_coverage_cost: int
    flood_coverage_percentage_cost: float
    tax_rate: float

    def __init__(
        self,
        type_coverage_cost_basic: int = 20,
        type_coverage_cost_premium: int = 40,
        pet_coverage_cost: int = 20,
    ):
        self.type_coverage_cost = QuoteCoverageTypesCost(
            Basic=type_coverage_cost_basic, Premium=type_coverage_cost_premium
        )
        self.pet_coverage_cost = pet_coverage_cost


@dataclass
class CaliforniaCost(StateSpecificCosts):
    """California coverage costs"""

    def __init__(self):
        super().__init__()
        self.flood_coverage_percentage_cost = 2
        self.tax_rate = 1


@dataclass
class TexasCost(StateSpecificCosts):
    """Texas coverage costs"""

    def __init__(self):
        super().__init__()
        self.flood_coverage_percentage_cost = 50
        self.tax_rate = 0.5


@dataclass
class NewYorkCost(StateSpecificCosts):
    """New York coverage costs"""

    def __init__(self):
        super().__init__()
        self.flood_coverage_percentage_cost = 10
        self.tax_rate = 2


# Extend this mapping when adding a new state
STATE_MAPPING_COSTS: dict[str, t.Any] = {
    States.California: CaliforniaCost(),  # type: ignore
    States.Texas: TexasCost(),  # type: ignore
    States.New_York: NewYorkCost(),  # type: ignore
}
