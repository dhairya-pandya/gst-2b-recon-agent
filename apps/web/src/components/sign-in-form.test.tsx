import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SignInForm, type AuthClient } from "./sign-in-form";

function fakeAuth(): AuthClient & { signInWithOtp: ReturnType<typeof vi.fn>; signInWithOAuth: ReturnType<typeof vi.fn> } {
  return {
    signInWithOtp: vi.fn().mockResolvedValue({ error: null }),
    signInWithOAuth: vi.fn().mockResolvedValue({ error: null }),
  };
}

describe("SignInForm", () => {
  it("starts Google sign-in", () => {
    const auth = fakeAuth();
    render(<SignInForm auth={auth} redirectTo="http://x/runs" />);
    fireEvent.click(screen.getByRole("button", { name: "Continue with Google" }));
    expect(auth.signInWithOAuth).toHaveBeenCalledWith(
      expect.objectContaining({ provider: "google" }),
    );
  });

  it("sends an email magic link and confirms", async () => {
    const auth = fakeAuth();
    render(<SignInForm auth={auth} redirectTo="http://x/runs" />);
    fireEvent.change(screen.getByLabelText("Work email"), { target: { value: "ca@firm.in" } });
    fireEvent.click(screen.getByRole("button", { name: "Email me a sign-in link" }));
    expect(auth.signInWithOtp).toHaveBeenCalledWith(
      expect.objectContaining({ email: "ca@firm.in" }),
    );
    expect(await screen.findByText("Check your email for a sign-in link.")).toBeInTheDocument();
  });
});
