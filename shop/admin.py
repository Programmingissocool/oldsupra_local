from django import forms
from django.contrib import admin
from . models import Brand, Category, subcategory, Product, ProductGallery, Brand, Banner, Variation, Color, Size, Page, About_Us, Fabric, About_UsGallery, Site_Content
import admin_thumbnails
from modeltranslation.admin import TranslationAdmin, TabbedTranslationAdmin
from django.conf import settings
from django.utils.html import format_html
from adminsortable2.admin import SortableAdminMixin
from django.contrib.admin.widgets import AdminFileWidget




class Site_ContentAdmin(TabbedTranslationAdmin):
    list_display = ('name', 'sale_countdown_enabled', 'sale_countdown_ends_at')



# Register your models here.

class VariationInline(admin.TabularInline):
    model = Variation
    readonly_fields = ('image_tag',)
    
    
@admin_thumbnails.thumbnail('image')
class About_UsGalleryInline(admin.TabularInline):
    model = About_UsGallery
    extra = 1
    

class About_UsAdmin(TabbedTranslationAdmin):
	list_display=('name',)
	list_display_link = ('name', )
	inlines = [About_UsGalleryInline]
	
	
	


class PageAdmin(TabbedTranslationAdmin):
	list_display=('page_name','description')
	list_display_link = ('page_name', )	


class ColorAdmin(TabbedTranslationAdmin):
	list_display=('title','title_en','title_ka', 'color_bg')
	list_display_link = ('title', 'color_bg')
	list_editable=('title_en','title_ka')

class SizeAdmin(admin.ModelAdmin):
    list_display=('title',)
    
class FabricAdmin(TabbedTranslationAdmin):
    list_display=('title','title_en','title_ka')
    list_editable=('title_en','title_ka')
    


class BannerAdmin(TabbedTranslationAdmin):
    def thumbnail(self, object):
        try:
            return format_html('<img src="{}" width="100" style="border-radius:50%;">'.format(object.images.url))
        except:
            return '-'
    thumbnail.short_description = 'Thumbnail'
    list_display = ('Banner_name','description','availiable','thumbnail','brands')
    list_editable = ('description','availiable','brands')
    prepopulated_fields = {'slug': ('Banner_name',)}
    save_as = True


class BrandAdmin(TranslationAdmin):
    list_display = ('Brand_name','description')
    

    


class CategoryAdmin(SortableAdminMixin,TabbedTranslationAdmin):
    prepopulated_fields = {'slug': ('category_name',)}
    list_display = ('category_name','slug','my_order','promotion')
    list_editable = ('promotion',)

    

    save_as = True
  
 



    class Media:
        js = (
            'http://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js',
            'http://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/jquery-ui.min.js',
            'modeltranslation/js/tabbed_translation_fields.js',
        )
        css = {
            'screen': ('modeltranslation/css/tabbed_translation_fields.css',),
        }
        
        

admin.site.register(Category,CategoryAdmin)
# class subcategory2Admin(admin.ModelAdmin):
#     list_display = ('subcategory_name', 'slug',)
#     list_editable = ( 'slug', 'maincategory')
#
#     class Media:
#         js = (
#             'http://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js',
#             'http://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/jquery-ui.min.js',
#             'modeltranslation/js/tabbed_translation_fields.js',
#         )
#         css = {
#             'screen': ('https://marketit.ge/tabbed_translation_fields.css',),
#         }





class subcategoryAdmin(SortableAdminMixin,admin.ModelAdmin):
    list_display = ('subcategory_name', 'slug', 'maincategory','my_order')
    list_display_links = ('subcategory_name',)
    list_editable = ('maincategory',)
    prepopulated_fields = {'slug': ('subcategory_name',)}
    ordering = ['my_order']
   
    


@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery

# @admin.action(description="Apply 10% discount to product and all its variations")
# def apply_10_percent_discount_to_product_and_variations(modeladmin, request, queryset):
#     for product in queryset:
#         try:
#             price = float(product.price)
#             product.discount_price = round(price * 0.9, 2)
#             product.is_on_sale = True
#             product.save()

#             variations = Variation.objects.filter(product=product)
#             for var in variations:
#                 var.discount_price = round(float(var.price) * 0.9, 2)
#                 var.save()
#         except Exception as e:
#             print(f"Error applying discount to {product}: {e}")

from django.utils.html import format_html
from django.contrib import admin

