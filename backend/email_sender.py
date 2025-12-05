"""
Custom emails sent for Authentication and other purposes
"""
from django.core.mail.backends.smtp import EmailBackend
import os

class GmailSMTPBackend(EmailBackend):
    def __init__(self, **kwargs):
        # get credentials from environment
        gmail_user = os.getenv('GMAIL_APP_USER')
        gmail_password = os.getenv('GMAIL_APP_PASSWORD')

        if not gmail_user or not gmail_password:
            raise ValueError('Email credentials must be set!')

        kwargs['username'] = gmail_user
        kwargs['password'] = gmail_password
        kwargs['host'] = 'smtp.gmail.com'
        kwargs['port'] = 587
        kwargs['use_tls'] = True
        kwargs['fail_silently'] = False

        super().__init__(**kwargs)
