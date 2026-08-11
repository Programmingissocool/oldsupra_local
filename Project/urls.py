from django.contrib import admin
from django.urls import path
from . import views


urlpatterns = [
    path('Projects/<slug:Project_slug>/', views.Projects, name='Projects'),
    path('Projects_ongoing', views.Projects_ongoing, name='Projects_ongoing'),
    path('Projects_completed', views.Projects_completed, name='Projects_completed'),
    path('All_Projects', views.All_Projects, name='All_Projects'),
]
