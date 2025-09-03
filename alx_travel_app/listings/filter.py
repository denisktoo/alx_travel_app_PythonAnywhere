import django_filters
from .models import Listing, Booking

class ListingFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr='iexact')
    price_per_night = django_filters.NumberFilter(field_name="price", lookup_expr='lte')
    location = django_filters.CharFilter(field_name="location", lookup_expr='icontains')

    class Meta:
        model = Listing
        fields = ['name', 'price_per_night', 'location']

class BookingFilter(django_filters.FilterSet):
    user = django_filters.CharFilter(field_name="user", lookup_expr='iexact')
    start_date = django_filters.DateTimeFilter(field_name="start_date", lookup_expr='gte')
    end_date = django_filters.DateTimeFilter(field_name="end_date", lookup_expr='lte')

    class Meta:
        model = Booking
        fields = ['user', 'start_date', 'end_date']
