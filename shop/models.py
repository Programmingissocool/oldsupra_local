from django.db import models
from ckeditor.fields import RichTextField
from django.urls import reverse
from django_quill.fields import QuillField
from taggit.managers import TaggableManager
from adminsortable.models import SortableMixin
from django.utils.html import mark_safe
# from adminsortable.models import SortableMixin

# Create your models here.


class Page(models.Model):
    page_name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = RichTextField()
    images = models.ImageField(upload_to='photos/pages', blank=True)
    my_order = models.PositiveIntegerField(
        default=0,
        blank=False,
        null=False,
    )
   

    class Meta:
        verbose_name = 'Page'
        verbose_name_plural = 'Pages'
        ordering = ['my_order']

    def get_url(self):
            return reverse('pages', args=[self.slug])
    def __str__(self):
        return self.page_name


class About_Us(models.Model):
    name = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=50, blank=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = RichTextField()
    images = models.ImageField(upload_to='photos/about', blank=True)
    my_order = models.PositiveIntegerField(
        default=0,
        blank=False,
        null=False,
    )
   

    class Meta:
        verbose_name = 'About Us'
        verbose_name_plural = 'About Us'
        ordering = ['my_order']

    def get_url(self):
            return reverse('about', args=[self.slug])
    def __str__(self):
        return self.name

class About_UsGallery(models.Model):
    title = models.ForeignKey(About_Us, default=None, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='store/aboutus', max_length=255)

    def __str__(self):
        return self.title.name

    class Meta:
        verbose_name = 'aboutusgallery'
        verbose_name_plural = 'about gallery'



class Brand(models.Model):
    Brand_name     = models.CharField(max_length=50, unique=True)
    slug           = models.SlugField(max_length=50, unique=True)
    url            = models.CharField(max_length=50, unique=True)
    description    = RichTextField()
    images         = models.ImageField(upload_to='photos/Brands')
    availiable     = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'brand'
        verbose_name_plural = 'Brands'

    # def get_url(self):
    #             return reverse('products_by_Brand_name', args=[self.slug])

    def __str__(self):
        return str(self.Brand_name)

    def get_url(self):
        return reverse('Brand', args=[self.slug])

class Category(models.Model):
    category_name = models.CharField(max_length=50, unique=True)
    Meta_title = models.CharField(max_length=150, blank=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(max_length=500, blank=True)
    text_block = models.TextField(max_length=10500, blank=True)
    cat_image = models.ImageField(upload_to='photos/categories', blank=True)
    modified_date  = models.DateTimeField(auto_now=True)
    order =         models.IntegerField(default=50)
    promotion = models.BooleanField(default=False)
    
    my_order = models.PositiveIntegerField(
        default=0,
        blank=False,
        null=False,
    )

    

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'
        ordering = ['my_order']
        
      
    
    def __unicode__(self):
        return self.category_name   
    
    def get_url_cat(self):
        return reverse('products_category', args=[self.slug])
    
    def get_url(self):
            return reverse('products_by_category', args=[self.slug])
    def __str__(self):
        return self.category_name

    
class subcategory(models.Model):
    subcategory_name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=100,unique=True)
    maincategory = models.ForeignKey(Category, on_delete=models.CASCADE)
    maincategory_name = models.CharField(max_length=50)
    is_availiable = models.BooleanField(default=True)
    my_order = models.PositiveIntegerField(
        default=0,
        blank=False,
        null=False,
    )


    class Meta:
        verbose_name = 'subcategory_name'
        verbose_name_plural = 'subcategories'
        ordering = ['my_order']
        
        
    def __unicode__(self):
            return self.subcategory_name     
        
    def get_url(self):
            return reverse('products_by_subcategory', args=[self.slug])
    def __str__(self):
            return self.subcategory_name


class Color(models.Model):
    title=models.CharField(max_length=100,blank=True)
    color_code=models.CharField(max_length=100,blank=True)

    class Meta:
        verbose_name_plural='4. Colors'

    def color_bg(self):
        return mark_safe('<div style="width:30px; height:30px; background-color:%s"></div>' % (self.color_code))

    def __str__(self):
        return self.title

