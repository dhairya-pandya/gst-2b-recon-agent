import { redirect } from "next/navigation";

// Magic-link and OAuth sign-ins land on /runs. There is no run list yet, so send users to the new-run form.
export default function RunsIndex() {
  redirect("/runs/new");
}
