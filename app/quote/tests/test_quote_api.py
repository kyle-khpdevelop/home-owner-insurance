"""
Tests for the quote API
"""
import json
from decimal import Decimal

from core.models import Quote
from core.models import User
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from quote.serializers import QuoteDetailSerializer
from quote.serializers import QuoteSerializer
from rest_framework import status
from rest_framework.test import APIClient

QUOTES_URL = reverse("quote:quote-list")


def _detail_url(quote_id: int) -> str:
    """Create and return a quote detail URL"""
    return reverse("quote:quote-detail", args=[quote_id])


def _create_user(**params) -> User:
    """Create and return a new user"""
    return get_user_model().objects.create_user(**params)


def _create_quote(user: User, **params):
    """Create and return a sample quote"""
    defaults = {
        "buyer_first_name": "Test",
        "buyer_last_name": "User",
        "state": "CA",
        "flat_cost_coverages": {"type_coverage": "Basic", "pet_coverage": True},
        "percentage_cost_coverages": {"flood_coverage": True},
    }
    defaults.update(params)
    quote = Quote.objects.create(user=user, **defaults)
    return quote


class PublicQuoteAPITests(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API"""
        res = self.client.get(QUOTES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateQuoteAPITests(TestCase):
    """Test authorized API requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@example.com", password="testPassword123"
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_quotes(self):
        """Test retrieving a list of quotes"""
        _create_quote(user=self.user)
        _create_quote(user=self.user)

        res = self.client.get(QUOTES_URL)

        quotes = Quote.objects.all().order_by("-id")
        serializer = QuoteSerializer(quotes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_quote_detail(self):
        """Test get quote detail"""
        quote = _create_quote(user=self.user)

        url = _detail_url(quote.id)
        res = self.client.get(url)
        serializer = QuoteDetailSerializer(quote)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_quote(self):
        """Test creating a quote"""
        payload = {
            "buyer_first_name": "Test",
            "buyer_last_name": "User",
            "state": "TX",
            "flat_cost_coverages": {
                "type_coverage": "Premium",
                "pet_coverage": False,
            },
            "percentage_cost_coverages": {"flood_coverage": False},
        }
        res = self.client.post(QUOTES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        quote = Quote.objects.get(id=res.data["id"])
        for k, v in payload.items():
            attribute = getattr(quote, k)
            if k in ("flat_cost_coverages", "percentage_cost_coverages"):
                attribute = json.loads(attribute)
            self.assertEqual(attribute, v)
        self.assertEqual(quote.user, self.user)

    def test_partial_update(self):
        """Test partial update of a quote"""
        original_state = "CA"
        quote = _create_quote(
            user=self.user,
            buyer_first_name="Test",
            buyer_last_name="User",
            state=original_state,
        )

        payload = {"buyer_first_name": "New", "buyer_last_name": "Name"}
        url = _detail_url(quote.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        quote.refresh_from_db()
        self.assertEqual(quote.buyer_first_name, payload["buyer_first_name"])
        self.assertEqual(quote.buyer_last_name, payload["buyer_last_name"])
        self.assertEqual(quote.state, original_state)
        self.assertEqual(quote.user, self.user)

    def test_full_update(self):
        """Test full update of quote"""
        quote = _create_quote(
            user=self.user,
            buyer_first_name="Test",
            buyer_last_name="User",
            state="TX",
            flat_cost_coverages={"type_coverage": "Basic", "pet_coverage": False},
            percentage_cost_coverages={"flood_coverage": False},
        )

        payload = {
            "buyer_first_name": "New",
            "buyer_last_name": "Name",
            "state": "CA",
            "flat_cost_coverages": {"type_coverage": "Premium", "pet_coverage": True},
            "percentage_cost_coverages": {"flood_coverage": True},
        }
        url = _detail_url(quote.id)
        res = self.client.put(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        quote.refresh_from_db()
        for k, v in payload.items():
            attribute = getattr(quote, k)
            self.assertEqual(attribute, v)
        self.assertEqual(quote.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the quote user results in an error"""
        new_user = _create_user(email="newUser@example.com", password="testPassword123")
        quote = _create_quote(user=self.user)

        payload = {"user": new_user.id}
        url = _detail_url(quote.id)
        self.client.patch(url, payload)

        quote.refresh_from_db()
        self.assertEqual(quote.user, self.user)

    def test_delete_quote(self):
        """Test deleting a quote successfully"""
        quote = _create_quote(user=self.user)

        url = _detail_url(quote.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Quote.objects.filter(id=quote.id))

    def test_delete_other_users_receipe_error(self):
        """Test trying to delete another user's quote gives error"""
        new_user = _create_user(
            email="newUser@example.com",
            password="testPassword123",
        )
        quote = _create_quote(user=new_user)

        url = _detail_url(quote.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Quote.objects.filter(id=quote.id).exists())

    def test_create_quote_bad_data_state(self):
        """Test creating a quote with bad data"""
        payload = {"state": None}
        res = self.client.post(QUOTES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        payload = {"state": "ZZ"}
        res = self.client.post(QUOTES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_quote_bad_data_flat_cost_coverage(self):
        """Test creating a quote with bad data"""
        payload = {"flat_cost_coverages": {}}
        res = self.client.post(QUOTES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        payload = {
            "flat_cost_coverages": {
                "bad_coverage": True,
            }
        }
        res = self.client.post(QUOTES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        payload = {
            "flat_cost_coverages": {
                "bad_coverage": True,
                "type_coverage": "Premium",
                "pet_coverage": True,
            }
        }
        res = self.client.post(QUOTES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        payload = {
            "flat_cost_coverages": {
                "type_coverage": "Super Premium",
                "pet_coverage": True,
            }
        }
        res = self.client.post(QUOTES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        payload = {"flat_cost_coverages": {"type_coverage": None, "pet_coverage": True}}
        res = self.client.post(QUOTES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        payload = {
            "flat_cost_coverages": {"type_coverage": "Basic", "pet_coverage": None}
        }
        res = self.client.post(QUOTES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_quote_bad_data_percentage_cost_coverage(self):
        """Test creating a quote with bad data"""
        payload = {"percentage_cost_coverages": {}}
        res = self.client.post(QUOTES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        payload = {
            "percentage_cost_coverages": {
                "bad_coverage": True,
            }
        }
        res = self.client.post(QUOTES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        payload = {
            "percentage_cost_coverages": {
                "bad_coverage": True,
                "flood_coverage": True,
            }
        }
        res = self.client.post(QUOTES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        payload = {"percentage_cost_coverages": {"flood_coverage": None}}
        res = self.client.post(QUOTES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_validate_california_cost(self):
        state = "CA"
        payload = {
            "buyer_first_name": "Test",
            "buyer_last_name": "User",
            "state": state,
            "flat_cost_coverages": {"type_coverage": "Basic", "pet_coverage": True},
            "percentage_cost_coverages": {"flood_coverage": True},
        }

        res = self.client.post(QUOTES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        quote = Quote.objects.get(id=res.data["id"])
        self.assertEqual(quote.state, state)
        self.assertEqual(quote.monthly_subtotal, Decimal("40.8"))
        self.assertEqual(quote.monthly_taxes, Decimal("0.41"))
        self.assertEqual(quote.monthly_total, Decimal("41.21"))

        payload = {
            "buyer_first_name": "Test",
            "buyer_last_name": "User",
            "state": state,
            "flat_cost_coverages": {"type_coverage": "Premium", "pet_coverage": True},
            "percentage_cost_coverages": {"flood_coverage": True},
        }

        res = self.client.post(QUOTES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        quote = Quote.objects.get(id=res.data["id"])
        self.assertEqual(quote.state, state)
        self.assertEqual(quote.monthly_subtotal, Decimal("61.2"))
        self.assertEqual(quote.monthly_taxes, Decimal("0.61"))
        self.assertEqual(quote.monthly_total, Decimal("61.81"))

        payload = {
            "buyer_first_name": "Test",
            "buyer_last_name": "User",
            "state": state,
            "flat_cost_coverages": {"type_coverage": "Premium", "pet_coverage": False},
            "percentage_cost_coverages": {"flood_coverage": True},
        }

        res = self.client.post(QUOTES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        quote = Quote.objects.get(id=res.data["id"])
        self.assertEqual(quote.state, state)
        self.assertEqual(quote.monthly_subtotal, Decimal("40.8"))
        self.assertEqual(quote.monthly_taxes, Decimal("0.41"))
        self.assertEqual(quote.monthly_total, Decimal("41.21"))

        payload = {
            "buyer_first_name": "Test",
            "buyer_last_name": "User",
            "state": state,
            "flat_cost_coverages": {"type_coverage": "Premium", "pet_coverage": False},
            "percentage_cost_coverages": {"flood_coverage": False},
        }

        res = self.client.post(QUOTES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        quote = Quote.objects.get(id=res.data["id"])
        self.assertEqual(quote.state, state)
        self.assertEqual(quote.monthly_subtotal, Decimal("40"))
        self.assertEqual(quote.monthly_taxes, Decimal("0.4"))
        self.assertEqual(quote.monthly_total, Decimal("40.40"))

    def test_validate_texas_cost(self):
        state = "TX"
        payload = {
            "buyer_first_name": "Test",
            "buyer_last_name": "User",
            "state": state,
            "flat_cost_coverages": {"type_coverage": "Basic", "pet_coverage": True},
            "percentage_cost_coverages": {"flood_coverage": True},
        }

        res = self.client.post(QUOTES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        quote = Quote.objects.get(id=res.data["id"])
        self.assertEqual(quote.state, state)
        self.assertEqual(quote.monthly_subtotal, Decimal("60"))
        self.assertEqual(quote.monthly_taxes, Decimal("0.3"))
        self.assertEqual(quote.monthly_total, Decimal("60.30"))

        payload = {
            "buyer_first_name": "Test",
            "buyer_last_name": "User",
            "state": state,
            "flat_cost_coverages": {"type_coverage": "Premium", "pet_coverage": True},
            "percentage_cost_coverages": {"flood_coverage": True},
        }

        res = self.client.post(QUOTES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        quote = Quote.objects.get(id=res.data["id"])
        self.assertEqual(quote.state, state)
        self.assertEqual(quote.monthly_subtotal, Decimal("90"))
        self.assertEqual(quote.monthly_taxes, Decimal("0.45"))
        self.assertEqual(quote.monthly_total, Decimal("90.45"))

        payload = {
            "buyer_first_name": "Test",
            "buyer_last_name": "User",
            "state": state,
            "flat_cost_coverages": {"type_coverage": "Premium", "pet_coverage": False},
            "percentage_cost_coverages": {"flood_coverage": True},
        }

        res = self.client.post(QUOTES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        quote = Quote.objects.get(id=res.data["id"])
        self.assertEqual(quote.state, state)
        self.assertEqual(quote.monthly_subtotal, Decimal("60"))
        self.assertEqual(quote.monthly_taxes, Decimal("0.3"))
        self.assertEqual(quote.monthly_total, Decimal("60.30"))

        payload = {
            "buyer_first_name": "Test",
            "buyer_last_name": "User",
            "state": state,
            "flat_cost_coverages": {"type_coverage": "Premium", "pet_coverage": False},
            "percentage_cost_coverages": {"flood_coverage": False},
        }

        res = self.client.post(QUOTES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        quote = Quote.objects.get(id=res.data["id"])
        self.assertEqual(quote.state, state)
        self.assertEqual(quote.monthly_subtotal, Decimal("40"))
        self.assertEqual(quote.monthly_taxes, Decimal("0.20"))
        self.assertEqual(quote.monthly_total, Decimal("40.20"))

    def test_validate_new_york_cost(self):
        state = "NY"
        payload = {
            "buyer_first_name": "Test",
            "buyer_last_name": "User",
            "state": state,
            "flat_cost_coverages": {"type_coverage": "Basic", "pet_coverage": True},
            "percentage_cost_coverages": {"flood_coverage": True},
        }

        res = self.client.post(QUOTES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        quote = Quote.objects.get(id=res.data["id"])
        self.assertEqual(quote.state, state)
        self.assertEqual(quote.monthly_subtotal, Decimal("44"))
        self.assertEqual(quote.monthly_taxes, Decimal("0.88"))
        self.assertEqual(quote.monthly_total, Decimal("44.88"))

        payload = {
            "buyer_first_name": "Test",
            "buyer_last_name": "User",
            "state": state,
            "flat_cost_coverages": {"type_coverage": "Premium", "pet_coverage": True},
            "percentage_cost_coverages": {"flood_coverage": True},
        }

        res = self.client.post(QUOTES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        quote = Quote.objects.get(id=res.data["id"])
        self.assertEqual(quote.state, state)
        self.assertEqual(quote.monthly_subtotal, Decimal("66"))
        self.assertEqual(quote.monthly_taxes, Decimal("1.32"))
        self.assertEqual(quote.monthly_total, Decimal("67.32"))

        payload = {
            "buyer_first_name": "Test",
            "buyer_last_name": "User",
            "state": state,
            "flat_cost_coverages": {"type_coverage": "Premium", "pet_coverage": False},
            "percentage_cost_coverages": {"flood_coverage": True},
        }

        res = self.client.post(QUOTES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        quote = Quote.objects.get(id=res.data["id"])
        self.assertEqual(quote.state, state)
        self.assertEqual(quote.monthly_subtotal, Decimal("44"))
        self.assertEqual(quote.monthly_taxes, Decimal("0.88"))
        self.assertEqual(quote.monthly_total, Decimal("44.88"))

        payload = {
            "buyer_first_name": "Test",
            "buyer_last_name": "User",
            "state": state,
            "flat_cost_coverages": {"type_coverage": "Premium", "pet_coverage": False},
            "percentage_cost_coverages": {"flood_coverage": False},
        }

        res = self.client.post(QUOTES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        quote = Quote.objects.get(id=res.data["id"])
        self.assertEqual(quote.state, state)
        self.assertEqual(quote.monthly_subtotal, Decimal("40"))
        self.assertEqual(quote.monthly_taxes, Decimal("0.80"))
        self.assertEqual(quote.monthly_total, Decimal("40.80"))
