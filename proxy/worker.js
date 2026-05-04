/**
 * Envio Cloud Proxy — Cloudflare Worker
 *
 * Relays LLM requests from the envio CLI to Groq,
 * keeping the API key server-side.  Rate-limits per
 * machine ID using Workers KV.
 */

const DAILY_LIMIT = 30;           // requests per machine per day
const IP_RPM_LIMIT = 60;          // requests per minute per IP
const ALLOWED_MODEL = "llama-3.3-70b-versatile";

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // ── Health check ──────────────────────────────────────
    if (url.pathname === "/health") {
      return Response.json({ status: "ok", service: "envio-proxy" });
    }

    // ── Only accept POST to /v1/chat ──────────────────────
    if (request.method !== "POST" || url.pathname !== "/v1/chat") {
      return Response.json({ error: "Not found" }, { status: 404 });
    }

    // ── Validate User-Agent ───────────────────────────────
    const ua = request.headers.get("User-Agent") || "";
    if (!ua.startsWith("envio/")) {
      return Response.json({ error: "Forbidden" }, { status: 403 });
    }

    // ── Parse body ────────────────────────────────────────
    let body;
    try {
      body = await request.json();
    } catch {
      return Response.json({ error: "Invalid JSON" }, { status: 400 });
    }

    const machineId = body.machine_id;
    if (!machineId || typeof machineId !== "string" || machineId.length < 16) {
      return Response.json({ error: "Invalid machine_id" }, { status: 400 });
    }

    const messages = body.messages;
    if (!Array.isArray(messages) || messages.length === 0) {
      return Response.json({ error: "messages required" }, { status: 400 });
    }

    // ── IP rate limit (per-minute) ────────────────────────
    const clientIP = request.headers.get("CF-Connecting-IP") || "unknown";
    const ipKey = `ip:${clientIP}:${minuteBucket()}`;
    const ipCount = parseInt((await env.RATE_LIMIT.get(ipKey)) || "0");
    if (ipCount >= IP_RPM_LIMIT) {
      return Response.json(
        { error: "Too many requests. Try again in a minute." },
        { status: 429 }
      );
    }
    await env.RATE_LIMIT.put(ipKey, String(ipCount + 1), { expirationTtl: 120 });

    // ── Machine daily rate limit ──────────────────────────
    const today = new Date().toISOString().split("T")[0];
    const rlKey = `rl:${machineId}:${today}`;
    const current = parseInt((await env.RATE_LIMIT.get(rlKey)) || "0");

    if (current >= DAILY_LIMIT) {
      return Response.json(
        {
          error: `Daily limit reached (${DAILY_LIMIT}/day). Use your own API key: envio config api <key>`,
          limit_reached: true,
          remaining: 0,
        },
        {
          status: 429,
          headers: {
            "X-RateLimit-Limit": String(DAILY_LIMIT),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": endOfDayUTC(),
          },
        }
      );
    }

    // ── Forward to Groq ───────────────────────────────────
    const remaining = DAILY_LIMIT - current - 1;
    try {
      const groqResp = await fetch(
        "https://api.groq.com/openai/v1/chat/completions",
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${env.GROQ_API_KEY}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            model: ALLOWED_MODEL,
            messages: messages,
            temperature: body.temperature ?? 0,
            max_tokens: Math.min(body.max_tokens ?? 2048, 4096),
          }),
        }
      );

      // Increment counter only on successful forward
      await env.RATE_LIMIT.put(rlKey, String(current + 1), {
        expirationTtl: 86400,
      });

      const groqData = await groqResp.json();

      return Response.json(groqData, {
        status: groqResp.status,
        headers: {
          "X-RateLimit-Limit": String(DAILY_LIMIT),
          "X-RateLimit-Remaining": String(remaining),
          "X-Powered-By": "envio-cloud",
        },
      });
    } catch (err) {
      return Response.json(
        { error: `Upstream error: ${err.message}` },
        { status: 502 }
      );
    }
  },
};

// ── Helpers ─────────────────────────────────────────────

function minuteBucket() {
  const now = new Date();
  return `${now.toISOString().slice(0, 16)}`; // "2026-05-04T22:28"
}

function endOfDayUTC() {
  const tomorrow = new Date();
  tomorrow.setUTCHours(24, 0, 0, 0);
  return tomorrow.toISOString();
}
