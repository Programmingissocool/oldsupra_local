from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.urls import reverse
from django.utils.text import slugify
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings


class MyAccountManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        if not email:
            raise ValueError('Email is mandatory')

        if not username:
            raise ValueError('Username is mandatory')

        # Create the user
        user = self.model(
            email=email,
            username=username,
        )
        user.set_password(password)
        user.is_active = True
        user.save(using=self._db)

        # Check if the UserProfile already exists for this user
        if not hasattr(user, 'userprofile'):
            # Ensure the slug is unique
            slug_base = slugify(f"{email}-{username}")
            slug = slug_base
            counter = 1

            # Check if the slug already exists and append a number if it does
            while UserProfile.objects.filter(slug=slug).exists():
                slug = f"{slug_base}-{counter}"
                counter += 1

            # Create a profile for the user
            UserProfile.objects.create(user=user, slug=slug)

        return user

    def create_superuser(self, first_name, last_name, email, username, password):
        user = self.create_user(
            email=self.normalize_email(email),
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        user.is_admin = True
        user.is_active = True
        user.is_staff = True
        user.is_superadmin = True
        user.save(using=self._db)

        # Ensure the slug is unique for superuser as well
        slug_base = slugify(f"{first_name}-{last_name}")
        slug = slug_base
        counter = 1

        while UserProfile.objects.filter(slug=slug).exists():
            slug = f"{slug_base}-{counter}"
            counter += 1

        # Create a profile for the superuser
        UserProfile.objects.create(user=user, slug=slug)

        return user


# Custom User Model
class Account(AbstractBaseUser, PermissionsMixin):
    first_name   = models.CharField(max_length=50)
    last_name    = models.CharField(max_length=50)
    username     = models.CharField(max_length=50, unique=True)
    email        = models.EmailField(max_length=50, unique=True)
    phone_number = models.CharField(max_length=50)

    date_joined  = models.DateTimeField(auto_now_add=True)
    last_login   = models.DateTimeField(auto_now_add=True)
    is_admin     = models.BooleanField(default=False)
    is_staff     = models.BooleanField(default=False)
    is_active    = models.BooleanField(default=True)
    is_superadmin = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = MyAccountManager()

    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, add_label):
        return True


class TestCustomer(Account):
    class Meta:
        proxy = True
        verbose_name = 'Pretend Customer'
        verbose_name_plural = 'Pretend Customer'


# User Profile Model
class UserProfile(models.Model):
    user = models.OneToOneField(Account, on_delete=models.CASCADE)
    slug = models.SlugField(max_length=50, blank=True)
    address_line_1 = models.CharField(blank=True, max_length=100)
    address_line_2 = models.CharField(blank=True, max_length=100)
    
    # Default profile picture URL
    default_picture = 'userprofile/default_profile.png'
    profile_picture = models.ImageField(
        blank=True, 
        upload_to='userprofile',
        default=default_picture
    )
    
    city = models.CharField(blank=True, max_length=20)
    state = models.CharField(blank=True, max_length=20)
    country = models.CharField(blank=True, max_length=20)

    def __str__(self):
        return self.user.first_name

    def full_address(self):
        return f'{self.address_line_1} {self.address_line_2}'

    def get_url(self):
        return reverse('Profile', args=[self.slug])


# Signal to automatically create user profile after user registration
@receiver(post_save, sender=Account)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        slug = slugify(f"{instance.first_name}-{instance.last_name}")
        UserProfile.objects.create(user=instance, slug=slug)
