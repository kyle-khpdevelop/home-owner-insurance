"""
Views for the Quote APIs
"""
import json

from core.models import Quote
from core.models import QuoteCoverageTypes
from core.models import QuoteFlatCostCoverages
from core.models import QuotePercentageCostCoverages
from core.models import States
from quote.serializers import QuoteDetailSerializer
from quote.serializers import QuoteSerializer
from quote.utils import EnhancedJSONEncoder
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
        flat_cost_coverage_data = serializer.validated_data["flat_cost_coverage"]
        flat_cost_coverage = QuoteFlatCostCoverages(
            coverage_type=QuoteCoverageTypes(flat_cost_coverage_data["coverage_type"]),
            pet_coverage=flat_cost_coverage_data["pet_coverage"],
        )

        percentage_cost_coverage_data = serializer.validated_data[
            "percentage_cost_coverage"
        ]
        percentage_cost_coverage = QuotePercentageCostCoverages(
            flood_coverage=percentage_cost_coverage_data.get("flood_coverage"),
        )

        serializer.validated_data["state"] = States(serializer.validated_data["state"])
        serializer.validated_data["flat_cost_coverage"] = json.dumps(
            flat_cost_coverage, cls=EnhancedJSONEncoder
        )
        serializer.validated_data["percentage_cost_coverage"] = json.dumps(
            percentage_cost_coverage, cls=EnhancedJSONEncoder
        )
        serializer.save(user=self.request.user)