# Size
class Size(models.Model):
    title=models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name_plural='5. Sizes'

    def __str__(self):
        return self.title
        
        
class Fabric(models.Model):
    title=models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name_plural='6. ქსოვილი'

    def __str__(self):
        return self.title
        





from django.db.models import Min, Max

class Product(models.Model):
    Product_name   = models.CharField(verbose_name="Product name",max_length=50, unique=True)
    Meta_title     = models.CharField(verbose_name="Meta name",max_length=50, blank=True)
    slug           = models.SlugField(max_length=50, unique=True)
    short          = RichTextField(verbose_name="Short Description", blank=True)
    test           = RichTextField(verbose_name="Full Description")
    material       = RichTextField(verbose_name="Full Description", blank=True)
    SKU            = models.CharField(max_length=50)
    Serial_numb    = models.CharField(max_length=50)
    price          = models.FloatField(default=0)
    discount_price = models.FloatField(default=0)
    images         = models.ImageField(upload_to='photos/Products')
    datasheet      = models.FileField(upload_to='photos/Datasheets', blank=True)
    related        = models.ManyToManyField("self", blank=True)
    stock          = models.IntegerField(default=50)
    is_availiable  = models.BooleanField(default=True)
    is_new         = models.BooleanField(default=True)
    is_on_sale     = models.BooleanField(default=True)
    # fabric         = models.ForeignKey(Fabric, on_delete=models.CASCADE, blank=True, null=True)
    category       = models.ForeignKey(Category, on_delete=models.CASCADE)
    brands         = models.ForeignKey(Brand, on_delete=models.CASCADE)
    subcategory    = models.ForeignKey(subcategory, on_delete=models.CASCADE, blank=True)
    created_date   = models.DateTimeField(auto_now_add=True)
    modified_date  = models.DateTimeField(auto_now=True)
    tags = TaggableManager()
    my_order = models.PositiveIntegerField(
        default=0,
        blank=False,
        null=False,
    )
    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['my_order']
        
    def __str__(self):
         return self.Product_name      

    def get_url(self):
        return reverse('Product_detail', args=[self.slug])

    def difference(self):
        return round((self.price or 0) - (self.discount_price or 0), 1)

    def get_price(self):
        return self.discount_price if self.is_on_sale else self.price

    def price_display(self):
        variations = self.variation_set.all()
        if variations.exists():
            min_price = variations.aggregate(Min('price'))['price__min']
            max_price = variations.aggregate(Max('price'))['price__max']
            if min_price == max_price:
                return f"{min_price} ₾"
            return f"{min_price} ₾ - {max_price} ₾"
        return f"{self.get_price()} ₾"

    def get_min_discount(self):
        return self.variation_set.aggregate(Min('discount_price'))['discount_price__min']

    def get_max_discount(self):
        return self.variation_set.aggregate(Max('discount_price'))['discount_price__max']

    def discount_range_display(self):
        min_discount = self.get_min_discount()
        max_discount = self.get_max_discount()
        if min_discount and max_discount:
            if min_discount == max_discount:
                return f"{min_discount} ₾"
            return f"{min_discount} ₾ - {max_discount} ₾"
        return None

    def is_discounted(self):
        if self.is_on_sale:
            if self.discount_price and self.discount_price < self.price:
                return True
            if self.get_min_discount():
                return True
        return False
            
            
            
            
            

