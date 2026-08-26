from django.contrib import admin
from django.urls import path
from . import views


urlpatterns = [
    path('', views.store, name='store'),
    path('st', views.storest, name='storest'),
    path('sale/', views.products_on_sale, name='products_on_sale'),
    path('saleshop/', views.products_on_sale_shop, name='products_on_sale_shop'),
    path('category/<slug:Category_slug>/', views.products_by_category, name='products_by_category'),
    path('<slug:Category_slug>/', views.products_category, name='products_category'),
    path('Brands/<slug:Brand_slug>/', views.Brands, name='Brand'),
    path('product/<slug:product_slug>/',views.Product_detail, name='Product_detail'),
    path('sub/<slug:subcategory_slug>/', views.store_subcategory, name='products_by_subcategory'),
    # path('search/', views.search, name='search'),
    path('ajax/search/', views.ajax_search, name='ajax_search'),
    path('countdown/update/', views.update_sale_countdown, name='update_sale_countdown'),
    path('countdown/remove/', views.remove_sale_countdown, name='remove_sale_countdown'),
    path('get-variation-details/', views.get_variation_details, name='get_variation_details'),
    path('Page/<slug:Page_slug>/', views.pages, name='pages'),
    path('about/<slug:About_Us_slug>/', views.about, name='about'),
 ]
