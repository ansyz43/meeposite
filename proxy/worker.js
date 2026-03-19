// Cloudflare Worker — OpenAI API Proxy
// Forwards requests to api.openai.com, bypassing geo-restrictions.
// Deploy: npx wrangler deploy

export default {
  async fetch(request, env) {
    // Only allow POST (API calls) and OPTIONS (CORS preflight)
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
      });
    }

    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    // Verify proxy secret to prevent unauthorized use
    const proxyKey = request.headers.get("X-Proxy-Key");
    if (env.PROXY_SECRET && proxyKey !== env.PROXY_SECRET) {
      return new Response("Unauthorized", { status: 401 });
    }

    // Rewrite URL to OpenAI
    const url = new URL(request.url);
    url.hostname = "api.openai.com";
    url.port = "";
    url.protocol = "https:";

    // Forward the request
    const headers = new Headers(request.headers);
    headers.delete("X-Proxy-Key");
    headers.set("Host", "api.openai.com");

    const response = await fetch(new Request(url.toString(), {
      method: request.method,
      headers: headers,
      body: request.body,
    }));

    // Return response with CORS headers
    const responseHeaders = new Headers(response.headers);
    responseHeaders.set("Access-Control-Allow-Origin", "*");

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  },
};
