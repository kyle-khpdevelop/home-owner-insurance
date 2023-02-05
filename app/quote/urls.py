"""
URL Mappings for the quote app
"""
from django.urls import include
from django.urls import path
from quote import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("quotes", views.QuoteViewSet)

app_name = "quote"

urlpatterns = [path("", include(router.urls))]
