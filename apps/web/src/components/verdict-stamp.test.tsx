import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { VerdictStamp, type Verdict } from "./verdict-stamp";

const cases: [Verdict, string][] = [
  ["matched", "Matched"],
  ["partial", "Check"],
  ["missing_in_2b", "Missing"],
  ["missing_in_books", "Missing"],
  ["duplicate", "Duplicate"],
];

describe("VerdictStamp", () => {
  it.each(cases)("renders label and data-verdict for %s", (verdict, label) => {
    render(<VerdictStamp verdict={verdict} />);
    const stamp = screen.getByText(label);
    expect(stamp).toBeInTheDocument();
    expect(stamp.closest("[data-verdict]")).toHaveAttribute("data-verdict", verdict);
  });

  it("maps each verdict to its ink token", () => {
    render(<VerdictStamp verdict="matched" />);
    const el = screen.getByText("Matched").closest("[data-verdict]");
    expect(el?.className).toContain("text-matched");
  });
});
