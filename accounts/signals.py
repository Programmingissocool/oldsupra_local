from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Account, UserProfile
from django.utils.text import slugify

@receiver(post_save, sender=Account)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Ensure the slug is unique
        slug_base = slugify(f"{instance.first_name}-{instance.last_name}")
        slug = slug_base
        counter = 1

        # Attempt to generate a unique slug
        while UserProfile.objects.filter(slug=slug).exists():
            slug = f"{slug_base}-{counter}"
            counter += 1

        # Create the user profile with the unique slug
        try:
            UserProfile.objects.create(user=instance, slug=slug)
        except Exception as e:
            print(f"Error creating user profile: {e}")