class ProductAdmin(SortableAdminMixin, TabbedTranslationAdmin):
    
    

    def thumbnail(self, object):
        try:
            return format_html('<img src="{}" width="100" style="border-radius:50%;">', object.images.url)
        except:
            return '-'
    thumbnail.short_description = 'Thumbnail'

    def variations_display(self, obj):
        variations = obj.variation_set.all()
        if variations.exists():
            html = "<br>".join(
                f"{var.color or ''} {var.size or ''} - {var.price:.2f} -- Disc {var.discount_price:.2f} ₾"
                for var in variations
            )
            return format_html(html)
        return '-'
    variations_display.short_description = 'Variations (name - price)'

    # IMPORTANT: Directly use "price" here, NOT a method.
    list_display = ('my_order', 'id', 'Product_name', 'price','discount_price', 'variations_display','is_availiable', 'is_on_sale','is_new', 'thumbnail')
    list_filter = ('category',)
    list_display_links = ('Product_name',)  # Keep product_name clickable, allows 'price' to be editable

    # Explicitly put the real model field here:
    list_editable = ('price', 'is_availiable','is_on_sale','is_new')

    actions = ['apply_discount_to_products','apply_20discount_to_products','apply_25discount_to_products','apply_30discount_to_products','apply_35discount_to_products','apply_40discount_to_products','apply_50discount_to_products']

    @admin.action(description="Apply 10 percent discount to selected products and variations")
    def apply_discount_to_products(self, request, queryset):
        for product in queryset:
            product.discount_price = round(product.price * 0.9, 2)
            product.is_on_sale = True
            product.save()

            variations = product.variation_set.all()
            for var in variations:
                var.discount_price = round(var.price * 0.9, 2)
                var.save()

        self.message_user(request, "10 percent discount applied successfully.")
        
    @admin.action(description="Apply 20 percent discount to selected products and variations")
    def apply_20discount_to_products(self, request, queryset):
        for product in queryset:
            product.discount_price = round(product.price * 0.8, 2)
            product.is_on_sale = True
            product.save()

            variations = product.variation_set.all()
            for var in variations:
                var.discount_price = round(var.price * 0.8, 2)
                var.save()

        self.message_user(request, "20 percent discount applied successfully.") 
        
    @admin.action(description="Apply 25 percent discount to selected products and variations")
    def apply_25discount_to_products(self, request, queryset):
        for product in queryset:
            product.discount_price = round(product.price * 0.75, 2)
            product.is_on_sale = True
            product.save()

            variations = product.variation_set.all()
            for var in variations:
                var.discount_price = round(var.price * 0.75, 2)
                var.save()

        self.message_user(request, "25 percent discount applied successfully.")     
        
        
    @admin.action(description="Apply 30 percent discount to selected products and variations")
    def apply_30discount_to_products(self, request, queryset):
        for product in queryset:
            product.discount_price = round(product.price * 0.7, 2)
            product.is_on_sale = True
            product.save()

            variations = product.variation_set.all()
            for var in variations:
                var.discount_price = round(var.price * 0.7, 2)
                var.save()

        self.message_user(request, "30 percent discount applied successfully.")
     
        
    @admin.action(description="Apply 35 percent discount to selected products and variations")
    def apply_35discount_to_products(self, request, queryset):
        for product in queryset:
            product.discount_price = round(product.price * 0.65, 2)
            product.is_on_sale = True
            product.save()

            variations = product.variation_set.all()
            for var in variations:
                var.discount_price = round(var.price * 0.65, 2)
                var.save()

        self.message_user(request, "35 percent discount applied successfully.")    
        
        
    @admin.action(description="Apply 40 percent discount to selected products and variations")
    def apply_40discount_to_products(self, request, queryset):
        for product in queryset:
            product.discount_price = round(product.price * 0.6, 2)
            product.is_on_sale = True
            product.save()

            variations = product.variation_set.all()
            for var in variations:
                var.discount_price = round(var.price * 0.6, 2)
                var.save()

        self.message_user(request, "40 percent discount applied successfully.")   
        
        
    @admin.action(description="Apply 50 percent discount to selected products and variations")
    def apply_50discount_to_products(self, request, queryset):
        for product in queryset:
            product.discount_price = round(product.price * 0.5, 2)
            product.is_on_sale = True
            product.save()

            variations = product.variation_set.all()
            for var in variations:
                var.discount_price = round(var.price * 0.5, 2)
                var.save()

        self.message_user(request, "50 percent discount applied successfully.")        

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "subcategory":
            category_id = request.POST.get("category_id")
            kwargs["queryset"] = subcategory.objects.filter(maincategory_id=category_id) if category_id else subcategory.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    list_per_page = 10
    search_fields = ['Product_name_en', 'Product_name_ka']
    fieldsets = ()
    save_as = True
    save_on_top = True
    inlines = [ProductGalleryInline, VariationInline]



admin.site.register(subcategory,subcategoryAdmin)
admin.site.register(Product,ProductAdmin)
admin.site.register(Banner,BannerAdmin)
admin.site.register(Brand,BrandAdmin)
admin.site.register(ProductGallery)
admin.site.register(Color,ColorAdmin)
admin.site.register(Size,SizeAdmin)
admin.site.register(Page,PageAdmin)
admin.site.register(About_Us,About_UsAdmin)
admin.site.register(Fabric,FabricAdmin)
admin.site.register(About_UsGallery)
admin.site.register(Site_Content,Site_ContentAdmin)

