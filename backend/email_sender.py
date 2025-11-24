"""
Custom emails sent for Authentication and other purposes
"""
from django.core.mail.backends.smtp import EmailBackend
import os

class GmailSMTPBackend(EmailBackend):
    def __init__(self, **kwargs):
        # override username/password with env vars
        kwargs['username'] = os.getenv('GMAIL_APP_USER')
        kwargs['password'] = os.getenv('GMAIL_APP_PASSWORD')
        if not username or not password:
            raise ValueError('gmail credentials must be set!')
        kwargs['host'] = 'smtp.gmail.com'
        kwargs['port'] = 587
        kwargs['use_tls'] = True
        kwargs['fail_silently'] = False

        super().__init__(**kwargs)
