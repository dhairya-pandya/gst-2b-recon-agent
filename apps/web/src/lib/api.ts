export type ApiOptions = {
  token: string;
  base?: string;
  method?: "GET" | "POST";
  body?: BodyInit;
  json?: unknown;
};

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: unknown,
  ) {
    super(`API ${status}: ${JSON.stringify(detail)}`);
  }
}

export async function apiFetch(path: string, opts: ApiOptions): Promise<unknown> {
  const base = opts.base ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8080";
  const headers: Record<string, string> = { Authorization: `Bearer ${opts.token}` };
  let body: BodyInit | undefined = opts.body;
  if (opts.json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(opts.json);
  }
  const res = await fetch(`${base}${path}`, {
    method: opts.method ?? "GET",
    body,
    headers,
  });
  const json: unknown = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = (json as { detail?: unknown }).detail ?? json;
    throw new ApiError(res.status, detail);
  }
  return json;
}
