// Engagement summary built on the timeline client (added independently of the API change, scenario 77).

export async function engagementReport(client) {
  const { items } = await client.timeline();
  const totalLikes = items.reduce((sum, item) => sum + item.like_count, 0);
  const top = items.reduce((best, item) => (best === null || item.like_count > best.like_count ? item : best), null);
  return { posts: items.length, totalLikes, topId: top === null ? null : top.id };
}
