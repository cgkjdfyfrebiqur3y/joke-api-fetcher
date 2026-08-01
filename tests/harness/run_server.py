"""
Test harness that runs the project's REAL HTTP server (src/server/frontend.py)
while STUBBING the external JokeAPI v2 dependency (v2.jokeapi.dev).

Goal of this harness (per the issue "Test my script but not the JokeAPI v2
dependency"):
  - Exercise the user's own code: token auth (check_token / authenticate),
    request routing (do_GET), status codes and JSON envelope.
  - Do NOT make any real network call to https://v2.jokeapi.dev. Instead the
    JokeAPI.getjoke() method is monkeypatched to return a deterministic joke,
    so tests never depend on the third-party service being up.

It loads frontend.py by file path (the source files use a hyphenated module
name `jokeapi-interface.py` and relative `secrets/` paths, which prevent a
plain import), injecting a stub `jokeapi_interface` module first.

A tiny HTML page is served at `/` (same origin as `/joke`) so a browser-based
tool like TestDriver has a UI surface to drive. The `/joke` route is handled by
the project's REAL handler code, unchanged.
"""

import importlib.util
import os
import sys
import types
from http.server import HTTPServer, ThreadingHTTPServer

SERVER_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "src", "server"
)
SERVER_DIR = os.path.abspath(SERVER_DIR)
SECRETS_DIR = os.path.join(SERVER_DIR, "secrets")
HARNESS_DIR = os.path.abspath(os.path.dirname(__file__))

# The stubbed joke that replaces the external JokeAPI v2 response.
STUB_JOKE = "Why do programmers prefer dark mode? Because light attracts bugs."


def _load_real_jokeapi_interface():
    """Load the real jokeapi-interface.py (hyphenated filename)."""
    path = os.path.join(SERVER_DIR, "jokeapi-interface.py")
    spec = importlib.util.spec_from_file_location("jokeapi_interface", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_stub_jokeapi_interface():
    """
    Build a stand-in `jokeapi_interface` module.

    We reuse the REAL error classes from the project so the server's
    except-clauses behave identically, but replace JokeAPI so getjoke()
    returns a canned joke instead of calling v2.jokeapi.dev.
    """
    real = _load_real_jokeapi_interface()

    stub = types.ModuleType("jokeapi_interface")

    # Re-export the project's real error hierarchy unchanged.
    stub.BackendError = real.BackendError
    stub.BackendNotRunningError = real.BackendNotRunningError

    class StubJokeAPI:
        """Drop-in for the real JokeAPI, but with NO external network call."""

        def __init__(self, categories=None):
            self.categories = categories or []

        def getjoke(self, type=None):
            mode = os.environ.get("STUB_JOKE_MODE", "ok")
            if mode == "backend_down":
                raise real.BackendNotRunningError("JokeAPI cannot be reached")
            if mode == "backend_timeout":
                raise real.BackendNotRunningError("JokeAPI timed out")
            if mode == "backend_error":
                raise real.BackendError("Backend broken")
            return STUB_JOKE

    stub.JokeAPI = StubJokeAPI
    return stub


def load_frontend():
    """Load the real frontend.py with the JokeAPI v2 dependency stubbed out."""
    # Inject the stub BEFORE importing frontend so its
    # `from jokeapi_interface import ...` resolves to the stub.
    sys.modules["jokeapi_interface"] = _build_stub_jokeapi_interface()

    # frontend.py uses relative paths like "secrets/tokens.txt", so run from
    # SERVER_DIR.
    os.makedirs(SECRETS_DIR, exist_ok=True)
    os.chdir(SERVER_DIR)
    if SERVER_DIR not in sys.path:
        sys.path.insert(0, SERVER_DIR)

    path = os.path.join(SERVER_DIR, "frontend.py")
    spec = importlib.util.spec_from_file_location("frontend", path)
    frontend = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(frontend)
    return frontend


def write_token_file(frontend):
    """
    Populate secrets/tokens.txt the way the server expects to read it.

    The server's own put_tokens_into_tempfile() is broken (its inner helper is
    never called and it references an undefined `tokens`), so we build the
    temp token file directly from the documented token records in tokens.py.
    Format per line: TOKEN STATE EXPIRATION EXPIRED REASON INVALID_CODE
    """
    lines = [
        # A valid, non-expired token -> /joke should return 200 + joke.
        "validtoken123 valid 2099-12-31T23:59:59 false none 0",
        # An invalid token -> 403.
        "invalidtoken456 invalid 2099-12-31T23:59:59 false fake 403",
    ]
    os.makedirs(SECRETS_DIR, exist_ok=True)
    with open(os.path.join(SECRETS_DIR, "tokens.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")


VALID_TOKEN = "validtoken123"
INVALID_TOKEN = "invalidtoken456"


def make_handler(frontend):
    """
    Subclass the project's REAL request handler to also serve the test HTML at
    `/`. All `/joke` behavior stays in the project's own do_GET (via super()).
    """
    RealHandler = frontend.JokeRequestHandler

    class HarnessHandler(RealHandler):
        # Advertise HTTP/1.1 but responses set Content-Length, so keep-alive is
        # safe; still, close per-request to avoid any stuck connection blocking
        # the (threaded) server pool.
        protocol_version = "HTTP/1.1"

        def do_GET(self):
            if self.path == "/" or self.path.startswith("/index.html"):
                with open(os.path.join(HARNESS_DIR, "index.html"), "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(body)
                return
            # Everything else -> the project's real handler (auth, /joke, 404).
            return super().do_GET()

    return HarnessHandler


def main():
    frontend = load_frontend()
    write_token_file(frontend)

    port = int(os.environ.get("PORT", "8089"))
    handler = make_handler(frontend)
    # ThreadingHTTPServer so a slow/stalled connection (e.g. a tunnel health
    # probe) can't block every other request the way a single-threaded
    # HTTPServer would.
    server = ThreadingHTTPServer(("0.0.0.0", port), handler)
    server.daemon_threads = True
    print(
        f"Test harness server (JokeAPI v2 STUBBED) running on port {port}",
        flush=True,
    )
    print(f"  valid token:   {VALID_TOKEN}", flush=True)
    print(f"  invalid token: {INVALID_TOKEN}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    main()
