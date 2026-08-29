from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class ExtensionTokenAuthentication(BaseAuthentication):
    """Matches the Chrome extension's static bearer token against EXTENSION_API_TOKEN."""

    keyword = "Token"

    def authenticate(self, request):
        header = request.headers.get("Authorization", "")
        if not header.startswith(f"{self.keyword} "):
            return None

        token = header[len(self.keyword) + 1 :].strip()
        if not settings.EXTENSION_API_TOKEN or token != settings.EXTENSION_API_TOKEN:
            raise AuthenticationFailed("Invalid extension token.")

        return (None, token)
