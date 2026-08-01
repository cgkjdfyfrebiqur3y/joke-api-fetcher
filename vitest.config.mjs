import { defineConfig } from "vitest/config";
import { config } from "dotenv";

config();

export default defineConfig({
  test: {
    testTimeout: 900000,
    hookTimeout: 900000,
  },
});
