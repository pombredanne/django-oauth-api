from oauthlib import oauth2
from oauthlib.common import urlencode

from rest_framework.request import Request

from oauth_api.exceptions import OAuthAPIError, FatalClientError


class OAuthHandler(object):
    def __init__(self, server):
        self.server = server

    def extract_params(self, request):

        if isinstance(request, Request):
            data = request.DATA
            headers = request._request.META.copy()
            uri = request._request.build_absolute_uri()
        else:
            data = urlencode(request.POST.items())
            headers = request.META.copy()
            uri = request.build_absolute_uri()

        method = request.method
        if 'wsgi.input' in headers:
            del headers['wsgi.input']
        if 'wsgi.errors' in headers:
            del headers['wsgi.errors']
        return uri, method, data, headers

    def create_authorization_response(self, request, scopes, credentials, allow):
        if not allow:
            raise oauth2.AccessDeniedError()

        credentials['user'] = request.user

        uri, headers, body, status = self.server.create_authorization_response(
            uri=credentials['redirect_uri'], scopes=scopes, credentials=credentials)

        return uri, headers, body, status

    def create_token_response(self, request):
        uri, method, data, headers = self.extract_params(request)
        url, headers, body, status = self.server.create_token_response(uri, method, data, headers)
        return url, headers, body, status

    def validate_authorization_request(self, request):
        """
        Wrapper method to call `validate_authorization_request` in OAuthLib
        """
        try:
            uri, method, data, headers = self.extract_params(request)

            scopes, credentials = self.server.validate_authorization_request(
                uri, method, data, headers)

            return scopes, credentials
        except oauth2.FatalClientError as error:
            raise FatalClientError(error=error)
        except oauth2.OAuth2Error as error:
            raise OAuthAPIError(error=error)
