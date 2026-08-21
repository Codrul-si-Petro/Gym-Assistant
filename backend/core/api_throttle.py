from django.conf import settings
from rest_framework.throttling import SimpleRateThrottle, UserRateThrottle

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
