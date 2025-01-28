import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { createClient } from "../api.js";
import { engagementReport } from "../consumer_77.js";

const recorded = readFileSync(new URL("./fixtures/timeline.json", import.meta.url), "utf8");

function recordedClient() {
  const fetchImpl = async () => new Response(recorded, { status: 200, headers: { "Content-Type": "application/json" } });
  return createClient({ handle: "marisol", fetchImpl });
}

test("engagementReport totals likes over the recorded timeline", async () => {
  const report = await engagementReport(recordedClient());
  assert.equal(report.posts, 3);
  assert.equal(report.totalLikes, 17);
  assert.equal(report.topId, 9);
});
