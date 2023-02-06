"""
Views for the Quote APIs
"""
import quote.utils as quote_util
from core.models import Quote
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
        return self.queryset.filter(user=self.request.user).order_by("-id")

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

        serializer.save(user=self.request.user)
