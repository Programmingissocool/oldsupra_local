from django.shortcuts import render, get_object_or_404, redirect
from . models import Brand, Product, ProductGallery, Category, subcategory, Variation, Color, Size, Banner, Page, About_Us, Fabric, About_UsGallery, Site_Content
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpResponse, HttpResponseForbidden
# from .forms import ReviewForm
from django.contrib import messages
from collections import defaultdict
from django.core.serializers import serialize
import json
from django.db.models import Min, Max
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.dateparse import parse_datetime


# Create your views here.
@staff_member_required
@require_POST
def update_sale_countdown(request):
    site_info = Site_Content.objects.filter(name="DEFAULT").first()
    if site_info is None:
        return HttpResponseForbidden("Default site content is not configured.")

    ends_at_raw = request.POST.get("sale_countdown_ends_at", "").strip()
    ends_at = parse_datetime(ends_at_raw)
    if ends_at is None:
        messages.error(request, "Enter a valid countdown end date and time.")
        return redirect(request.META.get("HTTP_REFERER", "store"))

    if timezone.is_naive(ends_at):
        ends_at = timezone.make_aware(ends_at, timezone.get_current_timezone())

    site_info.sale_countdown_enabled = True
    site_info.sale_countdown_ends_at = ends_at
    site_info.save(update_fields=["sale_countdown_enabled", "sale_countdown_ends_at"])
    messages.success(request, "Countdown updated.")
    return redirect(request.META.get("HTTP_REFERER", "store"))


@staff_member_required
@require_POST
def remove_sale_countdown(request):
    site_info = Site_Content.objects.filter(name="DEFAULT").first()
    if site_info is None:
        return HttpResponseForbidden("Default site content is not configured.")

    site_info.sale_countdown_enabled = False
    site_info.sale_countdown_ends_at = None
    site_info.save(update_fields=["sale_countdown_enabled", "sale_countdown_ends_at"])
    messages.success(request, "Countdown removed.")
    return redirect(request.META.get("HTTP_REFERER", "store"))


def pages(request, Page_slug):
        pages_full = Page.objects.get(slug=Page_slug)
        cats = Category.objects.all()
        context = {
            'pages_full': pages_full,
            'cats': cats,
        }
        return render(request, 'shop/pages_full.html', context)
        
        
def about(request, About_Us_slug):
        About_Usfull = About_Us.objects.get(slug=About_Us_slug)
        gallery_images = About_UsGallery.objects.filter(title=About_Usfull)
        cats = Category.objects.all()
        context = {
            'About_Usfull': About_Usfull,
            'cats': cats,
            'gallery_images': gallery_images,
        }
        return render(request, 'shop/about_usnew.html', context)        
     

def store(request, Category_slug=None):
        categories = None
        products = None
        brands        = Brand.objects.all()
        if Category_slug != None:
            categories = get_object_or_404(Category, slug=Category_slug)

            products = Product.objects.filter(category=categories, is_availiable=True).order_by('-created_date')

            paginator = Paginator(products, 12)
            page = request.GET.get('page')
            paged_products = paginator.get_page(page)
            product_count = products.count()
        else:
            products = Product.objects.all().filter(is_availiable=True).order_by('id')
            paginator = Paginator(products, 12)
            page = request.GET.get('page')
            paged_products = paginator.get_page(page)
            product_count = products.count()

        context = {
           'products': paged_products,
           'product_count': product_count,
           'brands' : brands,

        }
        return render(request, 'index.html', context)
        
        
def storest(request, Category_slug=None):
        categories = None
        products = None
        brands        = Brand.objects.all()
        if Category_slug != None:
            categories = get_object_or_404(Category, slug=Category_slug)

            products = Product.objects.filter(category=categories, is_availiable=True).order_by('-created_date')

            paginator = Paginator(products, 12)
            page = request.GET.get('page')
            paged_products = paginator.get_page(page)
            product_count = products.count()
        else:
            products = Product.objects.all().filter(is_availiable=True).order_by('id')
            paginator = Paginator(products, 12)
            page = request.GET.get('page')
            paged_products = paginator.get_page(page)
            product_count = products.count()

        context = {
           'products': paged_products,
           'product_count': product_count,
           'brands' : brands,

        }
        return render(request, 'index2.html', context)        


