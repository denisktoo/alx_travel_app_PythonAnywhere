from django.core.management.base import BaseCommand
from listings.models import Listing
from django.contrib.auth.models import User
import random

class Command(BaseCommand):
    help = 'Seed the database with sample listings data.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('🌱 Seeding sample listings...'))

        # Try to get the first user
        host = User.objects.first()

        if not host:
            self.stdout.write(self.style.WARNING('⚠️ No users found. Creating default user...'))
            host = User.objects.create_user(
                username='defaultuser',
                email='defaultuser@gmail.com',
                password='password@123'
            )
            self.stdout.write(self.style.SUCCESS(f'✅ Default user created: {host.username}'))

        # Create 10 sample listings
        for i in range(10):
            Listing.objects.create(
                host=host,
                name=f"Sample Listing {i+1}",
                description="This is a sample property description.",
                location=f"Sample City {i+1}",
                price_per_night=random.randint(50, 200)
            )

        self.stdout.write(self.style.SUCCESS('✅ Sample listings created successfully.'))
