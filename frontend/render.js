// Pure string renderers: no DOM access, so they run unchanged under node --test.

const ESCAPES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
const TOKEN = /(?<![\w@])@([a-z][a-z0-9_]{2,19})\b|(?<![\w#&])#([A-Za-z][A-Za-z0-9_]{1,29})/g;

export function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, (ch) => ESCAPES[ch]);
}

// Escape the text and turn @mentions and #hashtags into links.
export function linkify(text) {
  let out = "";
  let pos = 0;
  for (const match of text.matchAll(TOKEN)) {
    out += escapeHtml(text.slice(pos, match.index));
    if (match[1]) {
      out += `<a class="mention" href="/profiles/${match[1]}/">@${match[1]}</a>`;
    } else {
      out += `<a class="hashtag" href="/feed/tags/${match[2].toLowerCase()}/">#${match[2]}</a>`;
    }
    pos = match.index + match[0].length;
  }
  return out + escapeHtml(text.slice(pos));
}

export function formatCount(n) {
  if (n < 1000) {
    return String(n);
  }
  if (n < 1_000_000) {
    return `${(n / 1000).toFixed(n < 10_000 ? 1 : 0).replace(/\.0$/, "")}k`;
  }
  return `${(n / 1_000_000).toFixed(1).replace(/\.0$/, "")}m`;
}

// "5m", "3h", "2d" between two ISO timestamps.
export function relativeTime(createdAt, nowIso) {
  const seconds = Math.max(0, Math.floor((Date.parse(nowIso) - Date.parse(createdAt)) / 1000));
  if (seconds < 60) {
    return "now";
  }
  if (seconds < 3600) {
    return `${Math.floor(seconds / 60)}m`;
  }
  if (seconds < 86400) {
    return `${Math.floor(seconds / 3600)}h`;
  }
  return `${Math.floor(seconds / 86400)}d`;
}

export function renderUpdate(item, nowIso) {
  const verified = item.author.verified ? ' <span class="badge">verified</span>' : "";
  const pressed = item.liked ? "true" : "false";
  return [
    `<li class="update" data-id="${item.id}">`,
    `<a class="author" href="/profiles/${item.author.handle}/">${escapeHtml(item.author.display_name)}</a>${verified}`,
    ` <span class="handle">@${item.author.handle}</span>`,
    ` <time datetime="${item.created_at}">${relativeTime(item.created_at, nowIso)}</time>`,
    `<p class="body">${linkify(item.body)}</p>`,
    `<button class="like" data-action="like" data-id="${item.id}" aria-pressed="${pressed}">like ${formatCount(item.likes)}</button>`,
    ` <span class="replies">${formatCount(item.reply_count)} replies</span>`,
    `</li>`,
  ].join("");
}

export function renderTimeline(items, nowIso) {
  if (items.length === 0) {
    return '<p class="empty">Nothing to show yet.</p>';
  }
  return `<ol class="timeline">${items.map((item) => renderUpdate(item, nowIso)).join("")}</ol>`;
}

// Character counter state for the composer.
export function composerState(body, limit) {
  const used = body.trim().length;
  return { used, remaining: limit - used, over: used > limit, canPublish: used > 0 && used <= limit };
}
