"""Sitemaps for oldsupra.ge.

Deployment-side addition: the upstream site has never had a sitemap or a
robots.txt (both 404 on the old host; its robots.txt is served by Cloudflare,
not the application, so it disappears the moment Cloudflare stops proxying).

Kept out of the mirrored app modules so re-syncing code from the old host does
not clobber it, matching the settings_prod.py convention.
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from shop.models import Product, Category, Page, About_Us


class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    protocol = "https"

    def items(self):
        return Product.objects.filter(is_availiable=True)

    def location(self, obj):
        return reverse("Product_detail", args=[obj.slug])

    def lastmod(self, obj):
        return getattr(obj, "modified_date", None)


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6
    protocol = "https"

    def items(self):
        return Category.objects.all()

    def location(self, obj):
        return reverse("products_category", args=[obj.slug])


class PageSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.4
    protocol = "https"

    def items(self):
        return Page.objects.all()

    def location(self, obj):
        return reverse("pages", args=[obj.slug])


class StaticSitemap(Sitemap):
    changefreq = "monthly"
    priority = 1.0
    protocol = "https"

    def items(self):
        return ["home", "store", "contact", "products_on_sale"]

    def location(self, item):
        return reverse(item)


SITEMAPS = {
    "static": StaticSitemap,
    "products": ProductSitemap,
    "categories": CategorySitemap,
    "pages": PageSitemap,
}
