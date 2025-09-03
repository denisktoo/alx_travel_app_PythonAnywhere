from rest_framework import serializers
from .models import Listing, Booking, User, Payment

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_id', 'username', 'first_name', 'last_name', 'email', 'phone_number', 'role', 'created_at']

class ListingSerializer(serializers.ModelSerializer):
    host_name = serializers.SerializerMethodField()
    host = UserSerializer(read_only=True)

    class Meta:
        model = Listing
        fields = ['property_id', 'host', 'host_name', 'name', 'description', 'location',
                  'price_per_night', 'created_at', 'updated_at']
        read_only_fields = ['host']

    def get_host_name(self, obj):
        return f"{obj.host.first_name} {obj.host.last_name}"


class BookingSerializer(serializers.ModelSerializer):
    status = serializers.CharField()
    user = UserSerializer(read_only=True)

    property = ListingSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = ['booking_id', 'property', 'user', 'start_date', 'end_date', 'total_price', 'status', 'created_at']

    def validate_status(self, value):
        """
        Use serializers.ValidationError to validate status field.
        """
        allowed_statuses = ['confirmed', 'pending', 'cancelled']
        if value.lower() not in allowed_statuses:
            raise serializers.ValidationError(f"Status must be one of {allowed_statuses}.")
        return value
    
class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_id', 'username', 'first_name', 'last_name', 'email', 'phone_number', 'password', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
    
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
