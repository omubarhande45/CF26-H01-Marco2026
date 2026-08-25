/** Explicit route: POST /api/auth/login → GATEWAY_URL/auth/login */
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
  if (/localhost|127\.0\.0\.1/i.test(gateway)) {
    res.status(502).json({ detail: "GATEWAY_URL cannot be localhost." });
    return;
  }

  const headers = { Accept: "application/json", "Content-Type": "application/json" };
  let body;
  if (req.body != null) {
    body = typeof req.body === "string" ? req.body : JSON.stringify(req.body);
  }

  try {
    const upstream = await fetch(gateway + "/auth/login", { method: req.method || "POST", headers, body });
    const text = await upstream.text();
    res.status(upstream.status);
    res.setHeader("Content-Type", "application/json");
    try {
      res.json(JSON.parse(text || "{}"));
    } catch {
      res.send(text);
    }
  } catch (e) {
    res.status(502).json({
      detail: `Cannot reach ${gateway}/auth/login. ${e instanceof Error ? e.message : "upstream error"}`,
    });
  }
}
