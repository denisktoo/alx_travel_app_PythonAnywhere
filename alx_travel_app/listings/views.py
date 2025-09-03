from rest_framework import viewsets, generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import ListingSerializer, BookingSerializer, RegisterSerializer, UserSerializer, PaymentSerializer
from .models import Listing, Booking, User, Payment
from django.shortcuts import get_object_or_404
from .permissions import IsHostOrAdminUser
from .filter import ListingFilter, BookingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .pagination import ListingPagination, BookingPagination
import os
import requests
from rest_framework.response import Response
from rest_framework.decorators import action
from .tasks import send_payment_confirmation_email, send_booking_confirmation_email
import uuid

CHAPA_SECRET_KEY = os.getenv('CHAPA_SECRET_KEY')
CHAPA_BASE_URL = os.getenv('CHAPA_BASE_URL', 'https://api.chapa.co/v1')

class ListingsViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticated, IsHostOrAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ListingFilter
    pagination_class = ListingPagination
    
    def perform_create(self, serializer):
        serializer.save(host=self.request.user)

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = BookingFilter
    pagination_class = BookingPagination

    def get_queryset(self):
        listing_id = self.kwargs.get('listing_pk')
        return Booking.objects.filter(property_id=listing_id)

    def perform_create(self, serializer):
        listing = get_object_or_404(Listing, pk=self.kwargs.get('listing_pk'))
        booking = serializer.save(user=self.request.user, property=listing)

        # Send booking confirmation email asynchronously
        send_booking_confirmation_email.delay(
            booking.user.email,
            booking.booking_id,
            booking.total_price
        )

        # Automatically initiate payment after booking
        payment = Payment.objects.create(
            booking=booking,
            amount=booking.total_price,
            status="Pending"
        )

        base_url = "http://127.0.0.1:8000"
        callback_url = f"{base_url}/listings/{listing.pk}/bookings/{booking.pk}/payments/verify/"
        return_url = f"{base_url}/listings/{listing.pk}/bookings/{booking.pk}/payments/success/"

        payload = {
            "amount": str(booking.total_price),
            "currency": "ETB",
            "email": booking.user.email,
            "first_name": booking.user.first_name,
            "last_name": booking.user.last_name,
            "tx_ref": str(payment.transaction_id),
            "callback_url": callback_url,
            "return_url": return_url
        }

        headers = {
            "Authorization": f"Bearer {CHAPA_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        chapa_url = f"{CHAPA_BASE_URL}/transaction/initialize"
        response = requests.post(chapa_url, json=payload, headers=headers)
        data = response.json()

        if response.status_code == 200 and data.get('status') == 'success':
            return data
        else:
            # If payment init fails, mark booking as unpaid or handle as needed
            payment.status = "Failed"
            payment.save()
            return {"error": "Failed to initialize Chapa payment", "details": data}

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing and retrieving users.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        booking_id = self.kwargs.get('booking_pk')
        return Payment.objects.filter(booking_id=booking_id)
    
    def create(self, request, listing_pk=None, booking_pk=None):
        # Get the booking
        booking = get_object_or_404(Booking, pk=booking_pk, property_id=listing_pk)

        # Save payment to DB with Pending status
        payment = Payment.objects.create(
            booking=booking,
            amount=booking.total_price,
            status="Pending"
        )

        # Dynamically build URLs for callback and return
        base_url = "http://127.0.0.1:8000"
        callback_url = f"{base_url}/listings/{listing_pk}/bookings/{booking_pk}/payments/verify/"
        return_url = f"{base_url}/listings/{listing_pk}/bookings/{booking_pk}/payments/success/"

        # Prepare Chapa API payload
        payload = {
            "amount": str(booking.total_price),
            "currency": "ETB",
            "email": booking.user.email,
            "first_name": booking.user.first_name,
            "last_name": booking.user.last_name,
            "tx_ref": str(payment.transaction_id),
            "callback_url": callback_url,
            "return_url": return_url
        }

        headers = {
            "Authorization": f"Bearer {CHAPA_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        # Make request to Chapa API
        chapa_url = f"{CHAPA_BASE_URL}/transaction/initialize"
        response = requests.post(chapa_url, json=payload, headers=headers)
        data = response.json()

        if response.status_code == 200 and data.get('status') == 'success':
            return Response({
                "payment": PaymentSerializer(payment).data,
                "checkout_url": data['data']['checkout_url']
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['get'], url_path='verify')
    def verify_payment(self, request, listing_pk=None, booking_pk=None):
        """
        Verify payment status with Chapa using tx_ref from query params or booking_id
        """
        tx_ref = request.query_params.get("tx_ref")
        if not tx_ref:
            return Response({"error": "tx_ref is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Call Chapa verify API
        headers = {
            "Authorization": f"Bearer {CHAPA_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        verify_url = f"{CHAPA_BASE_URL}/transaction/verify/{tx_ref}"
        try:
            response = requests.get(verify_url, headers=headers)
            data = response.json()
        except Exception as e:
            return Response({"error": f"Error contacting Chapa: {str(e)}"},
                            status=status.HTTP_502_BAD_GATEWAY)

        # Find the booking & last payment
        booking = get_object_or_404(Booking, pk=booking_pk, property_id=listing_pk)
        payment = Payment.objects.filter(booking=booking).last()
        if not payment:
            return Response({"error": "Payment record not found"}, status=status.HTTP_404_NOT_FOUND)

        # Update payment status
        chapa_status = data.get('data', {}).get('status')
        if data.get('status') == 'success' and chapa_status == 'success':
            payment.status = "Completed"
            payment.save()

            # Send confirmation email asynchronously
            send_payment_confirmation_email.delay(
                booking.user.email,
                booking.booking_id,
                payment.amount
            )

            return Response({
                "message": "Payment verified successfully",
                "payment": PaymentSerializer(payment).data,
                "chapa_response": data
            }, status=status.HTTP_200_OK)
        else:
            payment.status = "Failed"
            payment.save()
            return Response({
                "message": "Payment verification failed",
                "payment": PaymentSerializer(payment).data,
                "chapa_response": data
            }, status=status.HTTP_400_BAD_REQUEST)