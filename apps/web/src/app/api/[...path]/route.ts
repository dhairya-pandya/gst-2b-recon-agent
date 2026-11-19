// Same-origin proxy to the FastAPI service, so the whole product lives at one URL.
// API_ORIGIN is read at request time (a Cloud Run env var), never baked into the bundle.
const FORWARD_REQUEST = ["authorization", "content-type"];
const FORWARD_RESPONSE = ["content-type", "retry-after"];

function apiOrigin(): string {
  return process.env.API_ORIGIN ?? "http://localhost:8080";
}

async function proxy(req: Request, ctx: { params: Promise<{ path: string[] }> }): Promise<Response> {
  const { path } = await ctx.params;
  const url = new URL(req.url);
  const target = `${apiOrigin()}/${path.map(encodeURIComponent).join("/")}${url.search}`;

  const headers = new Headers();
  for (const h of FORWARD_REQUEST) {
    const v = req.headers.get(h);
    if (v) headers.set(h, v);
  }
  const hasBody = req.method !== "GET" && req.method !== "HEAD";

  let upstream: Response;
  try {
    upstream = await fetch(target, {
      method: req.method,
      headers,
      body: hasBody ? req.body : undefined,
      // Stream uploads through instead of buffering them in memory.
      ...(hasBody ? { duplex: "half" } : {}),
      cache: "no-store",
    } as RequestInit);
  } catch {
    return Response.json({ detail: "The reconciliation service is unreachable." }, { status: 502 });
  }

  const out = new Headers();
  for (const h of FORWARD_RESPONSE) {
    const v = upstream.headers.get(h);
    if (v) out.set(h, v);
  }
  return new Response(upstream.body, { status: upstream.status, headers: out });
}

export const GET = proxy;
export const POST = proxy;
