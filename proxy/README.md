# Envio Cloud Proxy

A lightweight Cloudflare Worker that relays envio CLI LLM requests to Groq.
Your API key stays server-side — users never see it.

## Why?

Envio uses AI to understand natural language package requests (`envio prompt "flask api with auth"`).
Instead of requiring every user to get their own API key, this proxy provides **free AI access
out of the box** — rate-limited to 30 requests/day per machine.

## Architecture

```
envio CLI  ──HTTPS──▶  Cloudflare Worker  ──HTTPS──▶  Groq API
(no key)               (your key in CF secret)        (LLM inference)
```

- **User's machine**: Sends requests with an anonymous machine fingerprint (SHA-256 hash)
- **Cloudflare Worker**: Validates requests, enforces rate limits via KV, forwards to Groq
- **Groq API**: Runs Llama 3.3 70B inference, returns response

## Self-Hosting (Deploy Your Own Proxy)

If you're forking envio or want to run your own proxy:

### Prerequisites

- [Node.js](https://nodejs.org/) (v18+)
- [Cloudflare account](https://dash.cloudflare.com/sign-up) (free)
- [Groq API key](https://console.groq.com/) (free)

### Steps

```bash
# 1. Install Wrangler CLI
npm install -g wrangler

# 2. Login to Cloudflare
npx wrangler login

# 3. Create KV namespace for rate limiting
npx wrangler kv namespace create RATE_LIMIT
# Copy the "id" from the output and paste it into wrangler.toml

# 4. Deploy the Worker
npx wrangler deploy

# 5. Set your Groq API key as a secret (never stored in code)
npx wrangler secret put GROQ_API_KEY
# Paste your key when prompted — it's encrypted at rest

# 6. Verify
curl https://envio-proxy.<your-account>.workers.dev/health
# Should return: {"status":"ok","service":"envio-proxy"}
```

### Point envio to your proxy

Users can point their envio installation to your proxy by setting:

```bash
envio config set cloud_relay_url https://your-proxy.your-account.workers.dev
```

Or in `~/.envio/config.json`:

```json
{
  "cloud_relay_url": "https://your-proxy.your-account.workers.dev"
}
```

## Rate Limits

| Limit | Value | Scope |
|:------|:------|:------|
| Daily requests | 30/day | Per machine (anonymous fingerprint) |
| Per-minute requests | 60/min | Per IP address |
| User-Agent | Must start with `envio/` | Blocks non-envio traffic |
| Model | `llama-3.3-70b-versatile` only | Prevents model abuse |
| Max tokens | 4096 | Per request |

## Security

- **API key**: Stored as a Cloudflare secret (encrypted, never in code or logs)
- **Machine ID**: SHA-256 hash of non-PII system attributes (hostname, OS, etc.) — not reversible
- **No user data stored**: Requests are forwarded and forgotten — no logging of prompts or responses
- **User-Agent validation**: Only accepts requests from the envio CLI

## Configuration

Edit `wrangler.toml`:

| Field | Description |
|:------|:-----------|
| `name` | Worker name (appears in your Cloudflare dashboard) |
| `kv_namespaces[0].id` | KV namespace ID for rate limit storage |

Edit `worker.js` constants:

| Constant | Default | Description |
|:---------|:--------|:-----------|
| `DAILY_LIMIT` | `30` | Max requests per machine per day |
| `IP_RPM_LIMIT` | `60` | Max requests per IP per minute |
| `ALLOWED_MODEL` | `llama-3.3-70b-versatile` | Model forwarded to Groq |

## Local Development

```bash
# Run locally with wrangler dev (uses local KV simulation)
npx wrangler dev

# Test health endpoint
curl http://localhost:8787/health
```

## Files

| File | Purpose |
|:-----|:--------|
| `worker.js` | Cloudflare Worker source — request validation, rate limiting, Groq forwarding |
| `wrangler.toml` | Wrangler deployment config — worker name, KV bindings |
