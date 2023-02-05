"""
Tests for the quote API
"""
import json

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
        "coverage_type": "Basic",
        "pet_coverage": True,
        "state": "CA",
        "additional_coverage": {"flood_coverage": True},
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
            "coverage_type": "Premium",
            "pet_coverage": False,
            "state": "TX",
            "additional_coverage": {"flood_coverage": False},
        }
        res = self.client.post(QUOTES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        quote = Quote.objects.get(id=res.data["id"])
        for k, v in payload.items():
            attribute = getattr(quote, k)
            if k == "additional_coverage":
                attribute = json.loads(attribute)
            self.assertEqual(attribute, v)
        self.assertEqual(quote.user, self.user)

    def test_partial_update(self):
        """Test partial update of a quote"""
        original_coverage_type = "Premium"
        quote = _create_quote(
            user=self.user,
            buyer_first_name="Test",
            buyer_last_name="User",
            coverage_type=original_coverage_type,
        )

        payload = {"buyer_first_name": "New", "buyer_last_name": "Name"}
        url = _detail_url(quote.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        quote.refresh_from_db()
        self.assertEqual(quote.buyer_first_name, payload["buyer_first_name"])
        self.assertEqual(quote.buyer_last_name, payload["buyer_last_name"])
        self.assertEqual(quote.coverage_type, original_coverage_type)
        self.assertEqual(quote.user, self.user)

    def test_full_update(self):
        """Test full update of quote"""
        quote = _create_quote(
            user=self.user,
            buyer_first_name="Test",
            buyer_last_name="User",
            coverage_type="Basic",
            pet_coverage=False,
            state="TX",
            additional_coverage={"flood_coverage": False},
        )

        payload = {
            "buyer_first_name": "New",
            "buyer_last_name": "Name",
            "coverage_type": "Premium",
            "pet_coverage": True,
            "state": "CA",
            "additional_coverage": {"flood_coverage": True},
        }
        url = _detail_url(quote.id)
        res = self.client.put(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        quote.refresh_from_db()
        for k, v in payload.items():
            attribute = getattr(quote, k)
            print(f"Attribute: {k} | {attribute}")
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
