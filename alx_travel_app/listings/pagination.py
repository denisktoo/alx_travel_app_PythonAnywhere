from rest_framework.pagination import PageNumberPagination
from .models import Listing, Booking
from rest_framework.response import Response

class ListingPagination(PageNumberPagination):
    page_size = 15

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'results': data
        })
    
class BookingPagination(PageNumberPagination):
    page_size = 15

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'results': data
        })