from django.db.models.functions import Lower

def search(request):
    keyword = request.GET.get('keyword', '').strip()

    products_search = Product.objects.none()
    product_count = 0

    if keyword:
        keyword_lower = keyword.lower()

        products_search = Product.objects.annotate(
            test_lower=Lower('test'),
            product_name_lower=Lower('Product_name'),
            product_name_en_lower=Lower('Product_name_en'),
            product_name_ka_lower=Lower('Product_name_ka'),
        ).filter(
            Q(test_lower__icontains=keyword_lower) |
            Q(product_name_lower__icontains=keyword_lower) |
            Q(product_name_en_lower__icontains=keyword_lower) |
            Q(product_name_ka_lower__icontains=keyword_lower)
        ).order_by('-created_date')

        product_count = products_search.count()

    context = {
        'products_search': products_search,
        'product_count': product_count,
    }

    return render(request, 'shop/search_info.html', context)
    
    

import difflib
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q
from .models import Product


def ajax_search(request):
    # lower-case იპუტი
    keyword = request.GET.get('keyword', '').strip().lower()

    # პირველი, ჩვეულებრივიicontains–ძიება
    qs = Product.objects.filter(    
        Q(short_en__icontains=keyword) |
        Q(short_ka__icontains=keyword) |
        Q(Product_name_en__icontains=keyword) |
        Q(Product_name_ka__icontains=keyword) |
        Q(test_en__icontains=keyword) |
        Q(test_ka__icontains=keyword) 
    )[:10]

    suggestions = []
    # თუ ვერ მოიძებნა, fuzzy მიმთავართება
    if not qs.exists() and keyword:
        # 1) მოვდოთ ყველაფერი DB–იდან და ავაწყოთ ორიგინალ-ლოუერ მეპი
        original_terms = []
        for p in Product.objects.all():
            if p.Product_name_en:
                original_terms.append(p.Product_name_en)
            if p.Product_name_ka:
                original_terms.append(p.Product_name_ka)

        term_map = {term.lower(): term for term in original_terms}
        lower_terms = list(term_map.keys())

        # 2) fuzzy–მიიღოთ მხოლოდ lower_terms–ში
        close_lower = difflib.get_close_matches(keyword, lower_terms, n=5, cutoff=0.5)

        # 3) ორიგინალ terms, დიდი ასოებით
        close_original = [term_map[lt] for lt in close_lower]

        # 4) DB-ში გადაინძროლეთ ორიგინალ მონაცემებით
        suggestions = Product.objects.filter(
            Q(Product_name_en__in=close_original) |
            Q(Product_name_ka__in=close_original) 
        ).distinct()[:5]

    # უკან JSON-ში აგზავნოთ HTML partial-ით
    html = render_to_string(
        'shop/partials/search_results.html',
        {'products': qs, 'suggestions': suggestions},
        request=request
    )
    return JsonResponse({'html': html})
    


def Brands(request,Brand_slug):
    brand = None
    products = None

    # comment
    if Brand_slug != None:
        brand = get_object_or_404(Brand, slug=Brand_slug)
        products = Product.objects.filter(brands=brand, is_availiable=True)
        paginator = Paginator(products, 12)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()
    else:
        products = Product.objects.all().filter(is_availiable=True).order_by('id')
        paginator = Paginator(products, 12)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()
    context = {
       'products': paged_products,
       'product_count': product_count,
       'brand' : brand,
    }
    return render(request, 'shop/brand_info.html', context)

from collections import defaultdict
import json
from django.shortcuts import render, get_object_or_404

