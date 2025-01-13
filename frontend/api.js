// Thin client for the Pulse JSON API. Everything goes through one request() so errors look the same.

export class ApiError extends Error {
  constructor(status, code, detail = "") {
    super(detail ? `${code}: ${detail}` : code);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

export function createClient({ baseUrl = "", fetchImpl = globalThis.fetch, handle, now = null } = {}) {
  if (!handle) {
    throw new Error("a handle is required");
  }

  async function request(method, path, { query = {}, body } = {}) {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== null && value !== undefined) {
        params.set(key, value);
      }
    }
    if (now) {
      params.set("now", now);
    }
    const qs = params.toString();
    const init = { method, headers: { "X-Handle": handle, Accept: "application/json" } };
    if (body !== undefined) {
      init.headers["Content-Type"] = "application/json";
      init.body = JSON.stringify(body);
    }
    const response = await fetchImpl(`${baseUrl}${path}${qs ? `?${qs}` : ""}`, init);
    const payload = await response.json();
    if (!response.ok) {
      throw new ApiError(response.status, payload.error ?? "unknown_error", payload.detail ?? "");
    }
    return payload;
  }

  return {
    async timeline(cursor = null) {
      const data = await request("GET", "/feed/timeline/", { query: { cursor } });
      return { items: data.items, nextCursor: data.next_cursor };
    },
    publish(text, parent = null) {
      return request("POST", "/feed/publish/", { body: parent === null ? { body: text } : { body: text, parent } });
    },
    like(id) {
      return request("POST", `/feed/${id}/like/`);
    },
    unlike(id) {
      return request("DELETE", `/feed/${id}/like/`);
    },
    follow(target) {
      return request("POST", `/follows/${target}/`);
    },
    unfollow(target) {
      return request("DELETE", `/follows/${target}/`);
    },
    limits() {
      return request("GET", "/profiles/me/limits/");
    },
    async trending() {
      return (await request("GET", "/feed/trending/")).tags;
    },
  };
}
