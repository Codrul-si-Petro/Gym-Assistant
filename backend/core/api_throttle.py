from django.conf import settings
from rest_framework.throttling import SimpleRateThrottle, UserRateThrottle

# Production rates are intentionally tight. Local/dev and E2E runs (DJANGO_DEBUG=True,
# see .github/workflows/e2e-tests.yml) hammer the same test user across many pages in
# under a minute, which isn't representative of real traffic — relax the rate there so
# throttling doesn't cause flaky test failures instead of testing anything meaningful.
#
# NOTE: DRF's SimpleRateThrottle.__init__ only calls get_rate() when `rate` is unset on
# the instance. Setting a class-level `rate` therefore permanently locks in that value —
# we must assign `self.rate` in __init__ before super() so DEBUG can actually take effect.
DEBUG_RATE = "1000/min"
DEFAULT_PROD_RATE = "30/min"
ENDPOINT_PROD_RATE = "15/min"


class DefaultThrottle(UserRateThrottle):
    def __init__(self):
        self.rate = DEBUG_RATE if settings.DEBUG else DEFAULT_PROD_RATE
        super().__init__()


class EndpointThrottle(SimpleRateThrottle):
    def __init__(self):
        self.rate = DEBUG_RATE if settings.DEBUG else ENDPOINT_PROD_RATE
        super().__init__()

    def get_cache_key(self, request, view):
        ident = request.user.pk
        endpoint = view.__class__.__name__

        return f"throttle_{endpoint}_{ident}"  # per endpoint per identity
