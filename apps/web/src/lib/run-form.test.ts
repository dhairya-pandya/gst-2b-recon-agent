import { describe, expect, it } from "vitest";
import { buildRunForm } from "./run-form";

describe("buildRunForm", () => {
  it("packs client, period and the two required files", () => {
    const g = new File(["{}"], "gstr2b.json", { type: "application/json" });
    const b = new File(["a,b"], "books.csv", { type: "text/csv" });
    const fd = buildRunForm({ clientId: "c1", period: "2026-11", gstr2b: g, books: b, invoices: [] });
    expect(fd.get("client_id")).toBe("c1");
    expect(fd.get("period")).toBe("2026-11");
    expect((fd.get("gstr2b") as File).name).toBe("gstr2b.json");
    expect((fd.get("books") as File).name).toBe("books.csv");
  });

  it("rejects a missing client or period", () => {
    const f = new File(["x"], "x.json");
    expect(() => buildRunForm({ clientId: "", period: "2026-11", gstr2b: f, books: f, invoices: [] })).toThrow(/client/);
    expect(() => buildRunForm({ clientId: "c", period: "", gstr2b: f, books: f, invoices: [] })).toThrow(/period/);
  });
});