def Product_detail(request, product_slug):

    single_product = get_object_or_404(Product, slug=product_slug)

    # Helper to get effective price
    def get_effective_price(product, variation=None):
        if variation:
            return variation.discount_price if product.is_on_sale and variation.discount_price else variation.price
        return product.discount_price if product.is_on_sale and product.discount_price else product.price

    # Fetch variations with related fields
    variations = Variation.objects.filter(product=single_product).select_related('fabric', 'color', 'size')

    rel = single_product.related.all()
    product_gallery = ProductGallery.objects.filter(product=single_product)
    banners = Banner.objects.filter(availiable=True)
    cats = Category.objects.all()

    # -----------------------------
    # COMBINED IMAGES
    # -----------------------------
    combined_images = []

    for v in variations:
        if v.image:
            combined_images.append({
                'url': v.image.url,
                'fabric_id': v.fabric.id if v.fabric else None,
                'color_id': v.color.id if v.color else None,
                'size_id': v.size.id if v.size else None,
            })

    for g in product_gallery:
        combined_images.append({
            'url': g.image.url,
            'fabric_id': None,
            'color_id': None,
            'size_id': None,
        })

    # -----------------------------
    # GROUPING VARIATIONS
    # -----------------------------
    fabrics = []
    colors_by_fabric = defaultdict(list)
    sizes_by_fabric_color = defaultdict(list)

    fabric_set = set()

    for v in variations:
        fabric_id = v.fabric.id if v.fabric else None
        color_id = v.color.id if v.color else None
        size_id = v.size.id if v.size else None

        # Add to fabric list
        if fabric_id not in fabric_set:
            fabric_set.add(fabric_id)
            fabrics.append({
                "id": fabric_id,
                "title": v.fabric.title if v.fabric else "Default",
            })

        # Add colors under each fabric
        if v.color:
            if v.color.id not in [c["id"] for c in colors_by_fabric[fabric_id]]:
                colors_by_fabric[fabric_id].append({
                    "id": v.color.id,
                    "title": v.color.title,
                    "color_code": v.color.color_code,
                })

        # Add sizes under each fabric+color
        if v.size:
            key = (fabric_id, color_id)
            sizes_by_fabric_color[key].append({
                "size_id": v.size.id,
                "size_title": v.size.title,
                "price": get_effective_price(single_product, v),
                "old_price": v.price if single_product.is_on_sale and v.discount_price else None,
            })

    # -----------------------------
    # PREPARE DATA FOR TEMPLATE
    # -----------------------------
    colors_prepared = []
    for fabric_id, colors in colors_by_fabric.items():
        colors_prepared.append({
            "fabric_id": fabric_id,
            "colors": colors
        })

    sizes_prepared = []
    for (fabric_id, color_id), sizes in sizes_by_fabric_color.items():
        sizes_prepared.append({
            "fabric_id": fabric_id,
            "color_id": color_id,
            "sizes": sizes
        })

    # -----------------------------
    # VARIATION DETAILS (for JS)
    # -----------------------------
    variation_details = {}
    for v in variations:
        fabric_id = v.fabric.id if v.fabric else None
        color_id = v.color.id if v.color else None
        size_id = v.size.id if v.size else None

        key = f"{fabric_id}-{color_id}-{size_id}"

        variation_details[key] = {
            "image_url": v.image.url if v.image else "",
            "price": get_effective_price(single_product, v),
            "old_price": v.price if single_product.is_on_sale and v.discount_price else None,
        }

    # -----------------------------
    # CONTEXT
    # -----------------------------
    context = {
        'single_product': single_product,
        'rel': rel,
        'cats': cats,
        'banners': banners,
        'fabrics': fabrics,
        'colors_prepared': colors_prepared,
        'sizes_prepared': sizes_prepared,
        'combined_images': combined_images,
        'variation_details': json.dumps(variation_details),
    }

    return render(request, 'shop/single_item.html', context)

from django.db.models import Min, Max
from django.core.paginator import Paginator

