import unittest
from unittest.mock import patch, Mock

from src.client.main import (
    JokeClient,
    JokeClientError,
    AuthenticationError,
    InvalidTokenError,
    TokenExpiredError,
    TokenGoneError,
    ResourceNotFoundError,
    BackendError,
    BackendNotRunningError,
    BackendTimeoutError,
    InternalServerError,
)


class TestJokeClient(unittest.TestCase):

    def test_base_url_http(self):
        client = JokeClient("example.com", 9000)

        self.assertEqual(
            client.base_url,
            "http://example.com:9000"
        )

    def test_base_url_https(self):
        client = JokeClient(
            "example.com",
            443,
            use_https=True
        )

        self.assertEqual(
            client.base_url,
            "https://example.com:443"
        )

    def test_headers_without_token(self):
        client = JokeClient()

        self.assertEqual(
            client.headers,
            {}
        )

    def test_headers_with_token(self):
        client = JokeClient(token="abc123")

        self.assertEqual(
            client.headers,
            {
                "Authorization": "Bearer abc123"
            }
        )

    def test_getjoke_success(self):
        client = JokeClient()

        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "joke": "Why did the chicken cross the road?"
        }

        with patch(
            "src.client.main.requests.request",
            return_value=response
        ):
            joke = client.getjoke()

        self.assertEqual(
            joke,
            "Why did the chicken cross the road?"
        )


    def test_invalid_token(self):
        self.assert_http_exception(
            403,
            {"message": "Invalid token"},
            InvalidTokenError
        )


    def test_expired_token(self):
        self.assert_http_exception(
            403,
            {"message": "Token expired"},
            TokenExpiredError
        )


    def test_authentication_error(self):
        self.assert_http_exception(
            401,
            {"message": "Missing token"},
            AuthenticationError
        )


    def test_not_found(self):
        self.assert_http_exception(
            404,
            {"message": "Not found"},
            ResourceNotFoundError
        )


    def test_token_gone(self):
        self.assert_http_exception(
            410,
            {"message": "Token revoked"},
            TokenGoneError
        )


    def test_internal_server_error(self):
        self.assert_http_exception(
            500,
            {"message": "Crash"},
            InternalServerError
        )


    def test_backend_error(self):
        self.assert_http_exception(
            502,
            {"message": "Backend failed"},
            BackendError
        )


    def test_backend_not_running(self):
        self.assert_http_exception(
            503,
            {"message": "Server offline"},
            BackendNotRunningError
        )


    def test_backend_timeout(self):
        self.assert_http_exception(
            504,
            {"message": "Timeout"},
            BackendTimeoutError
        )


    def test_unexpected_status(self):
        client = JokeClient()

        response = Mock()
        response.status_code = 418
        response.json.return_value = {
            "message": "I'm a teapot"
        }

        with patch(
            "src.client.main.requests.request",
            return_value=response
        ):
            with self.assertRaises(JokeClientError):
                client.getjoke()


    def test_json_failure_uses_text(self):
        client = JokeClient()

        response = Mock()
        response.status_code = 200
        response.json.side_effect = Exception()
        response.text = '{"joke":"fallback"}'

        with patch(
            "src.client.main.requests.request",
            return_value=response
        ):
            result = client._request("GET", "/joke")

        self.assertEqual(
            result,
            {
                "message": '{"joke":"fallback"}'
            }
        )


    def test_setters(self):
        client = JokeClient()

        client.set_token("token")
        client.set_host("localhost")
        client.set_port(1234)
        client.set_timeout(5)
        client.use_ssl(True)

        self.assertEqual(client.token, "token")
        self.assertEqual(client.host, "localhost")
        self.assertEqual(client.port, 1234)
        self.assertEqual(client.timeout, 5)
        self.assertTrue(client.use_https)


    def assert_http_exception(
        self,
        status_code,
        json_data,
        exception
    ):
        client = JokeClient()

        response = Mock()
        response.status_code = status_code
        response.json.return_value = json_data

        with patch(
            "src.client.main.requests.request",
            return_value=response
        ):
            with self.assertRaises(exception):
                client.getjoke()


if __name__ == "__main__":
    unittest.main()