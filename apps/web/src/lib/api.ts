export type ApiOptions = {
  token: string;
  base?: string;
  method?: "GET" | "POST";
  body?: BodyInit;
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
  const res = await fetch(`${base}${path}`, {
    method: opts.method ?? "GET",
    body: opts.body,
    headers: { Authorization: `Bearer ${opts.token}` },
  });
  const json: unknown = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = (json as { detail?: unknown }).detail ?? json;
    throw new ApiError(res.status, detail);
  }
  return json;
}
