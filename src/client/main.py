# mylib/client.py

import requests


class JokeClientError(RuntimeError):
    """Base exception for all JokeClient errors."""
    pass


class AuthenticationError(JokeClientError):
    """401 Unauthorized"""
    pass


class InvalidTokenError(AuthenticationError):
    """403 Forbidden"""
    pass


class TokenExpiredError(AuthenticationError):
    """403 Forbidden (expired token)"""
    pass


class TokenGoneError(AuthenticationError):
    """410 Gone"""
    pass


class ResourceNotFoundError(JokeClientError):
    """404 Not Found"""
    pass


class BackendError(JokeClientError):
    """502 Bad Gateway"""
    pass


class BackendNotRunningError(BackendError):
    """503 Service Unavailable"""
    pass


class BackendTimeoutError(BackendError):
    """504 Gateway Timeout"""
    pass


class InternalServerError(JokeClientError):
    """500 Internal Server Error"""
    pass


class JokeClient:

    def __init__(
        self,
        host="127.0.0.1",
        port=8080,
        token=None,
        use_https=False,
        timeout=10
    ):
        self.host = host
        self.port = port
        self.token = token
        self.timeout = timeout
        self.use_https = use_https

    @property
    def base_url(self):
        protocol = "https" if self.use_https else "http"
        return f"{protocol}://{self.host}:{self.port}"

    @property
    def headers(self):

        headers = {}

        if self.token is not None:
            headers["Authorization"] = f"Bearer {self.token}"

        return headers

    def _request(self, method, endpoint, **kwargs):

        response = requests.request(
            method,
            self.base_url + endpoint,
            headers=self.headers,
            timeout=self.timeout,
            **kwargs
        )

        try:
            data = response.json()
        except Exception:
            data = {
                "message": response.text
            }

        if response.status_code == 200:
            return data

        if response.status_code == 401:
            raise AuthenticationError(
                data.get("message", "Authentication required.")
            )

        if response.status_code == 403:

            message = data.get("message", "")

            if "expired" in message.lower():
                raise TokenExpiredError(message)

            raise InvalidTokenError(message)

        if response.status_code == 404:
            raise ResourceNotFoundError(
                data.get("message", "Not found.")
            )

        if response.status_code == 410:
            raise TokenGoneError(
                data.get("message", "Gone.")
            )

        if response.status_code == 500:
            raise InternalServerError(
                data.get("message", "Internal server error.")
            )

        if response.status_code == 502:
            raise BackendError(
                data.get("message", "Backend error.")
            )

        if response.status_code == 503:
            raise BackendNotRunningError(
                data.get("message", "Backend unavailable.")
            )

        if response.status_code == 504:
            raise BackendTimeoutError(
                data.get("message", "Backend timeout.")
            )

        raise JokeClientError(
            f"Unexpected HTTP {response.status_code}: "
            f"{data.get('message', '')}"
        )

    # ===========================
    # Public API
    # ===========================

    def getjoke(self):
        """
        Returns the joke exactly as sent by the server.
        """
        data = self._request("GET", "/joke")
        return data["joke"]

    # ===========================
    # Convenience methods
    # ===========================

    def set_token(self, token):
        self.token = token

    def clear_token(self):
        self.token = None

    def set_host(self, host):
        self.host = host

    def set_port(self, port):
        self.port = port

    def set_timeout(self, timeout):
        self.timeout = timeout

    def use_ssl(self, enabled=True):
        self.use_https = enabled