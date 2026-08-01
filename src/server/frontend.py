from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import datetime

from jokeapi_interface import (
    JokeAPI,
    BackendError,
    BackendNotRunningError
)

TOKEN_REALFILE = "secrets/tokens.py"
def load_tokens_from_realfile():
    def load_tokens_from_file_using_import():
        import importlib.util
        spec = importlib.util.spec_from_file_location("tokens", TOKEN_REALFILE)
        tokens_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tokens_module)
        return tokens_module.tokens
    tokens = load_tokens_from_file_using_import()
    return tokens
def put_tokens_into_tempfile():
    with open("secrets/tokens.txt", "w") as file:
        tokens = load_tokens_from_realfile()
        for token, info in tokens.items():
            line = f"{token} {info['state']} {info['expiration']} {info['expired']} {info['reason']} {info['invalid_code']}\n"
            file.write(line)
TOKEN_FILE = "secrets/tokens.txt"


def load_tokens():
    """
Loads tokens.
"""
    tokens = {}

    try:
        with open(TOKEN_FILE, "r") as file:

            for line in file:

                if not line.strip():
                    continue

                parts = line.strip().split()

                if len(parts) != 6:
                    continue

                token = parts[0]

                tokens[token] = {
                    "state": parts[1],
                    "expiration": parts[2],
                    "expired": parts[3].lower() == "true",
                    "reason": parts[4],
                    "invalid_code": int(parts[5])
                }

    except FileNotFoundError:
        pass

    return tokens



def check_token(token):
    """
    Checks a token against the loaded tokens and returns a tuple of (is_valid, error_code, error_message).
"""

    tokens = load_tokens()

    if token not in tokens:
        return False, 401, "Authentication required"


    info = tokens[token]


    if info["state"].lower() != "valid":

        code = info["invalid_code"]

        if code == 410:
            return (
                False,
                410,
                "The requested resource is no longer available"
            )

        if code == 404:
            return (
                False,
                404,
                "Not found"
            )

        return (
            False,
            403,
            "Token invalid"
        )


    if info["expired"]:

        return (
            False,
            403,
            f"Token expired {info['expiration']}"
        )


    if info["expiration"] != "None":

        expiry = datetime.datetime.fromisoformat(
            info["expiration"]
        )

        if datetime.datetime.now() > expiry:

            return (
                False,
                403,
                f"Token expired {info['expiration']}"
            )


    return True, None, None



joke_api = JokeAPI([
    "Programming",
    "Misc",
    "Christmas",
    "Spooky",
    "Pun"
])



class JokeRequestHandler(BaseHTTPRequestHandler):
    """
The base handler for the requests
"""

    def send_json(self, status, data):

        response = json.dumps(
            data,
            indent=4
        ).encode("utf-8")


        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json"
        )

        self.send_header(
            "Content-Length",
            str(len(response))
        )

        self.end_headers()

        self.wfile.write(response)



    def authenticate(self):

        header = self.headers.get(
            "Authorization"
        )


        if not header:

            self.send_json(
                401,
                {
                    "error": True,
                    "type": "missing_token",
                    "message": "Authorization required"
                }
            )

            return False



        if header.startswith("Bearer "):

            token = header[7:]

        else:

            token = header



        valid, code, message = check_token(token)


        if not valid:

            self.send_json(
                code,
                {
                    "error": True,
                    "type": "authentication_failed",
                    "message": message
                }
            )

            return False


        return True




    def do_GET(self):

        if self.path == "/joke":


            if not self.authenticate():
                return



            try:

                joke = joke_api.getjoke()


                self.send_json(
                    200,
                    {
                        "error": False,
                        "joke": joke
                    }
                )


            except BackendNotRunningError as e:


                if "timed out" in str(e).lower():

                    self.send_json(
                        504,
                        {
                            "error": True,
                            "type": "backend_timeout",
                            "message": str(e)
                        }
                    )

                else:

                    self.send_json(
                        503,
                        {
                            "error": True,
                            "type": "backend_not_running",
                            "message": str(e)
                        }
                    )



            except BackendError as e:


                self.send_json(
                    502,
                    {
                        "error": True,
                        "type": "backend_error",
                        "message": str(e)
                    }
                )



            except Exception as e:


                self.send_json(
                    500,
                    {
                        "error": True,
                        "type": "internal_error",
                        "message": str(e)
                    }
                )



        else:


            self.send_json(
                404,
                {
                    "error": True,
                    "message": "Endpoint not found"
                }
            )




if __name__ == "__main__":


    server = HTTPServer(
        ("0.0.0.0", 8089),
        JokeRequestHandler
    )


    print(
        "Joke server running on port 8080"
    )


    try:
        put_tokens_into_tempfile()
        server.serve_forever()


    except KeyboardInterrupt:
        import os
        os.remove("secrets/tokens.txt")
        
        print(
            "\nStopping server"
        )
        server.server_close()