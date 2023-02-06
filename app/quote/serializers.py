"""
Serializers for the Quote API View
"""
from core.models import Quote
from rest_framework import serializers


class FlatCostCoveragesSerializer(serializers.Serializer):
    type_coverage = serializers.ChoiceField(
        choices=["Basic", "Premium"],
        default="Basic",
        help_text="The type of coverage",
    )
    pet_coverage = serializers.BooleanField(
        default=False,
        help_text="Optional coverage for pets",
    )


class PercentageCostCoveragesSerializer(serializers.Serializer):
    flood_coverage = serializers.BooleanField(
        default=False,
        help_text="Optional coverage for floods",
    )


class QuoteSerializer(serializers.ModelSerializer):
    """Serializer for quotes"""

    class Meta:
        model = Quote
        fields = (
            "id",
            "buyer_first_name",
            "buyer_last_name",
        )
        read_only_fields = ["id"]


class QuoteDetailSerializer(QuoteSerializer):
    """Serializer for quote detail view"""

    flat_cost_coverages = FlatCostCoveragesSerializer(help_text="Flat Cost Coverages")
    percentage_cost_coverages = PercentageCostCoveragesSerializer(
        help_text="Percentage Cost Coverages"
    )

    class Meta(QuoteSerializer.Meta):
        fields = QuoteSerializer.Meta.fields + (  # type: ignore
            "state",
            "flat_cost_coverages",
            "percentage_cost_coverages",
            "monthly_subtotal",
            "monthly_taxes",
            "monthly_total",
        )
        read_only_fields = [
            "monthly_subtotal",
            "monthly_taxes",
            "monthly_total",
        ]