class Site_Content(models.Model):
    name            = models.CharField(max_length=200, unique=True)
    MainButton      = models.CharField(max_length=200, blank=True)
    logo            = models.ImageField(upload_to='photos/SiteContent')
    PriceList       = models.FileField(upload_to='photos/SiteContent', blank=True)
    register            = models.CharField(max_length=200,blank=True, unique=True)
    lang              = models.CharField(max_length=200, blank=True)
    stock           = models.CharField(max_length=200, blank=True)    
    Address         = models.CharField(max_length=200, blank=True)
    VAT             = models.CharField(max_length=200, blank=True)
    Language        = models.CharField(max_length=200, blank=True)
    Cart            = models.CharField(max_length=200, blank=True)
    callus          = models.CharField(max_length=200, blank=True)    
    fb_link         = models.CharField(max_length=200, blank=True)
    insta_link      = models.CharField(max_length=200, blank=True)
    youtube_link    = models.CharField(max_length=200, blank=True)
    phone_number    = models.CharField(max_length=200, blank=True)
    email           = models.CharField(max_length=200, blank=True)
    phone           = models.CharField(max_length=200, blank=True)  
    contact_us       = models.CharField(max_length=200, blank=True)
    addresstext      = models.CharField(max_length=200, blank=True)
    socialtext       = models.CharField(max_length=200, blank=True)
    emailtext        = models.CharField(max_length=200, blank=True)
    tools            = models.CharField(max_length=200, blank=True)
    user             = models.CharField(max_length=200, blank=True) 
    first_name       = models.CharField(max_length=200, blank=True) 
    last_name        = models.CharField(max_length=200, blank=True)
    email_address    = models.CharField(max_length=200, blank=True)
    user_phone      = models.CharField(max_length=200, blank=True) 
    profile          = models.CharField(max_length=200, blank=True)
    save_changes     = models.CharField(max_length=200, blank=True) 
    my_orders          = models.CharField(max_length=200, blank=True)
    colors          = models.CharField(max_length=200, blank=True)
    sizes          = models.CharField(max_length=200, blank=True)
    filters          = models.CharField(max_length=200, blank=True)
    reset_filters          = models.CharField(max_length=200, blank=True)
    price          = models.CharField(max_length=200, blank=True)
    edit_profile        = models.CharField(max_length=200, blank=True) 
    search  = models.CharField(max_length=200, blank=True) 
    pages  = models.CharField(max_length=200, blank=True) 
    sale_countdown_enabled = models.BooleanField(default=True)
    sale_countdown_ends_at = models.DateTimeField(blank=True, null=True)
    
   
    def __str__(self):
        return str(self.name)            
        
            
            
class SaleCountdown(Site_Content):
    class Meta:
        proxy = True
        verbose_name = 'Sale Countdown'
        verbose_name_plural = 'Sale Countdown'

    def __str__(self):
        return 'Sale Countdown'


class Variation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, blank=True)
    color = models.ForeignKey(Color, on_delete=models.CASCADE, null=True)
    size = models.ForeignKey(Size, on_delete=models.CASCADE, null=True)
    fabric = models.ForeignKey(Fabric, on_delete=models.CASCADE, null=True, blank=True)
    price = models.FloatField(default=0)
    discount_price = models.FloatField(default=0)  # NEW
    image = models.ImageField(upload_to="product_imgs/", null=True)

    class Meta:
        verbose_name_plural = 'Variations'

    def __str__(self):
         return f"{self.product.Product_name} - {self.color} - {self.size}"

    def image_tag(self):
        return mark_safe(f'<img src="{self.image.url}" width="50" height="50" />')

    @property
    def get_price(self):
        if self.product.is_on_sale and self.discount_price:
            return self.discount_price
        return self.price

class ProductGallery(models.Model):
    product = models.ForeignKey(Product, default=None, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='store/products', max_length=255)

    def __str__(self):
        return self.product.Product_name

    class Meta:
        verbose_name = 'productgallery'
        verbose_name_plural = 'product gallery'


class Banner(models.Model):
    Banner_name   = models.CharField(max_length=50, unique=True)
    slug           = models.SlugField(max_length=50, unique=True)
    description    = QuillField(max_length=25550000)
    images         = models.ImageField(upload_to='photos/Banners')
    availiable     = models.BooleanField(default=True)
    hamburger_menu  = models.BooleanField(default=True)
    created_date   = models.DateTimeField(auto_now_add=True)
    modified_date  = models.DateTimeField(auto_now=True)
    brands         = models.ForeignKey(Brand, on_delete=models.CASCADE)

    # def get_url(self):
    #     return reverse('products_by_Brand_name', args=[self.brands.slug])


    def __str__(self):
        return str(self.Banner_name)



