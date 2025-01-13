import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { createApp } from "../app.js";

const fixture = JSON.parse(readFileSync(new URL("./fixtures/timeline.json", import.meta.url), "utf8"));
const NOW = () => "2025-03-03T12:00:00+00:00";

function fakeClient(overrides = {}) {
  const log = [];
  const client = {
    async timeline(cursor = null) {
      log.push(["timeline", cursor]);
      return cursor ? { items: [], nextCursor: null } : { items: structuredClone(fixture.items), nextCursor: fixture.next_cursor };
    },
    async limits() {
      log.push(["limits"]);
      return { post_length: 20 };
    },
    async publish(text) {
      log.push(["publish", text]);
      return { ...structuredClone(fixture.items[2]), id: 99, body: text };
    },
    async like(id) {
      log.push(["like", id]);
      return { ...structuredClone(fixture.items.find((i) => i.id === id)), liked: true };
    },
    async unlike(id) {
      log.push(["unlike", id]);
      return { ...structuredClone(fixture.items.find((i) => i.id === id)), liked: false };
    },
    ...overrides,
  };
  return { client, log };
}

function setup(overrides) {
  const { client, log } = fakeClient(overrides);
  const root = { innerHTML: "" };
  return { app: createApp({ client, root, nowIso: NOW }), root, log };
}

test("load renders the timeline and fetches limits once", async () => {
  const { app, root, log } = setup();
  await app.load();
  await app.load();
  assert.equal(app.state.items.length, 3);
  assert.equal(app.state.limits.post_length, 20);
  assert.equal(log.filter(([name]) => name === "limits").length, 1);
  assert.match(root.innerHTML, /data-action="more"/);
});

test("loadMore appends the next page and clears the cursor", async () => {
  const { app, root } = setup();
  await app.load();
  await app.loadMore();
  assert.equal(app.state.nextCursor, null);
  assert.doesNotMatch(root.innerHTML, /data-action="more"/);
});

test("publish checks the composer limit before calling the client", async () => {
  const { app, log } = setup();
  await app.load();
  assert.equal(await app.publish("x".repeat(21)), false);
  assert.equal(app.state.error, "too_long");
  assert.equal(await app.publish("   "), false);
  assert.equal(app.state.error, "empty");
  assert.equal(log.some(([name]) => name === "publish"), false);
});

test("publish puts the new update first", async () => {
  const { app, root } = setup();
  await app.load();
  assert.equal(await app.publish("  fresh news "), true);
  assert.equal(app.state.items[0].id, 99);
  assert.match(root.innerHTML, /fresh news/);
});

test("toggleLike calls like or unlike depending on the current state", async () => {
  const { app, log } = setup();
  await app.load();
  await app.toggleLike(11);
  await app.toggleLike(9);
  assert.deepEqual(log.filter(([name]) => name === "like" || name === "unlike"), [["like", 11], ["unlike", 9]]);
  assert.equal(app.state.items.find((i) => i.id === 11).liked, true);
  assert.equal(app.state.items.find((i) => i.id === 9).liked, false);
});

test("client errors are shown and do not clear the timeline", async () => {
  const failing = Object.assign(new Error("boom"), { code: "daily_limit" });
  const { app, root } = setup({ async publish() { throw failing; } });
  await app.load();
  assert.equal(await app.publish("hello"), false);
  assert.equal(app.state.error, "daily_limit");
  assert.match(root.innerHTML, /class="error">daily_limit/);
  assert.equal(app.state.items.length, 3);
});

test("handleClick routes like and more buttons", async () => {
  const { app, log } = setup();
  await app.load();
  await app.handleClick({ target: { dataset: { action: "like", id: "11" } } });
  await app.handleClick({ target: { dataset: { action: "more" } } });
  await app.handleClick({ target: {} });
  assert.deepEqual(log.filter(([name]) => name !== "limits").map(([name]) => name), ["timeline", "like", "timeline"]);
});
