/**
 * Vercel serverless proxy: browser /api/* → FastAPI gateway.
 * Set GATEWAY_URL in the Vercel project (e.g. https://fcqf-gateway.up.railway.app).
 */
export default async function handler(req, res) {
  const gateway = (process.env.GATEWAY_URL || process.env.FCQF_GATEWAY_URL || "").replace(/\/$/, "");
  if (!gateway) {
    res.status(503).json({
      detail:
        "Gateway is not configured on Vercel. Deploy the FCQF FastAPI service and set GATEWAY_URL (Project → Settings → Environment Variables) to that public URL, then redeploy.",
    });
    return;
  }

  const incoming = new URL(req.url || "/", "http://n");
  const suffix = incoming.pathname.replace(/^\/api/, "") || "/";
  const target = gateway + suffix + incoming.search;

  const headers = {
    Accept: "application/json",
    "Content-Type": req.headers["content-type"] || "application/json",
  };
  if (req.headers.authorization) headers.Authorization = req.headers.authorization;
  if (req.headers["x-fcqf-token"]) headers["X-FCQF-Token"] = req.headers["x-fcqf-token"];
  if (req.headers.cookie) headers.Cookie = req.headers.cookie;

  const method = (req.method || "GET").toUpperCase();
  let body;
  if (!["GET", "HEAD"].includes(method)) {
    if (typeof req.body === "string") body = req.body;
    else if (req.body != null) body = JSON.stringify(req.body);
  }

  try {
    const upstream = await fetch(target, { method, headers, body });
    const text = await upstream.text();
    const setCookie = upstream.headers.get("set-cookie");
    if (setCookie) res.setHeader("Set-Cookie", setCookie);
    res.status(upstream.status);
    const ct = upstream.headers.get("content-type") || "application/json";
    res.setHeader("Content-Type", ct);
    if (!text) {
      res.end();
      return;
    }
    try {
      res.json(JSON.parse(text));
    } catch {
      res.send(text);
    }
  } catch (e) {
    res.status(502).json({
      detail: `Cannot reach GATEWAY_URL (${gateway}). ${e instanceof Error ? e.message : "upstream error"}`,
    });
  }
}
