import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { ApiError, createClient } from "../api.js";

const fixture = JSON.parse(readFileSync(new URL("./fixtures/timeline.json", import.meta.url), "utf8"));

function recorder(status, payload) {
  const calls = [];
  const fetchImpl = async (url, init) => {
    calls.push({ url, init });
    return new Response(JSON.stringify(payload), { status, headers: { "Content-Type": "application/json" } });
  };
  return { calls, fetchImpl };
}

test("a handle is required", () => {
  assert.throws(() => createClient({ fetchImpl: async () => null }), /handle/);
});

test("timeline sends the handle header and maps the cursor", async () => {
  const { calls, fetchImpl } = recorder(200, fixture);
  const client = createClient({ handle: "marisol", fetchImpl, now: "2025-03-03T12:00:00" });
  const page = await client.timeline("abc");
  assert.equal(page.items.length, 3);
  assert.equal(page.nextCursor, fixture.next_cursor);
  assert.equal(calls[0].init.headers["X-Handle"], "marisol");
  assert.equal(calls[0].init.method, "GET");
  const url = new URL(calls[0].url, "http://pulse.invalid");
  assert.equal(url.pathname, "/feed/timeline/");
  assert.equal(url.searchParams.get("cursor"), "abc");
  assert.equal(url.searchParams.get("now"), "2025-03-03T12:00:00");
});

test("publish posts a JSON body and includes the parent only for replies", async () => {
  const { calls, fetchImpl } = recorder(201, fixture.items[0]);
  const client = createClient({ handle: "marisol", fetchImpl, baseUrl: "http://pulse.invalid" });
  await client.publish("hello");
  await client.publish("a reply", 11);
  assert.deepEqual(JSON.parse(calls[0].init.body), { body: "hello" });
  assert.deepEqual(JSON.parse(calls[1].init.body), { body: "a reply", parent: 11 });
  assert.equal(calls[0].url, "http://pulse.invalid/feed/publish/");
  assert.equal(calls[0].init.headers["Content-Type"], "application/json");
});

test("like and unlike use POST and DELETE on the same path", async () => {
  const { calls, fetchImpl } = recorder(200, fixture.items[1]);
  const client = createClient({ handle: "marisol", fetchImpl });
  await client.like(9);
  await client.unlike(9);
  assert.deepEqual(calls.map((c) => [c.init.method, c.url]), [["POST", "/feed/9/like/"], ["DELETE", "/feed/9/like/"]]);
});

test("error responses become ApiError with the status and code", async () => {
  const { fetchImpl } = recorder(429, { error: "daily_limit" });
  const client = createClient({ handle: "marisol", fetchImpl });
  await assert.rejects(client.publish("again"), (err) => {
    assert.ok(err instanceof ApiError);
    assert.equal(err.status, 429);
    assert.equal(err.code, "daily_limit");
    return true;
  });
});

test("trending unwraps the tag list", async () => {
  const { fetchImpl } = recorder(200, { tags: [{ tag: "lakeside", count: 51 }] });
  const client = createClient({ handle: "marisol", fetchImpl });
  assert.deepEqual(await client.trending(), [{ tag: "lakeside", count: 51 }]);
});