def products_category(request, Category_slug=None):
    cats = Category.objects.all()
    products = Product.objects.filter(is_availiable=True)
    brands = Brand.objects.all()
    colors = Color.objects.all()
    sizes = Size.objects.all()
    banners = Banner.objects.filter(availiable=True)

    categories = None
    if Category_slug:
        categories = get_object_or_404(Category, slug=Category_slug)
        products = products.filter(category=categories)

    # ფილტრები და დარჩენილი ლოგიკა იგივე რჩება
    color_filter = request.GET.get('color')
    if color_filter:
        products = products.filter(variation__color__title=color_filter)

    size_filter = request.GET.get('size')
    if size_filter:
        products = products.filter(variation__size__title=size_filter)

    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')

    if price_min:
        products = products.filter(price__gte=price_min)
    if price_max:
        products = products.filter(price__lte=price_max)

    products = products.distinct()

    colors_in_category = Color.objects.filter(variation__product__in=products).distinct()
    sizes_in_category = Size.objects.filter(variation__product__in=products).distinct()

    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)

    for product in paged_products:
        variations = product.variation_set.all()
        if variations.exists():
            product.min_discount = variations.aggregate(Min('discount_price'))['discount_price__min']
            product.max_discount = variations.aggregate(Max('discount_price'))['discount_price__max']
        else:
            product.min_discount = None
            product.max_discount = None

    min_price = products.aggregate(Min('price'))['price__min'] or 0
    max_price = products.aggregate(Max('price'))['price__max'] or 10000

    context = {
        'products': paged_products,
        'categories': categories,
        'brands': brands,
        'banners': banners,
        'cats': cats,
        'colors': colors_in_category,
        'sizes': sizes_in_category,
        'color_filter': color_filter,
        'size_filter': size_filter,
        'price_min': price_min if price_min else min_price,
        'price_max': price_max if price_max else max_price,
        'min_price': min_price,
        'max_price': max_price,
    }

    return render(request, 'shop/shop-extended2.html', context)

from django.db.models import Min, Max
from django.core.paginator import Paginator

def products_by_category(request, Category_slug=None):
    cats = Category.objects.all()
    products = Product.objects.filter(is_availiable=True)
    brands = Brand.objects.all()
    colors = Color.objects.all()
    sizes = Size.objects.all()
    banners       = Banner.objects.all().filter(availiable=True)

    categories = None
    if Category_slug:
        categories = get_object_or_404(Category, slug=Category_slug)
        products = products.filter(category=categories)

    color_filter = request.GET.get('color')
    if color_filter:
        products = products.filter(variation__color__title=color_filter)

    size_filter = request.GET.get('size')
    if size_filter:
        products = products.filter(variation__size__title=size_filter)

    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')

    if price_min:
        products = products.filter(price__gte=price_min)
    if price_max:
        products = products.filter(price__lte=price_max)

    products = products.distinct()

    colors_in_category = Color.objects.filter(variation__product__in=products).distinct()
    sizes_in_category = Size.objects.filter(variation__product__in=products).distinct()

    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)

    # Annotate only paged products
    for product in paged_products:
        variations = product.variation_set.all()
        if variations.exists():
            product.min_discount = variations.aggregate(Min('discount_price'))['discount_price__min']
            product.max_discount = variations.aggregate(Max('discount_price'))['discount_price__max']
        else:
            product.min_discount = None
            product.max_discount = None

    min_price = products.aggregate(Min('price'))['price__min'] or 0
    max_price = products.aggregate(Max('price'))['price__max'] or 10000

    context = {
        'products': paged_products,
        'categories': categories,
        'banners': banners,
        'brands': brands,
        'cats': cats,
        'colors': colors_in_category,
        'sizes': sizes_in_category,
        'color_filter': color_filter,
        'size_filter': size_filter,
        'price_min': price_min if price_min else min_price,
        'price_max': price_max if price_max else max_price,
        'min_price': min_price,
        'max_price': max_price,
    }

    return render(request, 'shop/shop-extended.html', context)





from django.db.models import Min, Max, Q
from django.core.paginator import Paginator




