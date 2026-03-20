// Cloudflare Worker — OpenAI API Proxy
// Forwards requests to api.openai.com, bypassing geo-restrictions.
// Deploy: npx wrangler deploy

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
      });
    }

    // Rewrite URL to OpenAI
    const url = new URL(request.url);
    url.hostname = "api.openai.com";
    url.port = "";
    url.protocol = "https:";

    // Forward the request
    const headers = new Headers(request.headers);
    headers.set("Host", "api.openai.com");

    const response = await fetch(new Request(url.toString(), {
      method: request.method,
      headers: headers,
      body: request.method === "POST" ? request.body : null,
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
