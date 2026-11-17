import { describe, expect, it } from "vitest";
import { validateClientInput } from "./client-form";

describe("validateClientInput", () => {
  it("accepts a well-formed name and GSTIN", () => {
    expect(validateClientInput({ name: "Acme Traders", gstin: "27AAAPL1234C1Z5" })).toBeNull();
  });

  it("rejects a short name", () => {
    expect(validateClientInput({ name: " A ", gstin: "27AAAPL1234C1Z5" })).toMatch(/legal name/);
  });

  it("rejects a malformed GSTIN", () => {
    expect(validateClientInput({ name: "Acme", gstin: "27AAAPL1234C" })).toMatch(/GSTIN/);
  });
});
