"""Generate mock data for development."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmers_companion.settings')
django.setup()

from apps.farmers.models import Farmer, Crop, Location


def seed():
    loc, _ = Location.objects.get_or_create(name='Nairobi', county='Nairobi County')
    maize, _ = Crop.objects.get_or_create(name='Maize')
    wheat, _ = Crop.objects.get_or_create(name='Wheat')

    farmer, created = Farmer.objects.get_or_create(
        phone_number='+254700000001',
        defaults={'name': 'John Kamau', 'location': loc},
    )
    farmer.crops.set([maize, wheat])
    farmer.save()

    print(f"Seeded farmer: {farmer} ({'created' if created else 'already exists'})")


if __name__ == '__main__':
    seed()
