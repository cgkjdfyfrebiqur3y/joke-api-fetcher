import { describe, expect, it } from "vitest";
import { TestDriver } from "testdriverai/vitest/hooks";

// This sample test exercises the exact production endpoint that the app's
// src/server/jokeapi-interface.py builds for the "Programming" category with
// safe-mode enabled, and verifies it returns a well-formed joke JSON payload.
describe("JokeAPI production /joke endpoint", () => {
  it("returns a Programming joke as JSON from production", async (context) => {
    const testdriver = TestDriver(context);

    // Start on a blank-ish page, then navigate to the production API endpoint.
    await testdriver.provision.chrome({ url: "https://jokeapi.dev" });
    await testdriver.wait(2000);

    // Navigate the browser to the exact production endpoint the app uses.
    await testdriver.find("the browser URL/address bar").click();
    await testdriver.type(
      "https://v2.jokeapi.dev/joke/Programming?safe-mode&type=single\n"
    );
    await testdriver.wait(3000);

    const assertResult = await testdriver.assert(
      'The browser is displaying a JSON response from the JokeAPI Programming endpoint containing "error": false, "category": "Programming", and a "joke" field with joke text'
    );
    expect(assertResult).toBeTruthy();
  });
});