def products_on_sale(request):
    cats = Category.objects.all()
    brands = Brand.objects.all()
    banners = Banner.objects.filter(availiable=True)

    # ფასდაკლებაში მყოფი პროდუქტები
    # ან პროდუქტები რომლის category.promotion=True
    products = Product.objects.filter(
        Q(is_on_sale=True) | Q(category__promotion=True),
        is_availiable=True
    ).select_related(
        'category',
        'brands',
        'subcategory'
    ).distinct()

    # ფერის ფილტრი
    color_filter = request.GET.get('color')
    if color_filter:
        products = products.filter(
            variation__color__title=color_filter
        )

    # ზომის ფილტრი
    size_filter = request.GET.get('size')
    if size_filter:
        products = products.filter(
            variation__size__title=size_filter
        )

    # ფასის ფილტრი
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')

    if price_min:
        products = products.filter(price__gte=price_min)

    if price_max:
        products = products.filter(price__lte=price_max)

    products = products.distinct()

    # მხოლოდ იმ ფერების გამოტანა რაც ამ პროდუქტებში არსებობს
    colors_in_category = Color.objects.filter(
        variation__product__in=products
    ).distinct()

    # მხოლოდ იმ ზომების გამოტანა რაც ამ პროდუქტებში არსებობს
    sizes_in_category = Size.objects.filter(
        variation__product__in=products
    ).distinct()

    # pagination
    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)

    # discount range თითოეულ პროდუქტზე
    for product in paged_products:
        variations = product.variation_set.all()

        if variations.exists():
            product.min_discount = variations.aggregate(
                Min('discount_price')
            )['discount_price__min']

            product.max_discount = variations.aggregate(
                Max('discount_price')
            )['discount_price__max']
        else:
            product.min_discount = None
            product.max_discount = None

    # slider min/max price
    min_price = products.aggregate(
        Min('price')
    )['price__min'] or 0

    max_price = products.aggregate(
        Max('price')
    )['price__max'] or 10000

    context = {
        'products': paged_products,
        'brands': brands,
        'banners': banners,
        'cats': cats,

        'colors': colors_in_category,
        'sizes': sizes_in_category,

        'color_filter': color_filter,
        'size_filter': size_filter,

        'price_min': price_min if price_min else min_price,
        'price_max': price_max if price_max else max_price,

        'min_price': min_price,
        'max_price': max_price,
    }

    return render(
        request,
        'shop/shop-extended.html',
        context
    )
    
    
    
def products_on_sale_shop(request):
    cats = Category.objects.all()
    brands = Brand.objects.all()
    banners = Banner.objects.filter(availiable=True)

    # ფასდაკლებაში მყოფი პროდუქტები
    # ან promotion category-ში არსებული პროდუქტები
    products = Product.objects.filter(
        Q(is_on_sale=True) | Q(category__promotion=True),
        is_availiable=True
    ).select_related(
        'category',
        'brands',
        'subcategory'
    ).distinct()

    # ფერით ფილტრი
    color_filter = request.GET.get('color')
    if color_filter:
        products = products.filter(
            variation__color__title=color_filter
        )

    # ზომით ფილტრი
    size_filter = request.GET.get('size')
    if size_filter:
        products = products.filter(
            variation__size__title=size_filter
        )

    # ფასის დიაპაზონი
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')

    if price_min:
        products = products.filter(price__gte=price_min)

    if price_max:
        products = products.filter(price__lte=price_max)

    products = products.distinct()

    # აქტიური ფერები
    colors_in_category = Color.objects.filter(
        variation__product__in=products
    ).distinct()

    # აქტიური ზომები
    sizes_in_category = Size.objects.filter(
        variation__product__in=products
    ).distinct()

    # pagination
    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)

    # discount min/max თითოეულ პროდუქტზე
    for product in paged_products:
        variations = product.variation_set.all()

        if variations.exists():
            product.min_discount = variations.aggregate(
                Min('discount_price')
            )['discount_price__min']

            product.max_discount = variations.aggregate(
                Max('discount_price')
            )['discount_price__max']
        else:
            product.min_discount = None
            product.max_discount = None

    # საერთო min/max price
    min_price = products.aggregate(
        Min('price')
    )['price__min'] or 0

    max_price = products.aggregate(
        Max('price')
    )['price__max'] or 10000

    context = {
        'products': paged_products,
        'brands': brands,
        'cats': cats,
        'colors': colors_in_category,
        'sizes': sizes_in_category,
        'banners': banners,

        'color_filter': color_filter,
        'size_filter': size_filter,

        'price_min': price_min if price_min else min_price,
        'price_max': price_max if price_max else max_price,

        'min_price': min_price,
        'max_price': max_price,
    }

    return render(
        request,
        'shop/shop-extended2.html',
        context
    )
    

