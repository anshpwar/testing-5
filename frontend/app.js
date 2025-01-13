// Timeline controller. It owns the state and delegates all network access to the client it is given.
import { composerState, renderTimeline } from "./render.js";

export function createApp({ client, root, nowIso, limits = null }) {
  const state = { items: [], nextCursor: null, error: null, limits };

  function render() {
    const more = state.nextCursor ? '<button class="more" data-action="more">Older updates</button>' : "";
    const problem = state.error ? `<p class="error">${state.error}</p>` : "";
    root.innerHTML = problem + renderTimeline(state.items, nowIso()) + more;
  }

  async function guarded(work) {
    try {
      state.error = null;
      await work();
    } catch (err) {
      state.error = err.code ?? "network_error";
    }
    render();
  }

  async function load() {
    await guarded(async () => {
      const page = await client.timeline();
      state.items = page.items;
      state.nextCursor = page.nextCursor;
      if (state.limits === null) {
        state.limits = await client.limits();
      }
    });
  }

  async function loadMore() {
    if (!state.nextCursor) {
      return;
    }
    await guarded(async () => {
      const page = await client.timeline(state.nextCursor);
      state.items = state.items.concat(page.items);
      state.nextCursor = page.nextCursor;
    });
  }

  async function publish(text) {
    const check = composerState(text, state.limits ? state.limits.post_length : Infinity);
    if (!check.canPublish) {
      state.error = check.over ? "too_long" : "empty";
      render();
      return false;
    }
    await guarded(async () => {
      state.items = [await client.publish(text.trim()), ...state.items];
    });
    return state.error === null;
  }

  async function toggleLike(id) {
    const current = state.items.find((item) => item.id === id);
    if (!current) {
      return;
    }
    await guarded(async () => {
      const updated = await (current.liked ? client.unlike(id) : client.like(id));
      state.items = state.items.map((item) => (item.id === id ? updated : item));
    });
  }

  // Click delegation: the root element carries one listener.
  async function handleClick(event) {
    const { action, id } = event.target.dataset ?? {};
    if (action === "like") {
      await toggleLike(Number(id));
    } else if (action === "more") {
      await loadMore();
    }
  }

  return { state, render, load, loadMore, publish, toggleLike, handleClick };
}
