from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

class User(AbstractUser):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    first_name = models.CharField(max_length=30, null=False)
    last_name = models.CharField(max_length=150, null=False)
    email = models.EmailField(unique=True, null=False)
    password = models.CharField(max_length=128)
    phone_number = models.CharField(max_length=20, null=True)
    
    ROLE_CHOICES = [
        ('guest', 'Guest'),
        ('host', 'Host'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name', 'role']

    def __str__(self):
        return self.email

class Listing(models.Model):
    property_id = models.AutoField(primary_key=True)
    host = models.ForeignKey('User', on_delete=models.CASCADE, related_name='listings')
    name = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Listing {self.property_id}: {self.name}"

class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    property = models.ForeignKey('Listing', on_delete=models.CASCADE)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    rating = models.DecimalField(max_digits=3, decimal_places=2)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review {self.review_id} by {self.user.first_name} for {self.property.name}"

class Booking(models.Model):
    booking_id = models.AutoField(primary_key=True)
    property = models.ForeignKey('Listing', on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking {self.booking_id} by {self.user.first_name} for {self.property.name}"
    
class Payment(models.Model):
    transaction_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE, related_name='payments')
    status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed')
    ])
    amount = models.FloatField()

    def __str__(self):
        return f"Payment {self.transaction_id} for {self.booking.user}"
