function gatewayBase() {
  return (process.env.GATEWAY_URL || process.env.FCQF_GATEWAY_URL || "").replace(/\/$/, "");
}

export async function proxyToGateway(req, res, extraPath) {
  res.setHeader("Access-Control-Allow-Origin", req.headers.origin || "*");
  res.setHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS,PUT,DELETE");
  res.setHeader("Access-Control-Allow-Headers", "Authorization,Content-Type,X-FCQF-Token,Accept");
  if (req.method === "OPTIONS") {
    res.status(204).end();
    return;
  }

  const gateway = gatewayBase();
  if (!gateway) {
    res.status(503).json({
      detail:
        "Set GATEWAY_URL in Vercel → Settings → Environment Variables to your Railway URL (https://….up.railway.app), then Redeploy. Do not use localhost.",
    });
    return;
  }
  if (/localhost|127\.0\.0\.1/i.test(gateway)) {
    res.status(502).json({ detail: "GATEWAY_URL cannot be localhost on Vercel." });
    return;
  }

  const incoming = new URL(req.url || "/", "http://n");
  let suffix = extraPath || incoming.pathname.replace(/^\/api/, "") || "/";
  if (incoming.pathname === "/api/proxy" || incoming.pathname.endsWith("/proxy")) {
    const p = incoming.searchParams.get("path") || "";
    suffix = "/" + p.replace(/^\//, "");
  }
  if (!suffix.startsWith("/")) suffix = "/" + suffix;
  const target = gateway + suffix + incoming.search.replace(/^\?path=[^&]*&?/, "?");

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
      detail: `Cannot reach GATEWAY_URL (${gateway}${suffix}). ${e instanceof Error ? e.message : "upstream error"}`,
    });
  }
}
