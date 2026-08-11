from django.db import models
from ckeditor.fields import RichTextField
from django.urls import reverse
from django_quill.fields import QuillField
from taggit.managers import TaggableManager
# from adminsortable.models import SortableMixin

# Create your models here.


class RevenueCenter(models.Model):
    rvc_name       = models.CharField(max_length=50, unique=True)
    slug           = models.SlugField(max_length=50, unique=True)
    url            = models.CharField(max_length=50, unique=True)
    description    = RichTextField()
    images         = models.ImageField(upload_to='photos/Brands', blank = True)
    availiable     = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'RevenueCenter'
        verbose_name_plural = 'Revenue Center'

    # def get_url(self):
    #             return reverse('products_by_Brand_name', args=[self.slug])

    def __str__(self):
        return str(self.rvc_name)

    # def get_url(self):
    #     return reverse('Brand', args=[self.slug])

class Status(models.Model):
    status_name = models.CharField(max_length=30, unique=True)


    def __str__(self):
        return str(self.status_name)

class RVC_Seats(models.Model):
    Table_Number = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    status = models.ForeignKey(Status, on_delete=models.CASCADE)
    revenue_center = models.ForeignKey(RevenueCenter, on_delete=models.CASCADE)
    cat_image = models.ImageField(upload_to='photos/categories', blank=True)


    class Meta:
        verbose_name = 'RVC_Seats'
        verbose_name_plural = 'RVC Seats'

    # def get_url(self):
    #         return reverse('products_by_category', args=[self.slug])
    def __str__(self):
        return self.Table_Number
