"""
Serializers for the Quote API View
"""
from core.models import Quote
from rest_framework import serializers


class QuoteSerializer(serializers.ModelSerializer):
    """Serializer for quotes"""

    class Meta:
        model = Quote
        fields = (
            "id",
            "buyer_first_name",
            "buyer_last_name",
            "coverage_type",
        )
        read_only_fields = ["id"]


class QuoteDetailSerializer(QuoteSerializer):
    """Serializer for quote detail view"""

    class Meta(QuoteSerializer.Meta):
        fields = QuoteSerializer.Meta.fields + (  # type: ignore
            "pet_coverage",
            "state",
            "additional_coverage",
        )
