from django.db import models
from ckeditor.fields import RichTextField
from django.urls import reverse
# from shop.models import Brand

# Create your models here.


class ProjectCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(max_length=500, blank=True)
    cat_image = models.ImageField(upload_to='photos/projectcategories', blank=True)

    class Meta:
        verbose_name = 'projectcategory'
        verbose_name_plural = 'Project Categories'

    # def get_url(self):
    #     return reverse('projects_by_category', args=[self.slug])
    def __str__(self):
        return self.name


class EndUser(models.Model):
    Company_name  = models.CharField(max_length=50, unique=True)
    Description    = RichTextField()
    slug           = models.SlugField(max_length=50, unique=True)
    vat_number     = models.CharField(max_length=50, unique=True)
    phone_number   = models.CharField(max_length=50, unique=True)
    address        = models.CharField(max_length=50, unique=True)
    website        = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return str(self.Company_name)


class Project(models.Model):
    Project_name   = models.CharField(max_length=50, unique=True)
    Description    = RichTextField()
    slug           = models.SlugField(max_length=50, unique=True)
    short          = models.TextField(max_length=500, blank=True)
    images         = models.ImageField(upload_to='photos/Projects')
    ongoing        = models.BooleanField(default=True)
    completed      = models.BooleanField(default=False)
    created_date   = models.DateTimeField(auto_now_add=True)
    modified_date  = models.DateTimeField(auto_now=True)
    start_date     = models.DateTimeField(auto_now=False)
    end_date       = models.DateTimeField(auto_now=False)
    duration       = models.CharField(max_length=50, unique=False)
    category       = models.ManyToManyField(ProjectCategory)
    client         = models.ManyToManyField(EndUser)
    # brands         = models.ManyToManyField(Brand)



    def get_url(self):
        return reverse('Projects', args=[self.slug])


    def __str__(self):
        return str(self.Project_name)


class ProjectGallery(models.Model):
    project = models.ForeignKey(Project, default=None, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='photos/Projects', max_length=255)

    def __str__(self):
        return self.project.Project_name

    class Meta:
        verbose_name = 'projectgallery'
        verbose_name_plural = 'Project Gallery'
