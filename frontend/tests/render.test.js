import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { composerState, escapeHtml, formatCount, linkify, relativeTime, renderTimeline, renderUpdate } from "../render.js";

const fixture = JSON.parse(readFileSync(new URL("./fixtures/timeline.json", import.meta.url), "utf8"));
const NOW = "2025-03-03T12:00:00+00:00";

test("escapeHtml escapes the five special characters", () => {
  assert.equal(escapeHtml(`<a href="x">'&'</a>`), "&lt;a href=&quot;x&quot;&gt;&#39;&amp;&#39;&lt;/a&gt;");
});

test("linkify links mentions and hashtags and escapes the rest", () => {
  const html = linkify("hi @tobias_k #Lakeside <script>");
  assert.equal(
    html,
    'hi <a class="mention" href="/profiles/tobias_k/">@tobias_k</a> <a class="hashtag" href="/feed/tags/lakeside/">#Lakeside</a> &lt;script&gt;',
  );
});

test("linkify ignores email addresses and entity-looking text", () => {
  assert.equal(linkify("write to a@bcd.example"), "write to a@bcd.example");
  assert.equal(linkify("fish &#x27; chips"), "fish &amp;#x27; chips");
});

test("formatCount abbreviates thousands and millions", () => {
  assert.deepEqual([0, 999, 1000, 1250, 10400, 2_500_000].map(formatCount), ["0", "999", "1k", "1.3k", "10k", "2.5m"]);
});

test("relativeTime picks the largest whole unit", () => {
  assert.equal(relativeTime("2025-03-03T11:59:30+00:00", NOW), "now");
  assert.equal(relativeTime("2025-03-03T11:30:00+00:00", NOW), "30m");
  assert.equal(relativeTime("2025-03-03T09:00:00+00:00", NOW), "3h");
  assert.equal(relativeTime("2025-03-01T12:00:00+00:00", NOW), "2d");
});

test("renderUpdate shows the author, counts and the pressed state", () => {
  const html = renderUpdate(fixture.items[1], NOW);
  assert.match(html, /data-id="9"/);
  assert.match(html, /Tobias Kern/);
  assert.match(html, /aria-pressed="true"/);
  assert.match(html, /like 12/);
  assert.match(html, /0 replies/);
  assert.doesNotMatch(html, /verified/);
});

test("renderUpdate abbreviates large like counts", () => {
  const html = renderUpdate({ ...fixture.items[1], likes: 1500 }, NOW);
  assert.match(html, /like 1\.5k/);
});

test("renderUpdate neutralises markup in bodies", () => {
  const html = renderUpdate(fixture.items[0], NOW);
  assert.match(html, /&lt;b&gt;muddy&lt;\/b&gt;/);
  assert.doesNotMatch(html, /<b>/);
  assert.match(html, /class="badge">verified/);
});

test("renderTimeline lists every item or an empty message", () => {
  assert.equal((renderTimeline(fixture.items, NOW).match(/class="update"/g) || []).length, 3);
  assert.match(renderTimeline([], NOW), /Nothing to show yet/);
});

test("composerState counts trimmed characters against the limit", () => {
  assert.deepEqual(composerState("  hello ", 10), { used: 5, remaining: 5, over: false, canPublish: true });
  assert.equal(composerState("   ", 10).canPublish, false);
  assert.deepEqual(composerState("x".repeat(11), 10), { used: 11, remaining: -1, over: true, canPublish: false });
});
