from rest_framework.throttling import UserRateThrottle


class DefaultPostThrottle(UserRateThrottle):
    rate = '15/min'  # this is for now only
