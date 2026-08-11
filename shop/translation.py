from .models import Product, Category,subcategory,Brand,Banner,Color, Page, About_Us, Fabric, Site_Content
from modeltranslation.translator import TranslationOptions,register

@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ('Product_name','Meta_title','test','short','material')


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('category_name','description','Meta_title','text_block')
    
    
@register(subcategory)
class subcategoryTranslationOptions(TranslationOptions):
    fields = ('subcategory_name',)  
    
    
@register(Brand)
class BrandTranslationOptions(TranslationOptions):
    fields = ('Brand_name','description')    
    
@register(Banner)
class BannerTranslationOptions(TranslationOptions):
    fields = ('Banner_name','description')     
    
    
@register(Color)
class ColorTranslationOptions(TranslationOptions):
    fields = ('title',) 
    
@register(Fabric)
class FabricTranslationOptions(TranslationOptions):
    fields = ('title',) 
        
    
@register(Page)
class PageTranslationOptions(TranslationOptions):
    fields = ('page_name','description')   
    
    
@register(About_Us)
class About_UsTranslationOptions(TranslationOptions):
    fields = ('name','title','description')       
    

@register(Site_Content)
class ProductTranslationOptions(TranslationOptions):
    fields = ('MainButton','Language','Cart','Address','callus', 'register', 'lang', 'stock','contact_us','addresstext','socialtext','emailtext','tools','user','first_name','last_name','email_address','user_phone','profile','save_changes','my_orders','edit_profile','colors','sizes','filters','reset_filters','price','search','pages')