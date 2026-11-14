'use strict';

// Keep unchanged message nodes connected: playback, selection and focus survive
// status changes. Only the latest page is mounted until older records are needed.
window.ChatBotTimeline = Object.freeze({
  mount({ el, button, messageNode, historyControl, emptyState, available }) {
    const states = new WeakMap(), pageSize = 200;
    const signatureOf = value => JSON.stringify(value, (_key, item) => item && typeof item === 'object' && !Array.isArray(item)
      ? Object.fromEntries(Object.keys(item).sort().map(key => [key, item[key]])) : item);
    function update(host, session, force = false) {
      const messages = session?.messages || [], id = session?.id || '';
      let state = states.get(host);
      const same = state?.id === id;
      const atEnd = host.scrollHeight - host.scrollTop - host.clientHeight < 45;
      if (!same) {
        if (!state) host.addEventListener('scroll', () => {
          const current = states.get(host);
          if (current) {
            if (host.scrollHeight - host.scrollTop - host.clientHeight < 45) current.followEnd = true;
            else if (host.scrollTop < current.lastTop - 1) current.followEnd = false;
            // Font/image layout can grow the range before the scroll event is
            // delivered. Growth alone must not be mistaken for reading history.
            current.lastTop = host.scrollTop;
          }
        }, { passive: true });
        state?.observer?.disconnect();
        state = { id, limit: pageSize, total: 0, nodes: new Map(), historyKey: null, followEnd: true, lastTop: 0 };
        states.set(host, state);
        const owned = state;
        state.observer = new ResizeObserver(() => {
          if (owned.followEnd) host.scrollTop = host.scrollHeight;
        });
      } else if (!atEnd && messages.length > state.total) {
        state.limit += messages.length - state.total;
      }
      state.total = messages.length;
      const hit = session?.highlight_message_id;
      if (hit !== undefined && hit !== null) {
        const index = messages.findIndex(message => String(message.id) === String(hit));
        if (index >= 0) state.limit = Math.max(state.limit, messages.length - index);
      }
      const start = Math.max(0, messages.length - state.limit), desired = [], nextNodes = new Map();
      host.dataset.session = id;
      if (messages.length) {
        if (start > 0) {
          const more = button(`显示更早的 ${Math.min(pageSize, start)} 条 · 还有 ${start} 条`, 'clock', () => {
            const top = host.scrollTop, height = host.scrollHeight;
            state.limit += pageSize;
            update(host, session);
            host.scrollTop = top + host.scrollHeight - height;
          }, 'small ghost timeline-more');
          desired.push(more);
        } else {
          const historyKey = JSON.stringify([session.context_window, session.source, session.next_cursor, session.has_more]);
          if (!state.history || force || historyKey !== state.historyKey) {
            state.history = historyControl(session);
            state.historyKey = historyKey;
          }
          desired.push(state.history);
        }
        const occurrences = new Map();
        for (let index = start; index < messages.length; index++) {
          const message = messages[index], raw = String(message.id ?? `index:${index}`);
          const occurrence = occurrences.get(raw) || 0;
          occurrences.set(raw, occurrence + 1);
          const key = `${raw}:${occurrence}`;
          const signature = signatureOf([message, session.title, session.source, available()]);
          let cached = state.nodes.get(key);
          if (!cached || cached.signature !== signature || (force && message.emoji_md5)) {
            cached = { signature, node: messageNode(message, session) };
          }
          cached.node.classList.toggle('message-latest', index === messages.length - 1);
          cached.node.classList.toggle('message-hit', hit != null && String(message.id) === String(hit));
          desired.push(cached.node);
          nextNodes.set(key, cached);
        }
      } else desired.push(emptyState());
      const keep = new Set(desired);
      // Remove only dropped records. Insertion before stable siblings avoids
      // detaching unrelated audio elements from the live document.
      for (const child of [...host.children]) if (!keep.has(child)) { state.observer.unobserve(child); child.remove(); }
      let cursor = host.firstChild;
      for (const node of desired) {
        if (cursor === node) cursor = cursor.nextSibling;
        else { host.insertBefore(node, cursor); state.observer.observe(node); }
      }
      state.nodes = nextNodes;
    }
    return Object.freeze({ update });
  }
});
