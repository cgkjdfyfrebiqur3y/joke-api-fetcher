# TestDriver tests — Joke API server (JokeAPI v2 dependency stubbed)

These tests exercise **your own code** (token auth, request routing, the JSON
response envelope in `src/server/frontend.py`) while **stubbing out the external
JokeAPI v2 dependency** (`https://v2.jokeapi.dev`). No test ever calls the
third-party API, so the suite is deterministic and doesn't depend on that
service being up — which is exactly what the issue asked for ("test my script
but not the JokeAPI v2 dependency").

## How the JokeAPI v2 dependency is stubbed

`tests/harness/run_server.py`:

- Loads your **real** `frontend.py` and its **real** error classes.
- Injects a stub `jokeapi_interface` module so that `JokeAPI.getjoke()` returns
  a fixed joke instead of making an HTTP request to `v2.jokeapi.dev`.
- Serves a tiny UI at `/` (`tests/harness/index.html`) on the **same origin** as
  `/joke`, giving TestDriver a browser surface to drive. The `/joke` route is
  handled entirely by your real code.
- Writes a known `secrets/tokens.txt` with one **valid** token
  (`validtoken123`) and one **invalid** token (`invalidtoken456`).

Nothing under `src/` is modified.

## Running

```bash
# 1) install deps
npm install --legacy-peer-deps

# 2) start the harness server (serves / and /joke; JokeAPI v2 stubbed)
python3 tests/harness/run_server.py            # listens on :8089

# 3) expose it publicly (any tunnel) and run the tests against that URL
APP_URL="https://<your-public-url>/" \
TUNNEL_PASSWORD="<loca.lt password, if using loca.lt>" \
  npx vitest run tests/joke-server.test.mjs
```

`APP_URL` defaults to `http://localhost:8089/`. `TUNNEL_PASSWORD` is only needed
for `*.loca.lt` URLs (their one-time interstitial); get it from
<https://loca.lt/mytunnelpassword>.

## Requirements

- **`TD_API_KEY`** must be set so TestDriver can provision a browser sandbox.
  Get one at <https://console.testdriver.ai/team>. In CI, prefer GitHub OIDC via
  `testdriverai/action` (no stored secret to rotate).
- **Vitest >= 4** (TestDriver requires it).

## What each test covers

- **returns a joke for a valid token** — clicks "Get Joke" with the default
  valid token and asserts the stubbed joke renders (proves auth + routing +
  200/JSON envelope end to end).
- **rejects an invalid token with an error** — swaps in the invalid token and
  asserts the page shows an HTTP error and **no** joke (proves your
  `check_token()` 403 path).
