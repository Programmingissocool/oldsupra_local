from . models import Product, subcategory, Category, Page, About_Us, Site_Content
from django.db.models import Prefetch
from .models import Product,Variation
from django.db.models import Min,Max




def defaultcontent(request):
    SiteInfo = Site_Content.objects.get(name="DEFAULT")
    return dict(SiteInfo=SiteInfo)

def About_Usall(request):
    About_Us_dict = About_Us.objects.all()
    return dict(About_Us_dict=About_Us_dict)
    
    
def page_all(request):
    page_links = Page.objects.all()
    return dict(page_links=page_links)    
    
def Product_all(request):
    product_links = Product.objects.all()
    return dict(product_links=product_links)
    



def menu_links_tv(request):
    tv_links = subcategory.objects.all().filter(maincategory_name="Fire_Alarm").filter(is_availiable=True)
    return dict(tv_links=tv_links)
    

def menu_links(request):
    categories = Category.objects.all()

    for category in categories:
        for subcat in category.subcategory_set.all():
            subcat.products = subcat.product_set.all()[:5]

    return {
        'categories': categories,
    }
    
    
    
def menu_links_catts(request):
    catts = Category.objects.all()

    for category in catts:
        for subcat in category.subcategory_set.all():
            subcat.products = subcat.product_set.all()[:5]

    return {
        'catts': catts,
    }
    
        

def get_filters(request):
	minMaxPrice=Variation.objects.aggregate(Min('price'),Max('price'))
	data={
		'minMaxPrice':minMaxPrice,
	}
	return data    