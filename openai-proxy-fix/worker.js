// OpenAI proxy that connects through US Cloudflare edge
const OPENAI_HOST = "api.openai.com";

export default {
  async fetch(request, env, ctx) {
    // Handle CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
          "Access-Control-Allow-Headers": "*",
          "Access-Control-Max-Age": "86400",
        },
      });
    }

    const url = new URL(request.url);
    const targetUrl = `https://${OPENAI_HOST}${url.pathname}${url.search}`;

    // Build new headers — set Host to openai
    const headers = new Headers(request.headers);
    headers.set("Host", OPENAI_HOST);

    const init = {
      method: request.method,
      headers,
      // Tell Cloudflare to connect directly to the origin IP
      // and treat the request as if it came from a US edge
      cf: {
        // Disable caching
        cacheTtl: 0,
        cacheEverything: false,
      },
    };

    if (request.method !== "GET" && request.method !== "HEAD") {
      init.body = request.body;
      init.duplex = "half";
    }

    try {
      const response = await fetch(targetUrl, init);
      const responseHeaders = new Headers(response.headers);
      responseHeaders.set("Access-Control-Allow-Origin", "*");
      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: responseHeaders,
      });
    } catch (err) {
      return new Response(JSON.stringify({ error: { message: err.message } }), {
        status: 502,
        headers: { "Content-Type": "application/json" },
      });
    }
  },
};
