import { describe, expect, it } from "vitest";
import { isProtected } from "./auth-guard";

describe("isProtected", () => {
  it("guards the client, new-run and run pages", () => {
    expect(isProtected("/clients")).toBe(true);
    expect(isProtected("/runs/new")).toBe(true);
    expect(isProtected("/runs/abc-123")).toBe(true);
  });

  it("leaves home, sign-in and the sign-in callback open", () => {
    expect(isProtected("/")).toBe(false);
    expect(isProtected("/sign-in")).toBe(false);
    expect(isProtected("/runs")).toBe(false);
  });
});
