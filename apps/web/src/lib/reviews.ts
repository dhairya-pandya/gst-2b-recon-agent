export type Decision = "accept" | "reject";
export type Review = { row_key: string; decision: Decision };

// Reviews are an append-only log; the latest decision per row wins.
export function latestDecisions(reviews: Review[] = []): Record<string, Decision> {
  const out: Record<string, Decision> = {};
  for (const r of reviews) out[r.row_key] = r.decision;
  return out;
}
