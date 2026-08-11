from django.contrib import admin
from . models import Project, ProjectCategory, EndUser, ProjectGallery
import admin_thumbnails
from django.utils.html import format_html





@admin_thumbnails.thumbnail('image')
class ProjectGalleryInline(admin.TabularInline):
    model = ProjectGallery

# Register your models here.
class ProjectAdmin(admin.ModelAdmin):
    def thumbnail(self, object):
        try:
            return format_html('<img src="{}" width="300" style="border-radius:50%;">'.format(object.images.url))
        except:
            pass # just ignore
    thumbnail.short_description = 'Project Image'

    list_display = ('Project_name','Description','ongoing','completed','thumbnail',)
    list_editable = ('Description','ongoing','completed',)
    prepopulated_fields = {'slug': ('Project_name',)}
    inlines = [ProjectGalleryInline]
    save_as = True


class ProjectCategoryAdmin(admin.ModelAdmin):
    list_display = ('name','description')
    list_editable_links = ('name','description')

class EndUserAdmin(admin.ModelAdmin):
    list_display = ('Company_name','phone_number')
    list_editable_links = ('Company_name','phone_number')



admin.site.register(Project,ProjectAdmin)
admin.site.register(ProjectCategory,ProjectCategoryAdmin)
admin.site.register(EndUser,EndUserAdmin)
# admin.site.register(ProjectGallery,ProjectGalleryInline)
