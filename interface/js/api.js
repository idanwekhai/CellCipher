// Thin fetch wrapper around the biocrypt API. Kept separate from DOM code so
// it's the one place that knows the request/response shapes.

const BASE = "/api";

async function request(path, options) {
  const response = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ? JSON.stringify(body.detail) : detail;
    } catch {
      /* response wasn't JSON; keep statusText */
    }
    throw new Error(`${response.status} ${detail}`);
  }
  return response.json();
}

export function encodeText(text, { passphrase, useNonce = true } = {}) {
  const body = { text };
  if (passphrase) {
    body.passphrase = passphrase;
    body.use_nonce = useNonce;
  }
  return request("/encode", { method: "POST", body: JSON.stringify(body) });
}

export function decodeDna(dna, { passphrase } = {}) {
  const body = { dna };
  if (passphrase) body.passphrase = passphrase;
  return request("/decode", { method: "POST", body: JSON.stringify(body) });
}

export function getInfo() {
  return request("/info", { method: "GET" });
}
