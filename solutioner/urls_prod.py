"""Root URLconf for this deployment.

Wraps the mirrored solutioner/urls.py and prepends robots.txt + sitemap.xml at
the DOMAIN ROOT. This must sit outside i18n_patterns: the upstream config wraps
everything in i18n_patterns, so /robots.txt 301-redirects to /ka/robots.txt, and
crawlers only ever read the unprefixed path.

Selected via ROOT_URLCONF in settings_prod.py so that re-syncing urls.py from
the old host does not clobber it.
"""
from django.contrib.sitemaps.views import sitemap
from django.urls import path
from django.views.generic import TemplateView

from .sitemaps import SITEMAPS
from .urls import urlpatterns as _upstream_urlpatterns

# Upstream urls.py registers the Django admin TWICE: once plainly and once
# inside i18n_patterns, so it answered at /admin/, /ka/admin/ AND /en/admin/.
# Three public login surfaces is three things to brute-force and defeats any
# edge rule written against /admin/ alone. Keep the canonical /admin/ only.
def _drop_prefixed_admin(patterns):
    kept = []
    for p in patterns:
        prefix = str(getattr(p, "pattern", ""))
        nested = getattr(p, "url_patterns", None)
        if nested is not None and prefix in ("ka/", "en/"):
            p.url_patterns[:] = [
                q for q in nested if not str(getattr(q, "pattern", "")).startswith("admin/")
            ]
        kept.append(p)
    return kept


_upstream_urlpatterns = _drop_prefixed_admin(_upstream_urlpatterns)

urlpatterns = [
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
        name="robots_txt",
    ),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": SITEMAPS},
        name="django.contrib.sitemaps.views.sitemap",
    ),
] + _upstream_urlpatterns
