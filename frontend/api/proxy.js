export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", req.headers.origin || "*");
  res.setHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Authorization,Content-Type,X-FCQF-Token,Accept");
  if (req.method === "OPTIONS") {
    res.status(204).end();
    return;
  }

  const gateway = (process.env.GATEWAY_URL || process.env.FCQF_GATEWAY_URL || "").replace(/\/$/, "");
  if (!gateway) {
    res.status(503).json({
      detail:
        "Set GATEWAY_URL in Vercel → Settings → Environment Variables to https://YOUR-APP.up.railway.app then Redeploy.",
    });
    return;
  }

  const incoming = new URL(req.url || "/", "http://n");
  const fromQuery = incoming.searchParams.get("path");
  let suffix = fromQuery ? "/" + fromQuery.replace(/^\//, "") : incoming.pathname.replace(/^\/api(\/proxy)?/, "") || "/";
  if (!suffix.startsWith("/")) suffix = "/" + suffix;
  if (suffix === "/proxy") suffix = "/";
  const rest = incoming.search.replace(/[?&]path=[^&]*/g, "").replace(/^&/, "?");
  const target = gateway + suffix + (rest.startsWith("?") ? rest : rest ? "?" + rest : "");

  const headers = { Accept: "application/json", "Content-Type": req.headers["content-type"] || "application/json" };
  if (req.headers.authorization) headers.Authorization = req.headers.authorization;
  if (req.headers["x-fcqf-token"]) headers["X-FCQF-Token"] = req.headers["x-fcqf-token"];

  const method = (req.method || "GET").toUpperCase();
  let body;
  if (!["GET", "HEAD"].includes(method) && req.body != null) {
    body = typeof req.body === "string" ? req.body : JSON.stringify(req.body);
  }

  try {
    const upstream = await fetch(target, { method, headers, body });
    const text = await upstream.text();
    res.status(upstream.status);
    res.setHeader("Content-Type", upstream.headers.get("content-type") || "application/json");
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
      detail: `Cannot reach GATEWAY_URL (${target}). ${e instanceof Error ? e.message : "upstream error"}`,
    });
  }
}
