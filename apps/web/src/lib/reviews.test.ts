import { describe, expect, it } from "vitest";
import { latestDecisions } from "./reviews";

describe("latestDecisions", () => {
  it("keeps the last decision per row", () => {
    expect(
      latestDecisions([
        { row_key: "A|1", decision: "accept" },
        { row_key: "B|2", decision: "reject" },
        { row_key: "A|1", decision: "reject" },
      ]),
    ).toEqual({ "A|1": "reject", "B|2": "reject" });
  });
  it("handles no reviews", () => {
    expect(latestDecisions()).toEqual({});
  });
});
