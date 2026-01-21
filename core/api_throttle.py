from rest_framework.throttling import SimpleRateThrottle, UserRateThrottle


class DefaultThrottle(UserRateThrottle):
    rate = "30/min"  # this is for now only


class EndpointThrottle(SimpleRateThrottle):
    rate = "15/min"

    def get_cache_key(self, request, view):
        ident = request.user.pk
        endpoint = view.__class__.__name__

        return f"throttle_{endpoint}_{ident}"  # per endpoint per identity
