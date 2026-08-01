import { describe, expect, it } from "vitest";
import { TestDriver } from "testdriverai/vitest/hooks";

// ---------------------------------------------------------------------------
// End-to-end test of the user's OWN Joke API server code (token auth, request
// routing, JSON response envelope) with the external JokeAPI v2 dependency
// (v2.jokeapi.dev) STUBBED OUT.
//
// The external dependency is replaced in tests/harness/run_server.py: the real
// JokeAPI.getjoke() (which calls https://v2.jokeapi.dev) is swapped for a stub
// that returns a fixed joke, so this test never touches the third-party API.
// Everything else — the token file, check_token(), authenticate(), do_GET(),
// status codes and the {"error", "joke"|"message"} envelope — is the project's
// REAL code.
//
// Run the harness + tunnel before this test and pass its public URL as APP_URL:
//   python3 tests/harness/run_server.py            # serves / and /joke
//   (exposed via a tunnel by run_local_app)
//   APP_URL=<public-url> npx vitest run tests/joke-server.test.mjs
//
// If the tunnel is a *.loca.lt URL it shows a one-time interstitial; set
// TUNNEL_PASSWORD to the value from https://loca.lt/mytunnelpassword and the
// test will click through it.
// ---------------------------------------------------------------------------

const APP_URL = process.env.APP_URL || "http://localhost:8089/";
const TUNNEL_PASSWORD = process.env.TUNNEL_PASSWORD || "";
const STUB_JOKE_SNIPPET = "light attracts bugs";

async function dismissTunnelInterstitial(testdriver) {
  // *.loca.lt shows a "You are about to visit…" reminder that wants the tunnel
  // password (the sandbox's public IP). Only appears for loca.lt URLs.
  if (!/loca\.lt/.test(APP_URL) || !TUNNEL_PASSWORD) return;
  const gate = await testdriver.find("tunnel password / IP address input box", {
    timeout: 8000,
  });
  if (gate && gate.found && gate.found()) {
    await gate.click();
    await testdriver.type(TUNNEL_PASSWORD);
    const submit = await testdriver.find("Click to Submit button");
    await submit.click();
    await testdriver.wait(2000);
  }
}

describe("Joke API server (JokeAPI v2 dependency stubbed)", () => {
  it("returns a joke for a valid token", async (context) => {
    const testdriver = TestDriver(context);

    await testdriver.provision.chrome({ url: APP_URL });
    await dismissTunnelInterstitial(testdriver);

    // The harness page defaults the token field to a VALID token, so just
    // fetch a joke.
    const getJoke = await testdriver.find("Get Joke button");
    await getJoke.click();
    await testdriver.wait(2000);

    // The stubbed joke should render, proving the whole auth+routing path in
    // the user's server worked end to end — without calling JokeAPI v2.
    const gotJoke = await testdriver.assert(
      `the page shows a success status and a joke containing "${STUB_JOKE_SNIPPET}"`,
    );
    expect(gotJoke).toBeTruthy();
  });

  it("rejects an invalid token with an error", async (context) => {
    const testdriver = TestDriver(context);

    await testdriver.provision.chrome({ url: APP_URL });
    await dismissTunnelInterstitial(testdriver);

    // Replace the default valid token with the invalid one.
    const tokenField = await testdriver.find("Auth token input field");
    await tokenField.click();
    await testdriver.pressKeys(["ctrl", "a"]);
    await testdriver.pressKeys(["backspace"]);
    await testdriver.type("invalidtoken456");

    const getJoke = await testdriver.find("Get Joke button");
    await getJoke.click();
    await testdriver.wait(2000);

    // The user's check_token() maps an invalid token to HTTP 403 "Token
    // invalid"; the page should show an error, and NO joke.
    const showsError = await testdriver.assert(
      "the page shows an error status (an HTTP error like 403) and does not show a joke",
    );
    expect(showsError).toBeTruthy();
  });
});
