from django.urls import path, include
from rest_framework import routers
from rest_framework_nested.routers import NestedDefaultRouter
from .views import ListingsViewSet, BookingViewSet, RegisterView, UserViewSet, PaymentViewSet

router = routers.DefaultRouter()
router.register(r'listings', ListingsViewSet, basename='listing')
router.register(r'users', UserViewSet, basename='user')

# Nested router of  bookings under listings
nested_router = NestedDefaultRouter(router, r'listings', lookup='listing')
nested_router.register(r'bookings', BookingViewSet, basename='listing-bookings')

# Nested router of payments under bookings
payments_router = NestedDefaultRouter(nested_router, r'bookings', lookup='booking')
payments_router.register(r'payments', PaymentViewSet, basename='booking-payments')

urlpatterns =[
    path('', include(router.urls)),
    path('', include(nested_router.urls)),
    path('', include(payments_router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
]