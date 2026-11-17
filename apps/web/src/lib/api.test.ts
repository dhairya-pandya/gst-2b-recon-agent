import { describe, expect, it, vi } from "vitest";
import { apiFetch } from "./api";

describe("apiFetch", () => {
  it("attaches the Supabase access token as a bearer header", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response("{}", { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    await apiFetch("/clients", { token: "tok-123", base: "http://api.test" });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://api.test/clients");
    expect(new Headers(init.headers).get("Authorization")).toBe("Bearer tok-123");
  });

  it("throws with the API detail on a non-2xx response", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: { field: "inum" } }), { status: 422 }),
    ));
    await expect(apiFetch("/runs", { token: "t", base: "http://x" })).rejects.toThrow(/inum/);
  });
});
