from django.shortcuts import render
from Project.models import Project
from shop.models import Brand, Banner, Product, Category, ProductGallery
from django.conf import settings
from django.utils import translation
from django.urls.exceptions import Resolver404
from django.urls.base import resolve, reverse
from urllib.parse import urlparse
from django.http import HttpResponseRedirect




def home(request):
    complete_projects = Project.objects.all().filter(ongoing=True)
    done_projects = Project.objects.all().filter(completed=True)
    all_projects  = Project.objects.all()
    brands        = Brand.objects.all()
    banners       = Banner.objects.all().filter(availiable=True)
    banners2       = Banner.objects.all().filter(hamburger_menu=True)
    PProduct       = Product.objects.all()
    cats          = Category.objects.all()
    product_with_images = []
    audio_banner  = Banner.objects.all().filter(Banner_name="Audio_System")
    fire_alarm_banner  = Banner.objects.all().filter(Banner_name="Fire_Alarm")
    middle_banner_1  = Banner.objects.all().filter(Banner_name="Middle_Banner_1")
    middle_banner_2  = Banner.objects.all().filter(Banner_name="Middle_Banner_2")

    # Check if the user came from the home page
    is_from_home = False
    referer = request.META.get('HTTP_REFERER', '')
    if referer and '/home' in referer:
        is_from_home = True

    for product in product_with_images:
        gallery_images = ProductGallery.objects.filter(product=product)

        product_with_images.append({
            'product': product,
            'gallery_images': gallery_images,
        })

    context = {
        'complete_projects' : complete_projects,
        'done_projects'     : done_projects,
        'brands'            : brands,
        'banners'           : banners,
        'banners2'          : banners2,
        'PProduct'           : PProduct,
        'all_projects'      : all_projects,
        'cats'              : cats,
        'product_with_images': product_with_images,
        'audio_banner'      : audio_banner,
        'fire_alarm_banner' : fire_alarm_banner,
        'middle_banner_1'   : middle_banner_1,
        'middle_banner_2'   : middle_banner_2,
        'is_from_home': is_from_home  # Pass this flag to the template
    }

    return render(request, 'landing-page.html', context)

def contact(request):
    return render(request, 'contact.html')

def register(request):
    return render(request, 'accounts/register.html')

def login(request):
    return render(request, 'accounts/login.html')


def set_language(request, language):
    for lang, _ in settings.LANGUAGES:
        translation.activate(lang)
        try:
            view = resolve(urlparse(request.META.get("HTTP_REFERER")).path)
        except Resolver404:
            view = None
        if view:
            break
    if view:
        translation.activate(language)
        next_url = reverse(view.url_name, args=view.args, kwargs=view.kwargs)
        response = HttpResponseRedirect(next_url)
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language)
    else:
        response = HttpResponseRedirect("/")
    return response

# def set_language(request, language):
#     translation.activate(language)
#
#     try:
#         view = resolve(urlparse(request.META.get("HTTP_REFERER")).path)
#     except Resolver404:
#         view = None
#
#     if view:
#         translation.activate(language)
#         keyword = request.GET.get('keyword', '')  # Get the keyword from the current query parameters
#         query_params = request.GET.urlencode()  # Get the rest of the query parameters
#         next_url = reverse(view.url_name, args=view.args, kwargs=view.kwargs)
#
#         # Construct the next_url with the keyword and the rest of the query parameters
#         if query_params:
#             next_url += f"?keyword={keyword}&{query_params}"
#         else:
#             next_url += f"?keyword={keyword}"
#
#         response = HttpResponseRedirect(next_url)
#         response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language)
#     else:
#         response = HttpResponseRedirect("/")
#
#     return response