def search(request, Category_id=None):
    # Fetch all available categories, colors, sizes, and brands
    cats = Category.objects.all()
    brands = Brand.objects.all()
    colors = Color.objects.all()
    sizes = Size.objects.all()

    # Start with all products
    products = Product.objects.all()

    # Fetch the selected category if Category_id is provided
    if Category_id:
        categories = get_object_or_404(Category, id=Category_id)
        products = products.filter(category=categories)  # Filter by category
    else:
        categories = None

    # Apply keyword search if available
    keyword = request.GET.get('keyword', None)
    if keyword:
        products = products.filter(
            Q(Serial_numb__icontains=keyword) |
            Q(Product_name_en__icontains=keyword) |
            Q(Product_name_ka__icontains=keyword) |
            Q(SKU__icontains=keyword)
        )

    # Apply color filter if available
    color_filter = request.GET.get('color', None)
    if color_filter:
        products = products.filter(variation__color__title=color_filter)

    # Apply size filter if available
    size_filter = request.GET.get('size', None)
    if size_filter:
        products = products.filter(variation__size__title=size_filter)

    # Apply price filter if available
    price_min = request.GET.get('price_min', None)
    price_max = request.GET.get('price_max', None)
    if price_min:
        products = products.filter(price__gte=price_min)  # Filter by min price
    if price_max:
        products = products.filter(price__lte=price_max)  # Filter by max price

    # Remove duplicates from products queryset
    products = products.distinct()

    # Get min and max price for price range slider
    min_price = products.aggregate(Min('price'))['price__min'] or 0
    max_price = products.aggregate(Max('price'))['price__max'] or 10000

    # Now fetch only the colors and sizes related to the filtered products
    colors_in_category = Color.objects.filter(variation__product__in=products).distinct()
    sizes_in_category = Size.objects.filter(variation__product__in=products).distinct()

    # Pagination for products (12 products per page)
    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)

    # Calculate the total product count (after filters)
    product_count = products.count()

    # Prepare context for rendering the template
    context = {
        'products': paged_products,
        'product_count': product_count,
        'categories': categories,  # Selected category (or None)
        'cats': cats,              # All categories
        'brands': brands,          # All brands
        'colors': colors_in_category,  # Only colors for the filtered products
        'sizes': sizes_in_category,    # Only sizes for the filtered products
        'color_filter': color_filter,
        'size_filter': size_filter,
        'price_min': price_min if price_min else min_price,
        'price_max': price_max if price_max else max_price,
        'min_price': min_price,
        'max_price': max_price,
        'keyword': keyword,  # Include the keyword for search context
    }

    return render(request, 'shop/shop-extended2.html', context)
    
    
# def store_subcategory(request, subcategory_slug=None):
#         subcategories = None
#         products = None
#         brands = Brand.objects.all()

#         if subcategory_slug != None:
#             subcategories = get_object_or_404(subcategory, slug=subcategory_slug)
#             products = Product.objects.filter(subcategory=subcategories, is_availiable=True).order_by('-created_date')
#             paginator = Paginator(products,2)
#             page = request.GET.get('page')
#             paged_products = paginator.get_page(page)
#             product_count = products.count()
#         else:
#             products = Product.objects.all().filter(is_availiable=True).order_by('-created_date')
#             paginator = Paginator(products, 2)
#             page = request.GET.get('page')
#             paged_products = paginator.get_page(page)
#             product_count = products.count()
#         context = {
#           'products': paged_products,
#           'product_count': product_count,
#           'brands' :  brands,
#         }
#         return render(request, 'shop/shop-extended.html', context)


from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Min, Max
from django.http import JsonResponse
from .models import Product, Brand, subcategory, Color, Size
from django.db.models.functions import Lower



