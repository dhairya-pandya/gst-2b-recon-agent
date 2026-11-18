import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { FileField } from "./file-field";

const json = new File(["{}"], "gstr2b.json", { type: "application/json" });

describe("FileField", () => {
  it("shows the chosen file with its size", () => {
    render(<FileField label="GSTR-2B file" hint="JSON" accept=".json" files={[json]} onChange={() => {}} />);
    expect(screen.getByText("gstr2b.json")).toBeInTheDocument();
    expect(screen.getByText("1 file chosen")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Replace file" })).toBeInTheDocument();
  });

  it("removes a file from the list", () => {
    const onChange = vi.fn();
    render(<FileField label="GSTR-2B file" hint="JSON" accept=".json" files={[json]} onChange={onChange} />);
    fireEvent.click(screen.getByRole("button", { name: "Remove gstr2b.json" }));
    expect(onChange).toHaveBeenCalledWith([]);
  });

  it("opens the picker from the button", () => {
    render(<FileField label="GSTR-2B file" hint="JSON" accept=".json" files={[]} onChange={() => {}} />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const click = vi.spyOn(input, "click");
    fireEvent.click(screen.getByRole("button", { name: "Choose file" }));
    expect(click).toHaveBeenCalled();
  });

  it("adds PDFs to the list and skips duplicates", () => {
    const onChange = vi.fn();
    const a = new File(["x"], "a.pdf", { type: "application/pdf" });
    render(<FileField label="Invoices" hint="PDF" accept=".pdf" multiple files={[a]} onChange={onChange} />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const b = new File(["yy"], "b.pdf", { type: "application/pdf" });
    fireEvent.change(input, { target: { files: [a, b] } });
    expect(onChange).toHaveBeenCalledWith([a, b]);
  });
});
