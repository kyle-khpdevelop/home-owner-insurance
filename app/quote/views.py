"""
Views for the Quote APIs
"""
import json

import quote.utils as quote_util
from core.models import Quote
from quote.constants import QuoteCoverageTypes
from quote.constants import QuoteFlatCostCoverages
from quote.constants import QuotePercentageCostCoverages
from quote.constants import States
from quote.serializers import QuoteDetailSerializer
from quote.serializers import QuoteSerializer
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import ModelSerializer


class QuoteViewSet(viewsets.ModelViewSet):
    """View for manage Quote APIs"""

    serializer_class = QuoteSerializer
    queryset = Quote.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_class = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve quotes for authenticated user"""
        if self.request.user.id is None:
            raise AuthenticationFailed("Unauthorized", code=401)
        return self.queryset.filter(user=self.request.user.id).order_by("-id")

    def get_serializer_class(self):
        """Return the serializer class for request"""
        if self.action == "list":
            return QuoteSerializer

        return QuoteDetailSerializer

    def perform_create(self, serializer: ModelSerializer):
        """Create a new quote"""

        serializer.validated_data["state"] = States(serializer.validated_data["state"])

        (
            monthly_subtotal,
            monthly_taxes,
            monthly_total,
        ) = quote_util.calculate_quote_cost(
            serializer.validated_data["state"],
            serializer.validated_data["flat_cost_coverages"],
            serializer.validated_data["percentage_cost_coverages"],
        )
        serializer.validated_data["monthly_subtotal"] = monthly_subtotal
        serializer.validated_data["monthly_taxes"] = monthly_taxes
        serializer.validated_data["monthly_total"] = monthly_total

        flat_cost_coverage_data = serializer.validated_data["flat_cost_coverages"]
        flat_cost_coverages = QuoteFlatCostCoverages(
            type_coverage=QuoteCoverageTypes(flat_cost_coverage_data["type_coverage"]),
            pet_coverage=flat_cost_coverage_data["pet_coverage"],
        )
        serializer.validated_data["flat_cost_coverages"] = json.dumps(
            flat_cost_coverages, cls=quote_util.EnhancedJSONEncoder
        )

        percentage_cost_coverage_data = serializer.validated_data[
            "percentage_cost_coverages"
        ]
        percentage_cost_coverages = QuotePercentageCostCoverages(
            flood_coverage=percentage_cost_coverage_data.get("flood_coverage"),
        )
        serializer.validated_data["percentage_cost_coverages"] = json.dumps(
            percentage_cost_coverages, cls=quote_util.EnhancedJSONEncoder
        )

        serializer.save(user=self.request.user)