def search_products_by_keyword(queryset, keyword):
    if not keyword:
        return queryset

    keyword_lower = keyword.lower()

    return queryset.annotate(
        test_lower=Lower('test'),
        product_name_lower=Lower('Product_name'),
        product_name_en_lower=Lower('Product_name_en'),
        product_name_ka_lower=Lower('Product_name_ka'),
    ).filter(
        Q(test_lower__icontains=keyword_lower) |
        Q(product_name_lower__icontains=keyword_lower) |
        Q(product_name_en_lower__icontains=keyword_lower) |
        Q(product_name_ka_lower__icontains=keyword_lower)
    ).order_by('-created_date')


def store_subcategory(request, subcategory_slug=None):
    subcategories = None
    products = Product.objects.filter(is_availiable=True).order_by('-created_date')
    brands = Brand.objects.all()
    colors = Color.objects.all()
    sizes = Size.objects.all()

    if subcategory_slug is not None:
        subcategories = get_object_or_404(subcategory, slug=subcategory_slug)
        products = products.filter(subcategory=subcategories)

    # Filters
    color_filter = request.GET.get('color')
    size_filter = request.GET.get('size')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    keyword = request.GET.get('keyword')

    if color_filter:
        products = products.filter(variation__color__title=color_filter)
    if size_filter:
        products = products.filter(variation__size__title=size_filter)
    if price_min:
        products = products.filter(price__gte=price_min)
    if price_max:
        products = products.filter(price__lte=price_max)

    # ✅ Apply shared search logic here:
    products = search_products_by_keyword(products, keyword)
    products = products.distinct()

    # Colors and Sizes available for filtered products
    colors_in_category = Color.objects.filter(variation__product__in=products).distinct()
    sizes_in_category = Size.objects.filter(variation__product__in=products).distinct()

    # Price range calculation
    min_price = products.aggregate(Min('price'))['price__min'] or 0
    max_price = products.aggregate(Max('price'))['price__max'] or 10000

    # Pagination for non-AJAX requests
    paginator = Paginator(products, 2)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)
    product_count = products.count()

    # Discount calculation
    for product in paged_products:
        variations = product.variation_set.all()
        if variations.exists():
            product.min_discount = variations.aggregate(Min('discount_price'))['discount_price__min']
            product.max_discount = variations.aggregate(Max('discount_price'))['discount_price__max']
        else:
            product.min_discount = None
            product.max_discount = None

    # ✅ AJAX live search response:
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        product_data = []
        for product in products:
            product_data.append({
                'id': product.id,
                'name': product.Product_name,
                'url': product.get_url(),
                'image': product.images.url,
                'price': product.price_display,
                'is_on_sale': product.is_on_sale,
                'min_discount': product.min_discount,
                'max_discount': product.max_discount,
            })
        return JsonResponse({'products': product_data})

    # Normal page render
    context = {
        'products': paged_products,
        'product_count': product_count,
        'brands': brands,
        'colors': colors_in_category,
        'sizes': sizes_in_category,
        'color_filter': color_filter,
        'size_filter': size_filter,
        'price_min': price_min if price_min else min_price,
        'price_max': price_max if price_max else max_price,
        'min_price': min_price,
        'max_price': max_price,
        'keyword': keyword,
    }
    return render(request, 'shop/shop-extended2.html', context)



def get_variation_details(request):
    product_id = request.GET.get('product_id')
    color_id = request.GET.get('color_id')
    size_id = request.GET.get('size_id')

    print(f"Received AJAX request: Product ID: {product_id}, Color ID: {color_id}, Size ID: {size_id}")

    try:
        variation = Variation.objects.get(
            product_id=product_id,
            color_id=color_id,
            size_id=size_id
        )

        print(f"Variation found: Price: {variation.price}, Image: {variation.image.url if variation.image else 'No Image'}")

        return JsonResponse({
            'image_url': variation.image.url if variation.image else '',
            'price': variation.price,
        })
    except Variation.DoesNotExist:
        print("Variation not found")
        return JsonResponse({'error': 'Variation not found'}, status=404)