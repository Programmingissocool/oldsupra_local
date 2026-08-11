from django.conf import settings
from django.http import HttpResponsePermanentRedirect


class ForceCanonicalDomainAndLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host()
        path = request.path

        canonical_host = getattr(settings, 'CANONICAL_HOST', 'oldsupra.ge')
        exempt_hosts = tuple(getattr(settings, 'CANONICAL_HOST_EXEMPT', ()))

        excluded_prefixes = (
            '/ka/',
            '/en/',
            '/admin/',
            '/static/',
            '/media/',
        )

        # Hosts served directly (the raw IP before DNS cutover): keep the
        # language-prefix behaviour but stay on the requested host and scheme.
        if host.split(':')[0] in exempt_hosts:
            if not path.startswith(excluded_prefixes):
                return HttpResponsePermanentRedirect(
                    f'{request.scheme}://{host}/ka{path}'
                )
            return self.get_response(request)

        scheme = 'https'

        if host.startswith('www.'):
            new_host = host.replace('www.', '', 1)
            return HttpResponsePermanentRedirect(
                f'{scheme}://{new_host}{path}'
            )

        if host != canonical_host:
            return HttpResponsePermanentRedirect(
                f'{scheme}://{canonical_host}{path}'
            )

        if not path.startswith(excluded_prefixes):
            return HttpResponsePermanentRedirect(
                f'{scheme}://{canonical_host}/ka{path}'
            )

        return self.get_response(request)
