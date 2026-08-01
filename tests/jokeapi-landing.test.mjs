import { describe, expect, it } from "vitest";
import { TestDriver } from "testdriverai/vitest/hooks";

// The joke-api-fetcher package fetches jokes from JokeAPI (https://jokeapi.dev).
// This sample test verifies the production JokeAPI documentation site loads.
describe("JokeAPI production landing page", () => {
  it("loads the JokeAPI documentation site", async (context) => {
    const testdriver = TestDriver(context);

    await testdriver.provision.chrome({ url: "https://jokeapi.dev" });

    // Wait for the documentation page to render.
    await testdriver.wait(3000);

    const assertResult = await testdriver.assert(
      'The JokeAPI documentation landing page is loaded, showing the "JokeAPI Documentation" heading and information describing it as a REST API that delivers jokes'
    );
    expect(assertResult).toBeTruthy();
  });
});
