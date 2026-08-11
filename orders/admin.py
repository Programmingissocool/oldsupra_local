
from django.contrib import admin
from .models import Payment, Order, OrderProduct
# Register your models here.
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin, ImportExportMixin, ExportActionMixin

class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    readonly_fields = ['product_image']
    extra = 0
    fields = ['product_image', 'product', 'color', 'size', 'quantity', 'product_price', 'ordered','gift']

    def product_image(self, instance):
        if not instance.pk:
            return "No Image"

        product = instance.product

        # If color and size are empty, use the default product image
        if not instance.color and not instance.size:
            if product and getattr(product, 'images', None) and product.images.name:
                return format_html('<img src="{}" width="150" height="150" />', product.images.url)

        # If there is a variation with an image, show it
        variation = instance.variation
        if variation and getattr(variation, 'image', None) and variation.image.name:
            return format_html('<img src="{}" width="150" height="150" />', variation.image.url)

        # Fallback: first product gallery image
        gallery_item = product.productgallery_set.order_by('id').first() if product else None
        if gallery_item and getattr(gallery_item, 'image', None) and gallery_item.image.name:
            return format_html('<img src="{}" width="150" height="150" />', gallery_item.image.url)

        # Final fallback
        return "No Image"

    product_image.short_description = "Product Image"

@admin.action(description="Return selected orders to New")
def mark_orders_new(modeladmin, request, queryset):
    updated = queryset.update(status='New')
    modeladmin.message_user(request, f"{updated} order(s) returned to New.")



@admin.action(description="Mark selected orders as Completed")
def mark_orders_completed(modeladmin, request, queryset):
    updated = queryset.update(status='Completed')
    modeladmin.message_user(request, f"{updated} order(s) marked as Completed.")

class OrderAdmin(ImportExportMixin,admin.ModelAdmin):
    
    
    change_list_template = "admin/import_export/change_list.html"
    list_display = ['order_number', 'full_name', 'phone', 'email', 'city', 'order_total', 'tax', 'status', 'is_ordered', 'created_at']
    list_filter = ['status', 'is_ordered']
    search_fields = ['order_number', 'first_name', 'last_name', 'phone', 'email']
    list_per_page = 20
    inlines = [OrderProductInline]
    actions = [mark_orders_completed, mark_orders_new]  # Registering the custom action

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.GET.get('status__exact') is not None:
            return qs
        return qs.filter(status='New')

# class OrderAdmin(admin.ModelAdmin):
#     list_display = ['order_number', 'full_name', 'phone', 'email', 'city', 'order_total', 'tax', 'status', 'is_ordered', 'created_at']
#     list_filter = ['status', 'is_ordered']
#     search_fields = ['order_number', 'first_name', 'last_name', 'phone', 'email']
#     list_per_page = 20
#     inlines = [OrderProductInline]
    
#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         if request.GET.get('status__exact') is not None:
#             return qs
#         return qs.filter(status='New')
    
    

class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_id','status','amount_paid','bank','created_at']
    list_filter = ['status']
 

admin.site.register(Payment, PaymentAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderProduct)