from django import forms
from django.contrib import admin
from . models import RevenueCenter, RVC_Seats, Status
import admin_thumbnails
from modeltranslation.admin import TranslationAdmin
from django.conf import settings
from django.utils.html import format_html


# Register your models here.

class RevenueCenterAdmin(admin.ModelAdmin):
    def thumbnail(self, object):
        try:
            return format_html('<img src="{}" width="100" style="border-radius:50%;">'.format(object.images.url))
        except:
            return '-'
    thumbnail.short_description = 'Thumbnail'
    list_display = ('rvc_name','description','availiable','thumbnail')
    list_editable = ('description','availiable')
    prepopulated_fields = {'slug': ('rvc_name',)}
    save_as = True


class StatusAdmin(admin.ModelAdmin):
    list_display = ('status_name',)


class RVC_SeatsAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('Table_Number',)}
    list_display = ('Table_Number','slug')

    save_as = True



   


admin.site.register(RevenueCenter,RevenueCenterAdmin)
admin.site.register(Status)
admin.site.register(RVC_Seats,RVC_SeatsAdmin)
# admin.site.register(subcategory2,)
