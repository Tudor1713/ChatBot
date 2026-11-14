'use strict';

/* All conversation and model output is inserted with textContent. The only
   innerHTML used below is our fixed, local SVG icon dictionary. */
(() => {
  const $ = (selector, root = document) => root.querySelector(selector);
  const el = (tag, cls, text) => { const n = document.createElement(tag); if (cls) n.className = cls; if (text !== undefined && text !== null) n.textContent = String(text); return n; };
  const append = (node, ...children) => { children.flat(Infinity).forEach(c => { if (c !== null && c !== undefined && c !== false) node.append(typeof c === 'string' ? document.createTextNode(c) : c); }); return node; };
  const paths = {
    chat: '<path d="M5 5h14v11H9l-4 4V5Z"/><path d="M9 9h6M9 12h4"/>',
    book: '<path d="M4 4h7a3 3 0 0 1 3 3v13a4 4 0 0 0-4-2H4V4Zm16 0h-3a3 3 0 0 0-3 3"/><path d="M20 4v14h-2M7 8h4M7 11h4"/>',
    people: '<circle cx="9" cy="8" r="3"/><path d="M3 20v-3a6 6 0 0 1 12 0v3M16 5a3 3 0 0 1 0 6M18 14a5 5 0 0 1 3 5"/>',
    settings: '<path d="M4 7h7m5 0h4M4 17h3m5 0h8"/><circle cx="14" cy="7" r="3"/><circle cx="10" cy="17" r="3"/>',
    compact: '<rect x="3" y="4" width="18" height="16" rx="2"/><rect x="12" y="11" width="9" height="9" rx="1.5"/>',
    expand: '<path d="M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5M3 3l6 6m12-6-6 6M3 21l6-6m12 6-6-6"/>',
    play: '<path d="m8 5 11 7-11 7V5Z"/>', pause: '<path d="M8 5v14M16 5v14"/>',
    pulse: '<path d="M3 12h4l3-8 4 16 3-8h4"/>',
    arrow: '<path d="M5 12h14m-5-5 5 5-5 5"/>',
    refresh: '<path d="M20 7v5h-5M4 17v-5h5"/><path d="M6 7a7 7 0 0 1 12-1l2 6M4 12l2 6a7 7 0 0 0 12-1"/>',
    copy: '<rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V3H3v13h5"/>',
    fill: '<path d="M13 5H4v15h16v-8M13 11l7-7m-6 0h6v6"/>',
    check: '<path d="m5 12 4 4L19 6"/>', close: '<path d="m6 6 12 12M18 6 6 18"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    edit: '<path d="m15 4 5 5L9 20H4v-5L15 4Z"/><path d="m12 7 5 5"/>',
    trash: '<path d="M4 6h16M9 6V3h6v3M6 6l1 15h10l1-15M10 10v7M14 10v7"/>',
    search: '<circle cx="10" cy="10" r="6"/><path d="m15 15 6 6"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7v.5"/>',
    lock: '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V6a4 4 0 0 1 8 0v4M12 14v3"/>',
    window: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M7 6.5h.01M10 6.5h.01"/>',
    eye: '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
    eyeoff: '<path d="m3 3 18 18M10 5c7-1 12 7 12 7a19 19 0 0 1-4 4M6 6a21 21 0 0 0-4 6s4 7 10 7a11 11 0 0 0 5-1M10 10a3 3 0 0 0 4 4"/>',
    upload: '<path d="M12 16V3m-5 5 5-5 5 5M4 14v7h16v-7"/>',
    folder: '<path d="M3 5h6l2 3h10v12H3V5Z"/>',
    pen: '<path d="M4 20h16M5 16l3-1L19 4l-3-3L5 12v4Z"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 2"/>',
    chevron: '<path d="m7 10 5 5 5-5"/>',
    spark: '<path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5L12 3Z"/>',
    link: '<path d="m9 15 6-6M8 7l2-2a5 5 0 0 1 7 7l-2 2M16 17l-2 2a5 5 0 0 1-7-7l2-2"/>',
    moments: '<circle cx="12" cy="12" r="8"/><path d="m12 4 3 8-3 8m8-8-8 3-8-3m2.3-5.7 5.7 3.2 5.7-3.2m0 11.4L12 14.5l-5.7 3.2"/>',
    image: '<rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8" cy="8" r="1.5"/><path d="m3 17 5-5 4 4 4-6 5 7"/>',
    voice: '<rect x="9" y="3" width="6" height="12" rx="3"/><path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3M9 22h6"/>',
    palette: '<path d="M12 3a9 9 0 1 0 0 18h1a2 2 0 0 0 0-4 2 2 0 0 1 0-4h4a4 4 0 0 0 4-4c0-3-4-6-9-6Z"/><path d="M7 9h.1M10 6h.1M15 6h.1M5.5 13h.1"/>',
    heart: '<path d="M12 20 4.5 12.5A5 5 0 0 1 12 6a5 5 0 0 1 7.5 6.5L12 20Z"/>',
    gear: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z"/>',
    winmin: '<path d="M6.5 12h11"/>',
    winmax: '<rect x="6.5" y="6.5" width="11" height="11" rx="1"/>',
    winrestore: '<path d="M9 9V6.5h8.5V15H15"/><rect x="6.5" y="9" width="8.5" height="8.5" rx="1"/>',
    winclose: '<path d="m7 7 10 10M17 7 7 17"/>',
  };
  function icon(name, size = 18) {
    const s = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    for (const [k, v] of Object.entries({ width: size, height: size, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.5, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'aria-hidden': 'true' })) s.setAttribute(k, v);
    s.innerHTML = paths[name] || paths.info;
    return s;
  }
  const demo = new URLSearchParams(location.search).get('demo') === '1';
  const pending = new Map();
  let bridge = null, counter = 0, page = 'workspace', compact = window.innerWidth <= 640, online = false, search = '', currentState;
  let renderQueued = false, experience = null, workbench = null, relationships = null, lastWorkspaceKey = null;
  let drawerTab = null, lastDrawerKey = null, drawerTimer = null, shell = null, memoryRevision = 0;
  let timelineView = null, drawerReturnFocus = null;
  const drawerTabs = [['settings', '模型'], ['auto-reply', '自动回复'], ['memory', '记忆'], ['appearance', '外观']];
  const blank = () => ({ config: { base_url: '', model_name: '', has_api_key: false, reply_model: '', reply_base_url: '', has_reply_api_key: false, relationship: '朋友', style: '自然简洁', auto_analyze: true, context_limit: 30, save_history: false, always_on_top: false, source: 'ocr', weflow_url: 'http://127.0.0.1:5031', weflow_has_token: false, debounce_ms: 1800 }, status: { capture: 'idle', analysis: 'idle', detail: '等待开始读取微信', last_error: '', source: 'ocr', connected: false }, auto_reply: { enabled: false, paused: false, status: 'off', detail: '', allowlist: [], group_mode: 'mention_only', debounce_seconds: 4, cooldown_seconds: 45, hourly_limit: 8, daily_limit: 40, sent_hour: 0, sent_day: 0, recent: [] }, sessions: [], current_session: null, analysis: null, notes: [], contacts: [], version: '2.6.1' });
  currentState = blank();
  const configured = () => currentState.config.has_api_key && currentState.config.base_url && currentState.config.model_name;
  const live = () => ['live', 'searching'].includes(currentState.status.capture);
  const available = () => online || demo;
  function setState(snapshot) {
    if (!snapshot || typeof snapshot !== 'object') return;
    if (experience?.reconcileSnapshot) snapshot = experience.reconcileSnapshot(snapshot);
    currentState = { ...currentState, ...snapshot, config: { ...currentState.config, ...(snapshot.config || {}) }, status: { ...currentState.status, ...(snapshot.status || {}) } };
    for (const k of ['sessions', 'notes', 'contacts']) if (!Array.isArray(currentState[k])) currentState[k] = [];
    currentState.auto_reply = { ...blank().auto_reply, ...(currentState.auto_reply || {}) };
    if (!Array.isArray(currentState.auto_reply.allowlist)) currentState.auto_reply.allowlist = [];
    if (!Array.isArray(currentState.auto_reply.recent)) currentState.auto_reply.recent = [];
    if (!renderQueued) { renderQueued = true; requestAnimationFrame(() => { renderQueued = false; render(); }); }
  }
  function rpc(method, params = {}) {
    if (demo) return demoRequest(method, params);
    if (!bridge) return Promise.reject(new Error('请通过 ChatBot 桌面快捷方式打开，浏览器预览无法连接微信。'));
    return new Promise((resolve, reject) => {
      const id = String(++counter);
      const timeout = setTimeout(() => { pending.delete(id); reject(new Error('操作等待超时，请检查模型连接或微信窗口后重试。')); }, ['import_chat_records', 'import_moments'].includes(method) ? 600000 : ['work_agent_turn', 'work_agent_test'].includes(method) ? 910000 : method === 'work_agent_attach' ? 120000 : ['run_agent', 'analyze_history', 'chat_persona', 'sync_analysis_archive'].includes(method) ? 210000 : ['analyze', 'test_connection', 'analyze_moment', 'transcribe_voice', 'analyze_image', 'choose_media', 'extract_followups', 'style_learn'].includes(method) ? 180000 : 45000);
      pending.set(id, { resolve, reject, timeout });
      try { bridge.request(JSON.stringify({ id, method, params })); } catch (err) { clearTimeout(timeout); pending.delete(id); reject(err); }
    });
  }
  async function sync() { const snapshot = await rpc('bootstrap'); if (snapshot) setState(snapshot); return snapshot; }
  function errorText(error) { return error && error.message ? error.message : String(error || '操作未完成，请重试。'); }
  function toast(message, level = 'info') {
    const host = $('#toasts');
    for (const existing of host.querySelectorAll('.toast')) if (existing.textContent === String(message)) existing.remove();
    while (host.children.length >= 3) host.firstElementChild.remove();
    const item = append(el('div', `toast${level === 'error' ? ' error' : ''}`), icon(level === 'error' ? 'info' : 'check', 16), el('span', '', message));
    host.append(item);
    setTimeout(() => item.remove(), level === 'error' ? 7000 : 4000);
  }
  function button(text, name, handler, cls = '', disabled = false) {
    const b = el('button', `btn ${cls}`.trim()); b.type = 'button'; b.disabled = disabled;
    if (name) b.append(icon(name, cls.includes('small') ? 13 : 15)); b.append(el('span', '', text));
    b.addEventListener('click', async () => {
      if (!handler || b.disabled) return;
      b.disabled = true; b.setAttribute('aria-busy', 'true');
      try { await handler(b); } catch (err) { toast(errorText(err), 'error'); }
      finally { b.disabled = disabled; b.removeAttribute('aria-busy'); }
    }); return b;
  }
  function iconButton(title, name, handler, cls = '') {
    const b = button('', null, handler, cls); b.className = `icon-button ${cls}`; b.replaceChildren(icon(name, 16)); b.title = title; b.setAttribute('aria-label', title); return b;
  }
  const notice = (text, kind = 'info') => append(el('div', `notice notice-${kind}`), icon('info', 15), el('span', '', text));
  const tag = (text, cls = '') => el('span', `tag ${cls}`, text);
  function formatTime(value) {
    if (!value) return '';
    if (/^\d{1,2}:\d{2}(:\d{2})?$/.test(String(value))) return String(value).slice(0, 5);
    const date = typeof value === 'number' ? new Date(value < 1e12 ? value * 1000 : value) : new Date(value);
    return Number.isNaN(date.getTime()) ? String(value).slice(0, 25) : date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
  }
  function valueText(value, fallback = '暂未提供') {
    if (value === null || value === undefined || value === '') return fallback;
    if (typeof value === 'object') return Object.entries(value).map(([k, v]) => `${k}：${valueText(v, '')}`).join('；');
    return String(value);
  }
  function percentage(value) { if (typeof value !== 'number' || !Number.isFinite(value)) return ''; return `${Math.round(value <= 1 ? value * 100 : value)}%`; }
  // One working surface. Settings, auto-reply and appearance open in a side drawer;
  // retired pages (insights, agent, moments, knowledge…) fall back to the workbench.
  function go(nextPage) {
    if (drawerTabs.some(([id]) => id === nextPage)) { openDrawer(nextPage); return; }
    closeDrawer(); page = 'workspace'; search = ''; render(true); $('#main').scrollTop = 0;
  }
  function openDrawer(tab = 'settings') {
    const drawer = $('#drawer'), scrim = $('#drawer-scrim');
    if (!drawerTab) drawerReturnFocus = document.activeElement === document.body ? $('#settings-button') : document.activeElement;
    clearTimeout(drawerTimer); drawerTab = tab; drawer.hidden = false; scrim.hidden = false; drawer.setAttribute('aria-hidden', 'false');
    renderDrawer(true);
    $('#app').inert = true;
    requestAnimationFrame(() => { drawer.classList.add('open'); scrim.classList.add('open'); drawer.querySelector('button')?.focus(); });
    $('#settings-button').classList.add('active');
  }
  function closeDrawer() {
    if (!drawerTab) return;
    const drawer = $('#drawer'), scrim = $('#drawer-scrim');
    drawerTab = null; lastDrawerKey = null; drawer.classList.remove('open'); scrim.classList.remove('open'); drawer.setAttribute('aria-hidden', 'true');
    $('#settings-button').classList.remove('active');
    $('#app').inert = false;
    (drawerReturnFocus?.isConnected ? drawerReturnFocus : $('#settings-button')).focus();
    drawerTimer = setTimeout(() => { if (!drawerTab) { drawer.hidden = true; scrim.hidden = true; drawer.replaceChildren(); } }, 240);
  }
  function renderDrawer(force = false) {
    if (!drawerTab) return;
    // The model form is never rebuilt behind the user's typing; the other tabs follow live state.
    if (!force && drawerTab === 'settings') return;
    const key = drawerTab === 'auto-reply' ? JSON.stringify({ a: currentState.auto_reply, s: currentState.current_session?.id || null, c: currentState.status.capture })
      : drawerTab === 'appearance' ? JSON.stringify(currentState.appearance || {})
      : drawerTab === 'memory' ? `memory:${memoryRevision}:${currentState.memory_auto}:${JSON.stringify(currentState.my_style || {})}` : 'settings';
    if (!force && key === lastDrawerKey) return;
    const drawer = $('#drawer'), sameTab = drawer.dataset.tab === drawerTab, scroll = sameTab ? $('.drawer-body', drawer)?.scrollTop || 0 : 0;
    const openDetails = sameTab ? [...drawer.querySelectorAll('details[data-fold]')].filter(d => d.open).map(d => d.dataset.fold) : [];
    lastDrawerKey = key; drawer.dataset.tab = drawerTab; drawer.replaceChildren();
    const tabs = el('div', 'drawer-tabs'); tabs.setAttribute('role', 'tablist');
    for (const [id, label] of drawerTabs) {
      if (id === 'auto-reply' && currentState.capabilities?.send === false) continue;
      const b = el('button', `drawer-tab${drawerTab === id ? ' active' : ''}`, label); b.type = 'button'; b.setAttribute('role', 'tab'); b.setAttribute('aria-selected', String(drawerTab === id));
      b.addEventListener('click', () => { if (drawerTab !== id) { drawerTab = id; renderDrawer(true); } }); tabs.append(b);
    }
    const head = append(el('div', 'drawer-head'), el('h2', '', '设置'), iconButton('关闭设置', 'close', closeDrawer));
    const body = el('div', 'drawer-body');
    body.append(drawerTab === 'settings' ? settings() : drawerTab === 'auto-reply' ? experience.renderAutoReply() : drawerTab === 'memory' ? memoryTab() : experience.renderAppearance());
    const c = currentState.config;
    const update = button(currentState.updates?.status === 'available' ? '发现新版本' : '检查更新', 'refresh', showUpdates, 'small ghost');
    update.id = 'check-updates';
    const foot = append(el('div', 'drawer-foot'), el('span', '', `ChatBot ${currentState.version || ''}`), update);
    drawer.append(head, tabs, body, foot);
    for (const d of drawer.querySelectorAll('details[data-fold]')) if (openDetails.includes(d.dataset.fold)) d.open = true;
    body.scrollTop = scroll;
  }
  function heading(title, subtitle, eyebrow, actions = []) {
    return append(el('div', 'page-heading'), append(el('div'), eyebrow ? el('div', 'eyebrow', eyebrow) : null, el('h1', '', title), subtitle ? el('p', 'page-subtitle', subtitle) : null), actions.length ? append(el('div', 'page-heading-actions'), actions) : null);
  }
  function empty(title, desc, name, action) { return append(el('div', 'empty'), append(el('div', 'empty-icon'), icon(name, 24)), el('h3', '', title), el('p', '', desc), action || null); }
  async function action(method, params = {}, success) { const result = await rpc(method, params); if (success) toast(success); await sync(); return result; }
  async function toggleCapture() {
    if (currentState.config.source === 'archive') { experience.openCatalog(); return; } await action(live() ? 'pause_capture' : 'start_capture'); }
  async function toggleCompact() { const enabled = !compact; await rpc('set_compact', { enabled }); compact = enabled; $('#app').classList.toggle('compact', compact); render(true); }
  function statusButton() {
    const b = $('#status-toggle'), status = currentState.status, archive = currentState.config.source === 'archive';
    const analyzing = status.analysis === 'running';
    const labels = { idle: '开始读取', searching: '正在寻找微信', live: '正在读取', waiting: '等待微信', paused: '已暂停', error: '读取异常' };
    const text = analyzing ? '正在分析' : archive ? '选择记录' : labels[status.capture] || '开始读取';
    const kind = analyzing ? 'running' : status.capture === 'live' ? 'live' : status.capture === 'error' ? 'error' : ['searching', 'waiting'].includes(status.capture) ? 'waiting' : 'paused';
    b.className = `tb-pill tb-status ${kind}`; b.disabled = !available();
    b.replaceChildren(analyzing ? bars() : el('i', 'tb-dot'), el('span', '', text));
    b.title = archive ? '选择要分析的聊天记录' : live() ? `${status.detail || '正在读取微信新消息'}\n点击暂停` : `${status.detail || '读取已暂停'}\n点击开始读取微信新消息`;
    b.setAttribute('aria-label', b.title.replace('\n', '，'));
  }
  function autoReplyPill() {
    const b = $('#auto-reply-pill'), a = currentState.auto_reply || {};
    const visible = currentState.capabilities?.send !== false && (a.enabled || a.status === 'emergency');
    b.hidden = !visible; if (!visible) return;
    const count = a.allowlist?.length || 0;
    const [text, kind] = a.status === 'emergency' ? ['自动回复已停止', 'error'] : a.status === 'blocked' ? ['自动回复等待微信', 'waiting'] : a.paused ? ['自动回复已暂停', 'paused'] : [`自动回复 · ${count} 个会话`, 'running'];
    b.className = `tb-pill tb-auto ${kind}`; b.replaceChildren(el('i', 'tb-dot'), el('span', '', text));
    b.title = `${a.detail || text}\n点击管理自动回复`;
  }
  function renderChrome() {
    experience?.updateState(currentState);
    statusButton(); autoReplyPill();
    const update = $('#check-updates');
    if (update) update.textContent = currentState.updates?.status === 'available' ? `发现新版本 ${currentState.updates.version}` : '检查更新';
    $('#demo-label').hidden = !demo;
    $('#app').classList.toggle('compact', compact);
    const compactButton = $('#compact-button'); compactButton.classList.toggle('active', compact);
    compactButton.title = compact ? '回到完整工作台' : '悬浮小窗'; compactButton.setAttribute('aria-label', compactButton.title);
  }
  function render(force = false) {
    renderChrome();
    renderDrawer(force);
    const workspaceKey = JSON.stringify({ compact, configured: Boolean(configured()), source: currentState.config.source, session: currentState.current_session, analysis: currentState.analysis, capture: currentState.status.capture, analyzing: currentState.status.analysis, error: currentState.status.last_error, auto: currentState.auto_reply, memory: currentState.memory_count, history: currentState.reply_history_count, profile: currentState.session_profile, due: currentState.analysis_due_at });
    // Catalog warming/import progress must not rebuild chat bubbles or interrupt audio.
    if (!force && workspaceKey === lastWorkspaceKey) return;
    const main = $('#main'); const oldScroll = main.scrollTop;
    const timeline = $('.timeline'); const oldTimeline = timeline ? { top: timeline.scrollTop, end: timeline.scrollHeight - timeline.scrollTop - timeline.clientHeight < 45, session: timeline.dataset.session } : null;
    const assist = $('.assistant-panel'); const assistScroll = assist?.scrollTop || 0;
    const active = document.activeElement;
    const draftFocus = active?.matches('.regen-row input') ? { start: active.selectionStart, end: active.selectionEnd, direction: active.selectionDirection, session: timeline?.dataset.session } : null;
    const folds = [...main.querySelectorAll('details[data-fold]')].filter(d => d.open).map(d => d.dataset.fold);
    if (configured()) {
      const existing = main.querySelector(':scope > .workspace');
      if (existing) workspace(existing, force);
      else main.replaceChildren(workspace(null, force));
    } else main.replaceChildren(onboarding());
    lastWorkspaceKey = workspaceKey;
    main.scrollTop = oldScroll;
    const nextTimeline = $('.timeline');
    if (nextTimeline) nextTimeline.scrollTop = !oldTimeline || oldTimeline.end || nextTimeline.dataset.session !== oldTimeline.session ? nextTimeline.scrollHeight : oldTimeline.top;
    if (currentState.current_session?.highlight_message_id) requestAnimationFrame(() => $('.message-hit')?.scrollIntoView({ block: 'center' }));
    for (const d of main.querySelectorAll('details[data-fold]')) if (folds.includes(d.dataset.fold)) d.open = true;
    const nextAssist = $('.assistant-panel'); if (nextAssist) nextAssist.scrollTop = assistScroll;
    if (draftFocus && draftFocus.session === currentState.current_session?.id) {
      const input = $('.regen-row input');
      if (input) { input.focus({ preventScroll: true }); input.setSelectionRange(draftFocus.start, draftFocus.end, draftFocus.direction); }
    }
  }
  function sourceLabel(source) { return source === 'archive' ? '本机聊天归档' : source === 'wechat_db' ? '本机微信数据库 · 只读' : source === 'weflow' ? 'WeFlow 本地接口' : source === 'manual' ? '手动提供的对话' : source === 'import' ? '已导入的聊天记录' : source === 'demo' ? '合成演示数据' : '微信窗口 · 本地 OCR'; }
  function workspace(existing = null, force = false) {
    const s = currentState, current = s.current_session, busy = s.status.analysis === 'running';
    const root = existing || el('section', 'page workspace');
    root.querySelector(':scope > .inline-error')?.remove();
    if (s.status.last_error) { const n = notice(s.status.last_error, 'error'); n.classList.add('inline-error'); root.prepend(n); }
    const grid = root.querySelector('.workspace-grid') || el('div', 'workspace-grid');
    const chat = grid.querySelector('.chat-panel') || el('section', 'panel chat-panel'); chat.setAttribute('aria-label', '当前对话');
    const header = append(el('div', 'panel-top'), sessionSwitch(current), append(el('div', 'panel-top-tools'), memoryChip(current), experience.sessionAutoReply(current)));
    const oldHeader = chat.querySelector(':scope > .panel-top');
    if (oldHeader) oldHeader.replaceWith(header); else chat.append(header);
    const timeline = chat.querySelector('.timeline') || el('div', 'timeline');
    timeline.setAttribute('role', 'log'); timeline.setAttribute('aria-label', '聊天记录');
    if (!timelineView) timelineView = window.ChatBotTimeline.mount({ el, button, available,
      historyControl: session => experience.historyControl(session),
      emptyState: () => empty(live() ? '正在等待新消息' : '选一段对话开始', live() ? '微信保持登录即可，新消息会出现在这里。' : '选择一个好友或群聊，ChatBot 会读取最近的聊天。', 'chat', button('选择会话', 'people', () => experience.openCatalog(), 'primary small', !available())),
      messageNode: (message, session) => {
        const node = el('article', `message ${message.side === 'me' ? 'me' : 'other'}`);
        node.dataset.messageId = message.id;
        return append(node, append(el('div', 'message-meta'), el('span', 'sender', message.side === 'me' ? '我' : message.sender_name || message.sender || session.title), el('time', '', formatTime(message.timestamp))), experience.messageContent(message, session));
      }
    });
    timelineView.update(timeline, current, force);
    if (!timeline.parentNode) chat.append(timeline);
    const assistant = el('section', 'assistant-panel'); assistant.setAttribute('aria-label', '判断与回复');
    const analysis = s.analysis?.session_id === current?.id ? s.analysis : null;
    if (compact) assistant.append(append(el('div', 'compact-session'), sessionSwitch(current)));
    assistant.append(judgmentStrip(analysis, current, busy));
    if (analysis?.warning) assistant.append(notice(analysis.warning, 'warn'));
    assistant.append(replies(analysis, current, busy));
    if (!chat.parentNode) grid.append(chat);
    const oldAssistant = grid.querySelector('.assistant-panel');
    if (oldAssistant) oldAssistant.replaceWith(assistant); else grid.append(assistant);
    if (!grid.parentNode) root.append(grid);
    return root;
  }
  function sessionSwitch(current) {
    const s = currentState, windowMeta = s.analysis?.session_id === current?.id ? s.analysis?.context_window || current?.context_window : current?.context_window;
    const caption = !current ? '点击选择好友或群聊' : windowMeta ? (windowMeta.mode === 'latest' ? `最近 ${windowMeta.message_count} 条` : `近 7 天 · ${windowMeta.message_count} 条`) : `${current.messages?.length || 0} 条消息`;
    const b = el('button', 'session-switch'); b.type = 'button'; b.title = '切换会话（Ctrl+K）'; b.disabled = !available();
    append(b, el('span', 'avatar', current?.title?.slice(0, 1) || '笺'), append(el('span', 'session-switch-copy'), append(el('span', 'session-name'), el('span', '', current?.title || '选择会话'), icon('chevron', 14)), el('span', 'session-caption', caption)));
    b.addEventListener('click', () => experience.openCatalog());
    return b;
  }
  function analyzeCurrent(current) { return action('analyze', { session_id: current?.id }); }
  function judgmentStrip(analysis, current, busy) {
    const strip = el('section', `judgment-strip${busy ? ' busy' : ''}`);
    const canAnalyze = available() && current?.messages?.length && !busy;
    const head = el('div', 'judgment-head'), lead = el('div', 'judgment-lead');
    const dueAt = Number(currentState.analysis_due_at) || 0, due = dueAt - Date.now() / 1000 > 4 ? new Date(dueAt * 1000).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) : '';
    if (busy) lead.append(append(el('span', 'judgment-busy'), bars(), el('span', '', '正在理解这段对话…')));
    else if (!analysis && due) lead.append(el('p', 'judgment-intent muted', `对方的消息你还没回，${due} 会自动分析；你先回了就取消。`));
    else if (!analysis) lead.append(el('p', 'judgment-intent muted', current?.messages?.length ? (s => s.config.auto_analyze ? '对方发来新消息时会按设置自动分析。' : '准备好了就点「分析」。')(currentState) : '选择会话后，这里会给出判断和回复建议。'));
    else if (analysis.judgment_available === false) lead.append(el('p', 'judgment-intent muted', '这次没有拿到判断，回复建议仍可使用。'));
    else lead.append(el('p', 'judgment-intent', valueText(analysis.intent, '对方的意图暂不明确')));
    const tools = el('div', 'judgment-tools');
    if (analysis && due && !busy) tools.append(el('span', 'fresh-chip', `${due} 自动分析`));
    else if (analysis?.context_changed && !busy) tools.append(el('span', 'fresh-chip', '有新消息'));
    const again = button(analysis ? '重新分析' : '分析', 'refresh', () => analyzeCurrent(current), `small${analysis?.context_changed || (!analysis && current?.messages?.length) ? ' primary' : ' ghost'}`, !canAnalyze);
    tools.append(again);
    head.append(lead, tools); strip.append(head);
    if (analysis && !busy && analysis.judgment_available !== false) strip.append(judgmentDetails(analysis));
    return strip;
  }
  function judgmentDetails(analysis) {
    const details = el('details', 'judgment-more'); details.dataset.fold = 'judgment';
    details.append(el('summary', '', '为什么这样判断'));
    const content = el('div', 'judgment-list');
    const rows = [['对方需要', valueText(analysis.need, '未返回')], ['建议做法', valueText(analysis.action, '未返回')]];
    if (typeof analysis.should_reply === 'boolean') rows.push(['是否回应', analysis.should_reply ? '适合回应实质内容' : '先少说或先核实']);
    if (analysis.risk !== null && analysis.risk !== undefined && analysis.risk !== '') rows.push(['关系风险', typeof analysis.risk === 'number' ? `${analysis.risk} / 9` : valueText(analysis.risk)]);
    if (analysis.urgency !== null && analysis.urgency !== undefined && analysis.urgency !== '') rows.push(['紧迫程度', valueText(analysis.urgency)]);
    const answers = analysis.answers || {};
    const binary = (key, yes, no) => typeof answers[key]?.noul === 'number' ? `${answers[key].noul >= .5 ? yes : no}（${percentage(answers[key].noul)}）` : null;
    for (const [label, value] of [['字面含义', binary('literal_question', '以字面表达为主', '可能另有含义')], ['紧张缓解', binary('tension_resolved', '已缓解或没有紧张', '仍有紧张感')]]) if (value) rows.push([label, value]);
    for (const [label, value] of rows) content.append(append(el('div', 'judgment-row'), el('span', 'judgment-label', label), el('span', 'judgment-value', value)));
    details.append(content); return details;
  }
  function bars() { return append(el('span', 'activity-bars'), el('i'), el('i'), el('i')); }
  function replies(analysis, session, busy) {
    const section = el('section', 'replies-section');
    const candidates = Array.isArray(analysis?.candidates) ? analysis.candidates : [];
    const historyCount = session?.id ? currentState.reply_history_count || 0 : 0;
    if (historyCount) section.append(append(el('div', 'replies-head'), el('span', 'replies-title', candidates.length ? '这次的建议' : ''),
      button(`之前的回复 · ${historyCount}`, 'clock', () => openReplyHistory(session), 'small ghost', !available())));
    if (!candidates.length) {
      if (busy) { section.append(append(el('div', 'reply-skeletons'), el('div', 'skeleton wide'), el('div', 'skeleton medium'), el('div', 'skeleton wide'))); return section; }
      if (analysis) section.append(empty('这次没有生成回复', analysis.warning || '可以检查模型设置后再分析一次。', 'pen', button('打开模型设置', 'gear', () => openDrawer('settings'), 'small ghost')));
      return section;
    }
    if (busy) section.classList.add('regenerating');
    const ordered = candidates.map((candidate, idx) => ({ candidate, idx }));
    ordered.sort((a, b) => Number(b.idx === analysis.best_index) - Number(a.idx === analysis.best_index));
    const canFill = currentState.capabilities?.send !== false && Boolean(session?.active);
    ordered.forEach(({ idx, candidate }, position) => {
      const best = idx === analysis.best_index, card = el('article', `reply-card${best ? ' best' : ''}`);
      if (candidate.reason) card.title = candidate.reason;
      card.append(append(el('div', 'reply-number'), el('span', 'reply-index', String(position + 1)), best ? el('b', 'recommendation-label', '推荐') : null));
      card.append(el('p', 'reply-text', candidate.text || ''));
      const copy = button('复制', 'copy', () => action('copy_reply', { text: candidate.text }, '已复制'), 'small ghost', !candidate.text || !available());
      const fill = button('填入微信', 'fill', () => action('fill_reply', { session_id: session.id, index: idx, text: candidate.text }, demo ? '演示模式：未向微信写入内容' : '已填入微信，确认后自己按发送'), `small ${best ? 'primary' : 'ghost'}`, !canFill || !candidate.text || !available());
      if (!canFill) fill.title = '要先在微信里打开这个会话';
      card.append(append(el('div', 'reply-actions'), copy, fill));
      section.append(card);
    });
    section.append(regenerateRow(session, busy));
    section.append(topicDirections(analysis, session));
    return section;
  }
  // 「换一批」：可直接点常用要求，也可以自己写；对话没变时沿用这次的判断，只重写回复。
  const regenDrafts = new Map();
  function regenerateRow(session, busy) {
    const row = el('form', 'regen-row');
    const input = el('input', 'input'); input.maxLength = 120; input.placeholder = '不满意？说说想怎么改（可不填），比如：别提加班的事';
    input.value = regenDrafts.get(session?.id) || ''; input.setAttribute('aria-label', '重新生成的要求');
    input.addEventListener('input', () => regenDrafts.set(session?.id, input.value));
    const run = async text => {
      await rpc('regenerate_replies', { session_id: session.id, instruction: text });
      regenDrafts.delete(session.id);
      toast(text ? `按「${text}」重新写一批…` : '正在换一批…');
      await sync();
    };
    const disabled = busy || !available() || !session?.id;
    const go = button(busy ? '正在生成…' : '换一批', 'refresh', () => run(input.value.trim()), 'small primary', disabled);
    const chips = el('div', 'regen-chips');
    for (const label of ['更短一点', '更热情', '更正式', '幽默一点', '先别答应']) chips.append(button(label, null, () => run(label), 'small ghost', disabled));
    row.append(append(el('div', 'regen-input'), input, go), chips);
    row.addEventListener('submit', e => { e.preventDefault(); go.click(); });
    return row;
  }

  function topicDirections(analysis, session) {
    const area = el('details', 'topic-directions'); area.dataset.fold = 'topics';
    area.append(append(el('summary', ''), el('span', '', '没话聊？换个话题'), el('span', 'subtle-caption', '三个方向')));
    const tabs = el('div', 'topic-tabs'); tabs.setAttribute('role', 'tablist'); tabs.setAttribute('aria-label', '话题方向');
    const content = el('div', 'topic-content');
    const directions = [['missed', '之前遗漏的'], ['their', '对方感兴趣的'], ['mine', '我感兴趣的']];
    const buttons = [];
    const draw = key => {
      buttons.forEach(b => { b.classList.toggle('selected', b.dataset.topicDirection === key); b.setAttribute('aria-selected', String(b.dataset.topicDirection === key)); });
      content.replaceChildren();
      const items = analysis?.topics?.[key] || [];
      if (!items.length) { content.append(el('p', 'subtle-caption', '这次没有找到有依据的话题。')); return; }
      for (const topic of items) {
        const card = el('article', 'topic-card'); card.append(el('h3', '', topic.title), el('p', 'topic-opener', topic.opener));
        card.append(el('p', 'topic-reason', `${topic.grounded ? '聊天依据' : '待确认方向'} · ${topic.reason}`));
        if (topic.evidence_ids?.length) {
          const details = el('details', 'topic-evidence'); details.append(el('summary', '', '查看原消息'));
          for (const id of topic.evidence_ids) {
            const message = topic.evidence?.find(m => String(m.id) === String(id)) || session?.messages?.find(m => String(m.id) === String(id));
            details.append(el('p', '', message ? message.text : '依据来自近 7 天的历史记录。'));
          }
          card.append(details);
        }
        card.append(button('复制开场白', 'copy', () => action('copy_reply', { text: topic.opener }, '已复制开场白'), 'small ghost', !available()));
        content.append(card);
      }
    };
    for (const [key, label] of directions) {
      const b = button(label, null, () => draw(key), 'topic-tab'); b.dataset.topicDirection = key; b.setAttribute('role', 'tab'); buttons.push(b); tabs.append(b);
    }
    area.append(tabs, content); draw('missed'); return area;
  }

  // ---- 记忆 ------------------------------------------------------------------
  function memoryChip(current) {
    if (!current?.id || current.source === 'manual') return null;
    const n = currentState.memory_count || 0, goal = currentState.session_profile?.goal || '';
    const b = el('button', `session-memory${n || goal ? ' has' : ''}`); b.type = 'button'; b.disabled = !available();
    b.title = goal ? `聊天目的：${goal}\n点击修改目的、背景和记忆` : `给「${current.title}」设定聊天目的、补充背景和记忆`;
    append(b, icon(goal ? 'spark' : 'book', 14), el('span', '', goal ? `目的：${goal.length > 8 ? goal.slice(0, 8) + '…' : goal}` : n ? `目的与记忆 · ${n}` : '目的与记忆'));
    b.addEventListener('click', () => openMemory(current).catch(err => toast(errorText(err), 'error')));
    return b;
  }
  function sessionProfileForm(session, view, refresh) {
    const profile = view.profile || {}, box = el('div', 'session-profile');
    const goal = el('input', 'input'); goal.maxLength = 200; goal.value = profile.goal || ''; goal.placeholder = '比如：约她周六吃饭 / 催对方确认合同 / 安慰一下她'; goal.setAttribute('aria-label', '聊天目的');
    const context = el('textarea', 'input'); context.rows = 3; context.maxLength = 2000; context.value = profile.context || ''; context.placeholder = 'AI 不知道、但回复时需要知道的：对方是谁、你们之间发生过什么、哪些话别提'; context.setAttribute('aria-label', '补充背景');
    const save = button('保存目的和背景', 'check', async () => {
      await rpc('session_profile_save', { session_id: session.id, goal: goal.value.trim(), context: context.value.trim() });
      toast('已保存；之后的分析和自动回复都会按这个来'); await refresh();
    }, 'small primary', !available());
    box.append(append(el('label', 'field'), el('span', 'field-label', '聊天目的'), goal), append(el('label', 'field'), el('span', 'field-label', '补充背景'), context));
    const scopeAll = view.auto_analyze_scope !== 'selected';
    const auto = toggle('自动分析这个会话', 'session_auto_analyze', scopeAll ? view.auto_analyze : Boolean(profile.auto_analyze),
      !view.auto_analyze ? '设置里的「新消息来了自动分析」现在是关的。' : scopeAll ? '设置里选的是「所有会话」，这个会话已在自动分析范围内。' : '对方来消息后按设置里的等待时间和条数自动分析。');
    const autoInput = auto.querySelector('input'); autoInput.disabled = scopeAll || !available();
    autoInput.addEventListener('change', async () => { try { await rpc('session_profile_save', { session_id: session.id, auto_analyze: autoInput.checked }); await refresh(); } catch (err) { toast(errorText(err), 'error'); } });
    box.append(append(el('div', 'session-profile-actions'), el('span', 'field-hint', '想让 AI 直接替你回，打开会话名旁边的「自动回复」。'), save), auto);
    return box;
  }
  function memoryRows(items, refresh) {
    const list = el('div', 'memory-list');
    if (!items.length) list.append(el('p', 'memory-empty', '还没有记下什么。'));
    for (const item of items) {
      const row = el('div', `memory-item${item.source === 'auto' ? ' auto' : ''}`);
      const text = el('span', 'memory-text', item.text); text.tabIndex = 0; text.title = '点一下就能改';
      const edit = () => {
        const input = el('input', 'input memory-edit'); input.value = item.text; input.maxLength = 120; input.setAttribute('aria-label', '修改这条记忆');
        text.replaceWith(input); input.focus(); input.select();
        let finished = false;
        const done = async save => {
          if (finished) return; finished = true;
          const value = input.value.trim();
          try { if (save && value && value !== item.text) { await rpc('memory_update', { id: item.id, text: value }); memoryRevision++; } } catch (err) { toast(errorText(err), 'error'); }
          await refresh();
        };
        input.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); done(true); } else if (e.key === 'Escape') { e.preventDefault(); done(false); } });
        input.addEventListener('blur', () => done(true));
      };
      text.addEventListener('click', edit); text.addEventListener('keydown', e => { if (e.key === 'Enter') edit(); });
      append(row, text, item.source === 'auto' ? el('span', 'memory-tag', '自动记下') : null,
        iconButton('删除这条记忆', 'close', async () => { await rpc('memory_delete', { id: item.id }); memoryRevision++; await refresh(); }, 'small'));
      list.append(row);
    }
    return list;
  }
  function memoryAdd(sessionId, refresh, placeholder) {
    const form = el('form', 'memory-add'), input = el('input', 'input'); input.maxLength = 120; input.placeholder = placeholder; input.setAttribute('aria-label', placeholder);
    const add = button('记下', 'plus', async () => {
      const text = input.value.trim(); if (!text) { input.focus(); return; }
      await rpc('memory_add', { session_id: sessionId, text }); memoryRevision++; input.value = '';
      await refresh(); requestAnimationFrame(() => document.querySelector(`.memory-add[data-session="${CSS.escape(sessionId)}"] .input`)?.focus());
    }, 'small primary', !available());
    form.dataset.session = sessionId; form.append(input, add);
    form.addEventListener('submit', e => { e.preventDefault(); add.click(); });
    return form;
  }
  function memoryAutoSwitch(enabled, refresh) {
    const row = toggle('聊天时自动记下新信息', 'memory_auto', enabled, '分析对话时，模型发现对方提到的值得记住的事会自动加进来，标着「自动记下」，不对就删掉。');
    const input = row.querySelector('input');
    input.addEventListener('change', async () => { try { await rpc('memory_auto', { enabled: input.checked }); memoryRevision++; await refresh(); } catch (err) { toast(errorText(err), 'error'); } });
    return row;
  }
  async function openMemory(session) {
    if (!session?.id) return;
    const dialog = $('#editor');
    const draw = async () => {
      const view = await rpc('memory_view', { session_id: session.id });
      const scroll = $('.memory-dialog-body', dialog)?.scrollTop || 0;
      // 记忆增删会重画弹窗：没保存的目的/背景草稿要留住。
      const draftGoal = dialog.open ? $('input[aria-label="聊天目的"]', dialog)?.value : undefined;
      const draftContext = dialog.open ? $('textarea[aria-label="补充背景"]', dialog)?.value : undefined;
      if (draftGoal !== undefined) view.profile = { ...(view.profile || {}), goal: draftGoal, context: draftContext ?? view.profile?.context };
      dialog.replaceChildren(); dialog.className = 'dialog memory-dialog';
      const head = append(el('div', 'memory-head'), append(el('div'), el('div', 'eyebrow', '目的与记忆'), el('h2', '', `「${session.title || '对方'}」`)), iconButton('关闭', 'close', () => dialog.close()));
      const body = el('div', 'memory-dialog-body');
      body.append(sessionProfileForm(session, view, refresh), append(el('div', 'memory-section-title'), el('h3', '', '记忆'), el('span', 'field-hint', '分析和回复时参考，不会原样念给对方；点一条可以改。')),
        memoryRows(view.items || [], refresh), memoryAdd(session.id, refresh, '记一条，比如：不吃香菜 / 下个月搬家'), memoryAutoSwitch(view.auto, refresh));
      dialog.append(head, body); body.scrollTop = scroll;
    };
    const refresh = async () => { await draw(); sync().catch(() => {}); };
    await draw(); if (!dialog.open) dialog.showModal();
    requestAnimationFrame(() => { if (document.activeElement?.closest('.memory-head')) document.activeElement.blur(); });
  }
  function styleBlock(refresh) {
    const section = el('section', 'memory-block style-block'), body = el('div', 'style-body');
    section.append(el('h3', '', '我的说话方式'), body);
    const info = currentState.my_style || {};
    const learn = async () => {
      toast('开始学习你的说话方式，大约半分钟…');
      await rpc('style_learn'); memoryRevision++; await sync();
      toast('学好了：之后的回复建议和自动回复都会模仿你的语气');
    };
    if (info.busy) { body.append(append(el('p', 'field-hint style-busy'), bars(), el('span', '', '正在从你的聊天记录里学习…'))); return section; }
    if (!info.learned) {
      body.append(el('p', 'field-hint', '从你最近发过的几百条消息里（只取你自己说的话）总结用词、语气和标点习惯，之后起草回复和自动回复都照着写。这些消息会发给你配置的模型来总结。'),
        button('学习我的说话方式', 'spark', learn, 'small primary', !available()));
      return section;
    }
    rpc('style_get').then(data => {
      const area = el('textarea', 'input style-profile'); area.rows = 8; area.maxLength = 1200; area.value = data.profile || ''; area.setAttribute('aria-label', '我的说话方式');
      const sw = toggle('起草回复和自动回复时模仿我的语气', 'style_enabled', data.enabled);
      sw.querySelector('input').addEventListener('change', async e => { try { await rpc('style_save', { enabled: e.target.checked }); memoryRevision++; await sync(); } catch (err) { toast(errorText(err), 'error'); } });
      body.append(sw, el('p', 'field-hint', `根据你发过的 ${data.sample_count || 0} 条消息总结${data.learned_at ? ' · ' + formatWhen(data.learned_at) : ''}；不准的地方直接改。`), area,
        append(el('div', 'style-actions'), button('保存修改', 'check', async () => { await rpc('style_save', { profile: area.value }); toast('已保存'); }, 'small', !available()), button('重新学习', 'refresh', learn, 'small ghost', !available())));
      if (data.examples?.length) body.append(el('p', 'field-hint style-examples', '你的原话举例：' + data.examples.slice(0, 6).join(' ／ ')));
    }).catch(err => body.append(notice(errorText(err), 'error')));
    return section;
  }
  function memoryTab() {
    const root = el('section', 'page memory-page'), holder = el('div', 'memory-overview');
    root.append(el('p', 'field-hint memory-intro', '记忆只存在这台电脑。分析对话时，ChatBot 会带上关于对方的记忆；手动分析还会带上「关于我」。'), holder);
    const draw = async () => {
      const view = await rpc('memory_overview');
      holder.replaceChildren();
      const mine = el('section', 'memory-block');
      mine.append(el('h3', '', '关于我'), el('p', 'field-hint', '你的近况、习惯、不想被提起的事。自动回复不会用到这部分。'), memoryRows(view.self || [], refresh), memoryAdd('self', refresh, '比如：工作日晚上 8 点后才有空'));
      const people = el('section', 'memory-block'); people.append(el('h3', '', `关于每个人 · ${view.people?.length || 0}`));
      if (!view.people?.length) people.append(el('p', 'memory-empty', '还没有。在工作台打开一个会话，点会话名旁边的「记忆」就能记。'));
      for (const person of view.people || []) {
        const b = el('button', 'memory-person'); b.type = 'button';
        append(b, el('span', 'auto-reply-avatar', (person.title || '笺').slice(0, 1)), append(el('span', 'memory-person-copy'), el('strong', '', person.title), el('span', '', person.preview)), el('span', 'memory-count', String(person.count)));
        b.addEventListener('click', () => openMemory({ id: person.session_id, title: person.title }).catch(err => toast(errorText(err), 'error')));
        people.append(b);
      }
      holder.append(memoryAutoSwitch(view.auto, refresh), mine, styleBlock(refresh), people);
    };
    const refresh = async () => { await draw(); sync().catch(() => {}); };
    draw().catch(err => holder.replaceChildren(notice(errorText(err), 'error')));
    return root;
  }

  // ---- 之前的回复 ------------------------------------------------------------
  function formatWhen(seconds) {
    const date = new Date(Number(seconds) * 1000); if (Number.isNaN(date.getTime())) return '';
    const time = date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }), today = new Date();
    if (date.toDateString() === today.toDateString()) return `今天 ${time}`;
    const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1);
    if (date.toDateString() === yesterday.toDateString()) return `昨天 ${time}`;
    return `${date.getMonth() + 1}月${date.getDate()}日 ${time}`;
  }
  async function openReplyHistory(session) {
    if (!session?.id) return;
    const dialog = $('#editor');
    const draw = async () => {
      const result = await rpc('reply_history', { session_id: session.id }), items = result.items || [];
      dialog.replaceChildren(); dialog.className = 'dialog history-dialog';
      dialog.append(append(el('div', 'memory-head'), append(el('div'), el('div', 'eyebrow', '之前的回复'), el('h2', '', `和「${session.title || '对方'}」`)), iconButton('关闭', 'close', () => dialog.close())));
      const list = el('div', 'history-list');
      if (!items.length) list.append(el('p', 'memory-empty', '还没有记录。每次分析生成的回复建议都会留在这里。'));
      const canFill = currentState.capabilities?.send !== false && Boolean(session.active);
      for (const item of items) {
        const card = el('article', 'history-entry');
        const meta = append(el('div', 'history-meta'), el('time', '', formatWhen(item.at)), item.auto ? el('span', 'memory-tag', '自动回复') : null,
          item.sent ? el('span', 'memory-tag sent', item.sent.status === 'sent' ? '已自动发出' : '已发出，待确认') : null);
        card.append(meta);
        if (item.reply_to) card.append(el('p', 'history-reply-to', `回的是：${item.reply_to}`));
        item.candidates.forEach((text, index) => {
          const sent = item.sent?.text === text, best = index === item.best_index;
          const row = el('div', `history-candidate${best ? ' best' : ''}${sent ? ' sent' : ''}`);
          row.append(el('p', 'reply-text', text));
          const actions = append(el('div', 'reply-actions'), sent ? el('b', 'recommendation-label', '发出的这条') : best ? el('b', 'recommendation-label', '当时推荐') : null,
            button('复制', 'copy', () => action('copy_reply', { text }, '已复制'), 'small ghost', !available()),
            button('填入微信', 'fill', () => action('fill_history_reply', { session_id: session.id, entry_id: item.id, index }, '已填入微信，确认后自己按发送'), 'small ghost', !canFill || !available()));
          row.append(actions); card.append(row);
        });
        list.append(card);
      }
      const foot = el('div', 'dialog-footer');
      if (items.length) foot.append(button('清空这些记录', 'trash', async () => { await rpc('reply_history_clear', { session_id: session.id }); await sync(); await draw(); }, 'small danger'));
      foot.append(button('关闭', null, () => dialog.close()));
      dialog.append(list, foot);
    };
    await draw(); if (!dialog.open) dialog.showModal();
    // 打开时不把焦点放在右上角关闭钮上（红色焦点框看着像报错）；Tab 仍可正常移动。
    requestAnimationFrame(() => { if (document.activeElement?.closest('.memory-head')) document.activeElement.blur(); });
  }

  function field(label, name, value, { type = 'text', placeholder = '', hint = '', optional = false, rows, options } = {}) {
    const wrap = el('div', 'field'), lab = el('label', '', label); lab.htmlFor = name;
    if (optional) lab.append(el('span', 'optional', '选填'));
    let input;
    if (options) { input = el('select', 'input'); for (const [v, t] of options) input.append(new Option(t, v, false, String(value) === String(v))); }
    else { input = el(rows ? 'textarea' : 'input', 'input'); if (!rows) input.type = type; else input.rows = rows; input.value = value ?? ''; input.placeholder = placeholder; }
    input.name = name; input.id = name; input.autocomplete = type === 'password' ? 'new-password' : 'off'; input.spellcheck = false;
    if (type === 'number') { input.min = name === 'context_limit' ? '3' : '400'; input.max = name === 'context_limit' ? '200' : '10000'; input.step = name === 'context_limit' ? '1' : '100'; }
    append(wrap, lab);
    if (type === 'password') {
      const toggle = iconButton('显示密钥', 'eye', () => { input.type = input.type === 'password' ? 'text' : 'password'; toggle.replaceChildren(icon(input.type === 'password' ? 'eye' : 'eyeoff', 16)); toggle.title = input.type === 'password' ? '显示密钥' : '隐藏密钥'; toggle.setAttribute('aria-label', toggle.title); });
      wrap.append(append(el('div', 'input-wrap'), input, toggle));
    } else wrap.append(input);
    if (hint) wrap.append(el('p', 'field-hint', hint));
    return wrap;
  }
  function toggle(label, name, checked, desc) {
    const text = append(el('div', 'switch-copy'), el('div', '', label), desc ? el('p', 'field-hint', desc) : null);
    const l = el('label', 'switch'), input = document.createElement('input'); input.type = 'checkbox'; input.name = name; input.id = name; input.checked = Boolean(checked); input.setAttribute('aria-label', label); append(l, input, el('span', 'switch-track'));
    return append(el('div', 'switch-row'), text, l);
  }
  function primaryFields(form, lean = false) {
    const c = currentState.config;
    form.append(field('API Key', 'api_key', '', { type: 'password', placeholder: c.has_api_key ? '已安全保存，留空保留' : '输入模型服务 API Key', hint: c.has_api_key ? '密钥不会回传到界面。输入新值即可替换。' : '只保存在这台电脑：Windows 使用 DPAPI，macOS 使用钥匙串。' }));
    form.append(field('Base URL', 'base_url', c.base_url, { placeholder: 'https://你的模型服务地址', hint: '填写模型提供方给出的 API 地址。' }));
    form.append(field('Model name', 'model_name', c.model_name, { placeholder: '填写模型名称' }));
    if (currentState.model_profile && !lean) {
      const profile = currentState.model_profile;
      form.append(append(el('div', 'model-profile-receipt'), el('span', '', `${(profile.context_tokens / 10000).toLocaleString()} 万 tokens 上下文`), el('span', '', `思考强度 ${profile.effort} · 模型最高档`), el('span', '', `${profile.max_output_tokens.toLocaleString()} tokens 输出上限（含思考）`)));
    }
  }
  function readConfig(form) {
    const data = new FormData(form), out = {};
    for (const [key, value] of data.entries()) out[key] = String(value).trim();
    form.querySelectorAll('input[type="checkbox"]').forEach(i => { out[i.name] = i.checked; });
    for (const k of ['context_limit', 'debounce_ms', 'auto_analyze_wait', 'auto_analyze_count']) if (k in out) out[k] = Number(out[k]);
    return out;
  }
  function validateConfig(config) {
    if (!config.api_key && !currentState.config.has_api_key) throw new Error('请填写 API Key。');
    if (!config.base_url) throw new Error('请填写 Base URL。');
    let url; try { url = new URL(config.base_url); } catch { throw new Error('Base URL 格式不正确，请填写完整的 http:// 或 https:// 地址。'); }
    if (!['http:', 'https:'].includes(url.protocol)) throw new Error('Base URL 必须使用 http:// 或 https://。');
    if (!config.model_name) throw new Error('请填写 Model name。');
    if ('context_limit' in config && (!Number.isInteger(config.context_limit) || config.context_limit < 3 || config.context_limit > 200)) throw new Error('上下文条数需要是 3–200 之间的整数。');
    if ('debounce_ms' in config && (!Number.isFinite(config.debounce_ms) || config.debounce_ms < 400 || config.debounce_ms > 10000)) throw new Error('消息合并等待时间需要在 400–10000 毫秒之间。');
  }
  function formFeedback(form, message, error = false) {
    let f = $('.form-feedback', form); if (!f) { f = el('div', 'form-feedback'); f.setAttribute('role', 'status'); form.append(f); }
    f.className = `form-feedback${error ? ' error' : ''}`; f.textContent = message;
  }
  function configActions(form, onboardingMode = false) {
    const test = button('测试连接', 'link', async () => {
      try { const config = readConfig(form); validateConfig(config); formFeedback(form, '正在验证模型连接，请稍候…'); const result = await rpc('test_connection', { config }); formFeedback(form, result.message || (result.success ? '连接成功' : '连接未通过'), result.success === false); }
      catch (err) { formFeedback(form, errorText(err), true); }
    }, '', !available());
    const save = button(onboardingMode ? '进入工作台' : '保存设置', onboardingMode ? 'arrow' : 'check', async () => {
      try { const config = readConfig(form); validateConfig(config); await rpc('save_config', { config }); await sync(); for (const field of form.querySelectorAll('input[type="password"]')) field.value = ''; toast('模型设置已保存'); go(onboardingMode ? 'workspace' : 'settings'); }
      catch (err) { formFeedback(form, errorText(err), true); }
    }, 'primary', !available());
    form.append(append(el('div', 'form-actions'), test, save));
    form.addEventListener('submit', e => { e.preventDefault(); save.click(); });
  }
  function onboarding() {
    const root = el('section', 'onboarding');
    const copy = el('div', 'welcome-copy');
    copy.append(append(el('div', 'welcome-wordmark'), icon('pulse', 21), el('span', '', 'ChatBot')));
    const title = el('h1'); append(title, '微信里的对话，', document.createElement('br'), el('em', '', '有 ChatBot 一起斟酌。')); copy.append(title);
    copy.append(el('p', 'welcome-intro', '在电脑端读取对话、理解沟通意图，获得有依据的回复建议。只填三项模型配置，即可开始。'));
    const steps = el('div', 'welcome-steps');
    for (const [n, text] of [['01', '接入你自己的模型服务'], ['02', '导入完整记录，选择客户会话'], ['03', '分析、核对证据并确认下一步行动']]) steps.append(append(el('div', 'welcome-step'), el('span', 'step-number', n), el('span', '', text)));
    copy.append(steps);
    const form = el('form', 'welcome-form'); form.id = 'onboarding-form'; form.autocomplete = 'off'; form.append(el('div', 'eyebrow', '第一次见面'), el('h2', '', '三项配置，就此开始'), el('p', 'form-description', '使用你自己的模型服务。保存后，随时可以在设置中调整。')); primaryFields(form); configActions(form, true);
    form.append(append(el('div', 'privacy-caption'), icon('lock', 12), el('span', '', '仅将选中的对话上下文和相关背景发往你配置的 API。本地历史默认关闭，候选回复不会自动发送到微信。')));
    return append(root, copy, form);
  }
  function autoAnalysisFields(c) {
    const box = el('div', 'auto-analysis-box');
    box.append(toggle('新消息来了自动分析', 'auto_analyze', c.auto_analyze, '自动分析只给出判断和回复建议，不会替你发送。'));
    box.append(append(el('div', 'form-two'),
      field('分析哪些会话', 'auto_analyze_scope', c.auto_analyze_scope || 'all', { options: [['all', '所有会话'], ['selected', '只分析我选的会话']] }),
      field('先等我回复', 'auto_analyze_wait', c.auto_analyze_wait ?? 0, { options: [[0, '不等，马上分析'], [30, '等 30 秒'], [60, '等 1 分钟'], [120, '等 2 分钟'], [300, '等 5 分钟'], [600, '等 10 分钟'], [1800, '等 30 分钟']] })));
    box.append(field('对方连发几条就直接分析', 'auto_analyze_count', c.auto_analyze_count ?? 0, { options: [[0, '不按条数'], [2, '2 条'], [3, '3 条'], [5, '5 条'], [10, '10 条']], hint: '对方来消息后，等这么久你还没回才分析；你回了就取消。等待期间对方连发到这个条数，就不再等。' }));
    if ((c.auto_analyze_scope || 'all') === 'selected') {
      const chosen = currentState.auto_analyze_selected || [];
      box.append(el('p', 'field-hint auto-analysis-chosen', chosen.length ? `已选 ${chosen.length} 个：${chosen.map(s => s.title).join('、')}` : '还没选会话：在工作台打开一个会话，点会话名旁边的「目的与记忆」，打开「自动分析这个会话」。'));
    }
    return box;
  }
  function settings() {
    const root = el('section', 'page settings-page');
    const form = el('form', 'settings-form'); form.id = 'config-form'; form.autocomplete = 'off';
    const c = currentState.config;
    form.append(el('h3', 'settings-group-title', '模型连接')); primaryFields(form, true);
    form.append(el('h3', 'settings-group-title', '自动分析'), autoAnalysisFields(c));
    form.append(el('h3', 'settings-group-title', '常用'),
      toggle('自动检查版本更新', 'updates_auto', c.updates_auto !== false, '启动后和使用期间检查 GitHub 正式发布版，有新版时提示。'),
      toggle('自动识别表情', 'stickers_auto', c.stickers_auto !== false, '收到表情时把表情图交给上面的模型看，换成一句话的意思；同一个表情只看一次。'),
      toggle('窗口保持置顶', 'always_on_top', c.always_on_top));
    const advanced = el('details', 'advanced'); advanced.dataset.fold = 'advanced'; advanced.append(el('summary', '', '更多选项'));
    const body = el('div', 'advanced-body');
    const source = el('section', 'advanced-section'); source.append(el('h3', '', '消息读取'));
    source.append(field('读取来源', 'source', c.source === 'auto' ? 'ocr' : c.source, { options: [['archive', '主动导入的聊天归档'], ...(currentState.capabilities?.native_capture === false ? [] : [['ocr', '微信可见窗口（本地 OCR）']]), ...(currentState.capabilities?.native_database === false ? [] : [['wechat_db', '本机微信数据库（推荐）']]), ['weflow', '已有 WeFlow 本地服务']] }), el('p', 'field-hint', '本机数据库：微信保持登录即可，窗口最小化或收进托盘也能读到新消息。'));
    source.append(field('WeFlow 地址', 'weflow_url', c.weflow_url, { optional: true, placeholder: 'http://127.0.0.1:5031' }), field('WeFlow 访问令牌', 'weflow_token', '', { type: 'password', optional: true, placeholder: c.weflow_has_token ? '已保存，留空保留' : '仅当你的服务需要验证时填写' }));
    source.append(button('检查读取来源', 'refresh', async () => { const result = await rpc('refresh_sources'); const sources = Array.isArray(result) ? result : result?.sources; if (sources?.length) toast(sources.map(s => typeof s === 'string' ? s : s.title || s.name || s.source || '已发现来源').join('；')); else toast(typeof result?.message === 'string' ? result.message : '已刷新来源，请检查所选数据源。'); }, 'small', !available()));
    const behavior = el('section', 'advanced-section'); behavior.append(el('h3', '', '分析与表达'));
    behavior.append(append(el('div', 'form-two'), field('默认关系', 'relationship', c.relationship, { placeholder: '朋友 / 同事 / 客户' }), field('表达风格', 'style', c.style, { placeholder: '自然、简洁、有分寸' })));
    behavior.append(field('群聊回复对象', 'reply_to', c.reply_to || '', { optional: true, placeholder: '例如：项目负责人', hint: '群聊中需要针对特定成员分析时填写。' }));
    behavior.append(field('我的兴趣', 'my_interests', c.my_interests || '', { rows: 2, optional: true, placeholder: '例如：摄影、徒步、电影', hint: '用于「我感兴趣的」话题方向。' }));
    behavior.append(append(el('div', 'form-two'), field('实时显示消息条数', 'context_limit', c.context_limit, { type: 'number', hint: '分析时仍读取最近 7 天。' }), field('合并消息等待（毫秒）', 'debounce_ms', c.debounce_ms, { type: 'number', hint: '等对方说完再分析。' })));
    behavior.append(toggle('在本机保留会话历史', 'save_history', c.save_history, '关闭时只在本次运行期间保留。'));
    const generation = el('section', 'advanced-section'); generation.append(el('h3', '', '回复生成模型（可选）'), el('p', 'field-hint', '留空时使用上面的模型。只有判断服务不能写回复时才需要另配。'));
    generation.append(field('生成模型名称', 'reply_model', c.reply_model, { optional: true, placeholder: '留空：使用默认' }), field('生成模型 Base URL', 'reply_base_url', c.reply_base_url, { optional: true, placeholder: '留空：按服务自动匹配' }), field('生成模型 API Key', 'reply_api_key', '', { type: 'password', optional: true, placeholder: c.has_reply_api_key ? '已保存，留空保留' : '留空：复用主密钥' }));
    if (currentState.model_profile) { const profile = currentState.model_profile; generation.append(append(el('div', 'model-profile-receipt'), el('span', '', `${(profile.context_tokens / 10000).toLocaleString()} 万 tokens 上下文`), el('span', '', `思考强度 ${profile.effort}`), el('span', '', `${profile.max_output_tokens.toLocaleString()} tokens 输出上限`))); }
    const media = el('section', 'advanced-section'); media.append(el('h3', '', '图片与语音'), el('p', 'field-hint', '只处理你主动选择识别的图片或语音。'));
    for (const [prefix, label] of [['vision','视觉识别'],['stt','语音转写']]) media.append(field(`${label}模型`, `${prefix}_model`, c[`${prefix}_model`], { optional: true }), field(`${label} API 地址`, `${prefix}_base_url`, c[`${prefix}_base_url`], { optional: true }), field(`${label} API Key`, `${prefix}_api_key`, '', { type: 'password', optional: true, placeholder: c[`has_${prefix}_api_key`] ? '已保存，留空保留' : '仅同来源可复用主 Key' }));
    media.append(field('语音识别来源', 'stt_backend', c.stt_backend, { options: [['auto','自动'],['cloud','联网'],['local','本地离线模型']] }), field('转写接口协议', 'stt_protocol', c.stt_protocol || 'auto', { options: [['auto','自动'],['multipart','OpenAI 兼容 multipart'],['json','OpenRouter 兼容 JSON']] }), field('本地语音模型目录', 'stt_local_model', c.stt_local_model, { optional: true }), toggle('允许联网媒体处理', 'media_allow_cloud', c.media_allow_cloud, '主动识别的图片或音频可能发送到相应服务。'));
    const data = el('section', 'advanced-section'); data.append(el('h3', '', '本地数据'));
    data.append(append(el('div', 'data-actions'), button('打开数据文件夹', 'folder', () => rpc('open_data_folder'), 'small', !available()), button('清除会话历史', 'trash', () => confirmDialog('清除会话历史', '此操作会清除本地保存的聊天上下文和分析记录，模型设置仍会保留。', async () => { await action('clear_history', {}, '会话历史已清除'); }), 'small danger', !available())));
    append(body, source, behavior, generation, media, data); advanced.append(body); form.append(advanced); configActions(form);
    root.append(form); return root;
  }

  function collection(kind) {
    const notes = kind === 'knowledge', items = notes ? currentState.notes : currentState.contacts;
    const root = el('section', 'page collection-page');
    const actions = notes ? [button('导入文本', 'upload', importNotes, '', !available()), button('添加知识', 'plus', () => noteDialog(), 'primary', !available())] : [button('添加联系人', 'plus', () => contactDialog(), 'primary', !available())];
    root.append(heading(notes ? '背景知识库' : '联系人', notes ? '为分析补充事实、偏好和常用背景。' : '记录关系与沟通习惯，自动匹配当前会话。', null, actions));
    const input = el('input', 'input'); input.id = 'collection-search'; input.placeholder = notes ? '搜索标题、内容或标签' : '搜索姓名、别名或关系'; input.setAttribute('aria-label', input.placeholder); input.value = search;
    input.addEventListener('input', () => { search = input.value; renderCollectionItems(root, kind); });
    root.append(append(el('div', 'collection-toolbar'), append(el('div', 'search-wrap'), icon('search', 16), input), el('span', 'collection-count', `${items.length} ${notes ? '条背景知识' : '位联系人'}`)));
    root.append(el('div', 'collection-results')); renderCollectionItems(root, kind); return root;
  }
  function renderCollectionItems(root, kind) {
    const notes = kind === 'knowledge', items = notes ? currentState.notes : currentState.contacts;
    const filtered = items.filter(item => JSON.stringify(item).toLowerCase().includes(search.trim().toLowerCase()));
    const results = $('.collection-results', root); results.replaceChildren();
    if (!filtered.length) { results.append(append(el('div', 'collection-empty'), empty(search ? '没有找到匹配内容' : notes ? '了解你，从背景开始' : '给重要的关系，留一份备注', search ? '换个关键词试试，或添加新的条目。' : notes ? '可以记录工作安排、个人偏好、项目资料，或一段你希望助手记住的背景。' : '称呼、你们的关系、最近在谈的事，都能帮助模型给出更合适的判断。', notes ? 'book' : 'people', !search ? button(notes ? '添加第一条知识' : '添加第一位联系人', 'plus', () => notes ? noteDialog() : contactDialog(), 'small', !available()) : null))); return; }
    const grid = el('div', 'collection-grid');
    for (const item of filtered) {
      const card = el('article', `item-card${notes ? '' : ' contact-card'}`);
      const tools = append(el('div', 'item-actions'), iconButton('编辑', 'edit', () => notes ? noteDialog(item) : contactDialog(item)), iconButton('删除', 'trash', () => confirmDialog(notes ? '删除这条知识' : '删除这位联系人', `删除后，分析时将不再使用「${item.title || item.name}」的背景信息。`, () => action(notes ? 'delete_note' : 'delete_contact', { id: item.id }, '已删除')), 'danger'));
      if (!notes) card.append(el('div', 'contact-avatar', (item.name || '联').slice(0, 1)));
      card.append(append(el('div', 'item-top'), el('h3', '', notes ? item.title : item.name), tools));
      if (!notes && item.aliases?.length) card.append(el('div', 'contact-aliases', `匹配别名：${Array.isArray(item.aliases) ? item.aliases.join('、') : item.aliases}`));
      card.append(el('p', 'item-content', (notes ? item.content : item.notes) || '尚未添加备注'));
      const tags = el('div', 'item-tags');
      if (notes) { if (item.always) tags.append(tag('每次分析使用', 'mint')); for (const text of Array.isArray(item.tags) ? item.tags : String(item.tags || '').split(/[,，]/).filter(Boolean)) tags.append(tag(text)); }
      else if (item.relationship) tags.append(tag(item.relationship, 'mint'));
      card.append(tags); grid.append(card);
    }
    results.append(grid);
  }
  function showDialog(title) {
    const dialog = $('#editor'); if (dialog.open) dialog.close(); dialog.replaceChildren();
    dialog.className = 'dialog';
    dialog.append(append(el('div', 'dialog-head'), el('h2', '', title), iconButton('关闭', 'close', () => dialog.close())));
    const body = el('div', 'dialog-body'); dialog.append(body); dialog.showModal(); return { dialog, body };
  }
  async function showUpdates() {
    const { dialog, body } = showDialog('版本更新');
    body.append(el('p', '', `当前版本：ChatBot ${currentState.version || ''}`), el('p', 'field-hint', '正在检查 GitHub 发布版…'));
    try {
      const result = await rpc('check_updates');
      if (!dialog.open || !body.isConnected) return;
      body.replaceChildren(el('p', '', `当前版本：ChatBot ${currentState.version || ''}`), el('p', '', result.message || '正在检查更新，请稍后重试。'));
      if (result.notes) { const notes = el('pre', 'update-notes', result.notes); notes.style.cssText = 'white-space:pre-wrap;font:inherit;max-height:300px;overflow:auto'; body.append(notes); }
      if (result.url) body.append(button('前往 GitHub 下载', 'arrow', () => rpc('open_update_release'), 'primary'));
      body.append(el('p', 'field-hint', '只读取公开版本信息，不上传聊天和密钥。更新前退出 ChatBot，保留原安装目录的 data 文件夹。'));
    } catch (err) { if (body.isConnected) body.replaceChildren(el('p', '', errorText(err))); }
  }
  function noteDialog(note = {}) {
    const { dialog, body } = showDialog(note.id ? '编辑背景知识' : '添加背景知识'), form = el('form');
    append(form, field('标题', 'note-title', note.title, { placeholder: '例如：近期工作安排' }), field('具体内容', 'note-content', note.content, { rows: 7, placeholder: '补充希望模型了解的事实、偏好或背景…' }), field('标签', 'note-tags', Array.isArray(note.tags) ? note.tags.join('，') : note.tags, { placeholder: '用逗号分隔，例如：工作，项目', optional: true }), toggle('每次分析都使用', 'note-always', note.always, '关闭后，由会话内容匹配相关知识。'));
    const save = button('保存知识', 'check', async () => {
      const title = $('#note-title').value.trim(), content = $('#note-content').value.trim();
      if (!title || !content) { formFeedback(form, '请填写标题和具体内容。', true); return; }
      try { await rpc('save_note', { note: { ...(note.id ? { id: note.id } : {}), title, content, tags: $('#note-tags').value.split(/[,，]/).map(t => t.trim()).filter(Boolean), always: $('#note-always').checked } }); dialog.close(); await sync(); toast('背景知识已保存'); } catch (err) { formFeedback(form, errorText(err), true); }
    }, 'primary');
    form.append(append(el('div', 'dialog-footer'), button('取消', null, () => dialog.close()), save)); form.addEventListener('submit', e => { e.preventDefault(); save.click(); }); body.append(form);
  }
  function contactDialog(contact = {}) {
    const { dialog, body } = showDialog(contact.id ? '编辑联系人' : '添加联系人'), form = el('form');
    append(form, field('微信会话名称', 'contact-name', contact.name, { placeholder: '填写微信中显示的名称', hint: '名称用于匹配读取到的微信会话。' }), field('别名', 'contact-aliases', Array.isArray(contact.aliases) ? contact.aliases.join('，') : contact.aliases, { placeholder: '用逗号分隔其他可能显示的名称', optional: true }), field('你们的关系', 'contact-relationship', contact.relationship, { placeholder: '例如：项目同事、朋友、客户' }), field('沟通背景', 'contact-notes', contact.notes, { rows: 5, optional: true, placeholder: '记录对方的沟通偏好、近期在讨论的事…' }));
    const save = button('保存联系人', 'check', async () => {
      const name = $('#contact-name').value.trim(); if (!name) { formFeedback(form, '请填写微信会话名称。', true); return; }
      try { await rpc('save_contact', { contact: { ...(contact.id ? { id: contact.id } : {}), name, aliases: $('#contact-aliases').value.split(/[,，]/).map(s => s.trim()).filter(Boolean), relationship: $('#contact-relationship').value.trim(), notes: $('#contact-notes').value.trim() } }); dialog.close(); await sync(); toast('联系人已保存'); } catch (err) { formFeedback(form, errorText(err), true); }
    }, 'primary');
    form.append(append(el('div', 'dialog-footer'), button('取消', null, () => dialog.close()), save)); form.addEventListener('submit', e => { e.preventDefault(); save.click(); }); body.append(form);
  }
  function confirmDialog(title, desc, confirm) {
    const { dialog, body } = showDialog(title); body.append(el('p', 'dialog-copy', desc));
    body.append(append(el('div', 'dialog-footer'), button('取消', null, () => dialog.close()), button('确认清除', 'trash', async () => { await confirm(); dialog.close(); }, 'danger')));
  }
  function manualDialog() {
    const { dialog, body } = showDialog('补充一段对话'), form = el('form');
    form.append(el('p', 'dialog-copy', '用于补充未能识别的上下文，或分析一段你主动提供的对话。手动文本不会改变微信中的消息。'));
    form.append(field('会话名称', 'manual-title', currentState.current_session?.title || '', { placeholder: '这段对话的联系人或主题' }), field('对话内容', 'manual-text', '', { rows: 9, placeholder: '对方：明天的方案可以再聊聊吗？\n我：可以，你想重点看哪一部分？' }));
    const save = button('加入工作台', 'arrow', async () => {
      const title = $('#manual-title').value.trim(), text = $('#manual-text').value.trim(); if (!title || !text) { formFeedback(form, '请填写会话名称和对话内容。', true); return; }
      try { await rpc('manual_context', { title, text }); dialog.close(); await sync(); toast('对话已加入，可点击「分析当前」'); } catch (err) { formFeedback(form, errorText(err), true); }
    }, 'primary');
    form.append(append(el('div', 'dialog-footer'), button('取消', null, () => dialog.close()), save)); form.addEventListener('submit', e => { e.preventDefault(); save.click(); }); body.append(form);
  }
  function importNotes() {
    const input = document.createElement('input'); input.type = 'file'; input.accept = '.txt,.md,text/plain,text/markdown';
    input.addEventListener('change', async () => {
      const file = input.files?.[0]; if (!file) return;
      if (file.size > 2 * 1024 * 1024) { toast('文件较大，请选择小于 2 MB 的文本文件。', 'error'); return; }
      try { const text = await file.text(); if (!text.trim()) throw new Error('文件内容为空。'); await action('import_notes', { text }, '知识库文本已导入'); } catch (err) { toast(errorText(err), 'error'); }
    }); input.click();
  }

  let demoSnapshot, demoSessions = new Map();
  function initializeDemo() {
    demoSnapshot = blank(); demoSnapshot.config = { ...demoSnapshot.config, has_api_key: true, base_url: 'https://demo.example.invalid/v1', model_name: 'hy4-preview-f', auto_analyze: true };
    const now = new Date();
    const messages = [
      ['other', '林以宁', '明天提案的结构我重新看了一遍，整体方向没有问题。', -14],
      ['me', '我', '太好了。我把案例部分也补充了，稍后发你新版。', -12],
      ['other', '林以宁', '嗯，不过开头的用户洞察，感觉还是有一点抽象。', -8],
      ['other', '林以宁', '客户之前很在意落地，你觉得要不要放个更具体的场景？', -5],
      ['other', '林以宁', '如果今晚能一起过一下就更好了，十几分钟应该就够。', -1],
    ].map(([side, sender, text, offset], i) => ({ id: `demo-message-${i}`, side, sender, text, timestamp: new Date(now.getTime() + offset * 60000).toISOString(), source: 'ocr' }));
    demoSnapshot.current_session = { id: 'demo-session-1', title: '林以宁', messages, source: 'ocr', active: true };
    messages.splice(2, 0, { id: 'demo-image', side: 'other', sender: '林以宁', kind: 'image', text: '[图片]', media_url: 'demo-scene.svg', timestamp: new Date(now.getTime() - 10 * 60000).toISOString(), source: 'demo' });
    messages.splice(4, 0, { id: 'demo-voice', side: 'other', sender: '林以宁', kind: 'voice', text: '[语音]', duration: 12, timestamp: new Date(now.getTime() - 7 * 60000).toISOString(), source: 'demo' });
    messages.splice(6, 0, { id: 'demo-sticker', side: 'other', sender: '林以宁', kind: 'emoji', emoji_md5: '0'.repeat(32), image_description: '期待地搓手', text: '[表情：期待地搓手]', timestamp: new Date(now.getTime() - 4 * 60000).toISOString(), source: 'demo' });
    const at = now.getTime() / 1000;
    demoMemory = { auto: true, self: [{ id: 'demo-self-1', text: '工作日晚上 8 点后才有空', source: 'manual', at }], sessions: { 'demo-session-1': { title: '林以宁', items: [
      { id: 'demo-mem-1', text: '负责客户沟通，喜欢先确认方向再谈细节', source: 'manual', at },
      { id: 'demo-mem-2', text: '下周三去客户公司做提案', source: 'auto', at }] } } };
    demoHistory = { 'demo-session-1': [
      { id: 'demo-h-1', at: at - 3600, reply_to: '客户之前很在意落地，你觉得要不要放个更具体的场景？', candidates: ['可以，我先补一个使用场景，晚点发你看看。', '有道理，我们从客户最在意的环节切进去。', '好，我今晚先改一版开头。'], best_index: 0, auto: false, sent: null },
      { id: 'demo-h-2', at: at - 90000, reply_to: '明天提案的结构我重新看了一遍，整体方向没有问题。', candidates: ['太好了，那我把案例再补一补。', '收到，辛苦啦！'], best_index: 1, auto: true, sent: { text: '收到，辛苦啦！', status: 'sent', at: at - 89990 } }] };
    demoSnapshot.sessions = [{ id: 'demo-session-1', title: '林以宁', count: messages.length, preview: messages.at(-1).text, updated: now.toISOString(), source: 'ocr', auto_reply_eligible: true, auto_reply_type_known: false }];
    demoSnapshot.status = { capture: 'live', analysis: 'idle', detail: '演示模式 · 所有对话与分析均为合成数据', last_error: '', source: 'ocr', connected: false };
    demoSnapshot.analysis = demoAnalysis('demo-session-1');
    demoSnapshot.notes = [{ id: 'demo-note-1', title: '品牌提案 · 本周背景', content: '客户更重视具体业务场景。第一轮提案聚焦用户洞察和可执行的路径，避免过多概念表达。', tags: ['工作', '提案'], always: false }];
    demoSnapshot.contacts = [{ id: 'demo-contact-1', name: '林以宁', aliases: ['以宁'], relationship: '项目同事', notes: '负责客户沟通，喜欢先确认方向再讨论细节。' }];
    demoSnapshot.actions = [{ id: 'demo-follow-up', session_id: 'demo-session-1', session_title: '林以宁 · 客户方案', title: '核对客户场景，准备下一轮方案', detail: '确认业务场景与可执行路径，再给客户明确的讨论时间。', state: 'open', revision: 1, evidence: [{ side: 'other', text: '客户之前很在意落地，你觉得要不要放个更具体的场景？' }] }];
    demoSnapshot.appearance = { theme: 'paper', font_scale: 1, background_url: '' };
    demoSnapshot.model_profile = { context_tokens: 1000000, max_output_tokens: 64000, effort: 'high' };
    demoSnapshot.catalog = { available: true, source: 'demo', detail: '演示目录 · 合成会话' };
    const names = ['周思远', '设计提案讨论组', '许知遥', '产品协作组', '陈序', '唐映宁', '周末徒步', '顾予安', '林悦', '研发小队', '程书', '许漫', '摄影同行', '沈禾', '江岚'];
    names.forEach((name, i) => demoSnapshot.sessions.push({ id: `demo-more-${i}`, title: name, is_group: /组|队|同行|徒步/.test(name), preview: i % 3 === 0 ? '[图片]' : i % 3 === 1 ? '[语音] 18秒' : '好的，我们明天再确认一下。', kind: i % 3 === 0 ? 'image' : i % 3 === 1 ? 'voice' : 'text', updated: now.toISOString(), source: 'demo', count: 3, auto_reply_eligible: i < 5, auto_reply_type_known: true }));
    demoSnapshot.auto_reply = { ...blank().auto_reply, recent: [{ id: 'demo-auto-reply-1', title: '合成联系人', is_group: false, at: now.toISOString(), status: 'simulated', reason: 'signature_appended' }] };
    demoSessions = new Map([[demoSnapshot.current_session.id, structuredClone(demoSnapshot.current_session)]]);
    demoMemoryCounts();
    demoSnapshot.moments = { available: true, source: 'demo', items: [
      { id: 'demo-moment-1', author: '林以宁', session_id: 'demo-session-1', text: '忙完这一阵，终于赶上了傍晚的光。偶尔慢一点，才会发现熟悉的路也很好看。', timestamp: now.toISOString(), images: ['demo-scene.svg'] },
      { id: 'demo-moment-2', author: '周思远', session_id: 'demo-more-0', text: '第一场分享结束。紧张是真紧张，大家的反馈也是真的有用。下一场见。', timestamp: now.toISOString(), images: [] },
      { id: 'demo-moment-3', author: '许知遥', session_id: 'demo-more-2', text: '周末的小目标：读完手边这本书，试一家新咖啡馆。', timestamp: now.toISOString(), images: [] },
    ] };
  }
  function demoAnalysis(sessionId) {
    return { session_id: sessionId, intent: '对方想一起把方案说得更具体，也在确认你今晚是否方便。', need: '用真实场景支撑洞察，降低明天提案的不确定性。', action: '先接住建议，再给出明确的时间与准备动作。', should_reply: true, urgency: null, risk: 1, confidence: null, answers: { literal_question: { noul: .91 }, true_intent: { choice: 'request_action' }, danger_level: { score: 1 }, should_reply_now: { noul: .84 }, best_action: { choice: 'make_plan' }, she_needs: { choice: 'action' }, tension_resolved: { noul: .93 } }, candidates: [
      { text: '我也觉得加一个具体场景会更有说服力。我先把开头改一版，今晚 8 点一起过一下，你方便吗？', score: null, reason: '回应具体建议，并主动给出下一步和可商量的时间。' },
      { text: '可以，我们就从客户最在意的使用场景切入。你今晚哪个时间方便？我提前把案例和洞察整理到一起。', score: null, reason: '给对方留出时间选择，同时明确自己的准备工作。' },
      { text: '你提的这个点很关键。我先补一个完整的用户场景，晚些时候我们花十几分钟对一遍。', score: null, reason: '表达认可、承诺行动，语气自然，具体时间可继续确认。' },
      { text: '好呀，先用一个具体场景讲清楚。你把最想强调的点发我，我们一起顺一下。', score: null, reason: '邀请对方补充重点，便于继续交流。' },
      { text: '有道理，客户更容易理解具体场景。我们晚点抽十分钟对一下，看看还缺什么。', score: null, reason: '接住对方建议，保留讨论空间。' },
    ], topics: {
      missed: [{ title: '上次没展开的客户反馈', opener: '上次客户提到的落地问题，后来有更具体的反馈吗？', reason: '合成示例：前文提到反馈但没有展开。', evidence_ids: [], grounded: true }],
      their: [{ title: '顺着对方兴趣聊方案表达', opener: '你平时会留意哪些讲得特别清楚的方案？', reason: '合成示例：对方关心具体场景，可能喜欢讨论表达方法。', evidence_ids: [], grounded: true }],
      mine: [{ title: '从自己的兴趣切入摄影', opener: '我最近在练习用照片讲故事，你觉得方案里放一组实拍场景怎么样？', reason: '合成示例：用户补充了摄影兴趣。', evidence_ids: [], grounded: false }]
    }, context_window: { days: 7, start: Date.now()/1000-7*86400, end: Date.now()/1000, message_count: 87, media_count: 2, complete: true, source: 'demo' }, best_index: 0, usage: null, latency_ms: 1840, updated_at: new Date().toISOString(), warning: '' };
  }
  let demoMemory, demoHistory, demoProfiles = {}, demoStyle = null;
  function demoMemoryCounts() {
    const sid = demoSnapshot.current_session?.id;
    demoSnapshot.memory_count = (demoMemory.sessions[sid]?.items || []).length; demoSnapshot.memory_auto = demoMemory.auto;
    demoSnapshot.reply_history_count = (demoHistory[sid] || []).length;
    demoSnapshot.session_profile = { goal: '', context: '', auto_analyze: false, ...(demoProfiles[sid] || {}) };
    demoSnapshot.auto_analyze_selected = Object.entries(demoProfiles).filter(([, p]) => p.auto_analyze).map(([id]) => ({ session_id: id, title: demoSnapshot.sessions.find(s => s.id === id)?.title || id }));
    demoSnapshot.my_style = { learned: Boolean(demoStyle), enabled: demoStyle?.enabled !== false, sample_count: demoStyle?.sample_count || 0, learned_at: demoStyle?.learned_at || null, busy: false };
  }
  function demoMemoryRequest(method, params) {
    const sid = params.session_id, now = Date.now() / 1000;
    const all = () => [...demoMemory.self, ...Object.values(demoMemory.sessions).flatMap(s => s.items)];
    let result = { success: true };
    if (method === 'memory_view') result = { auto: demoMemory.auto, session_id: sid, title: demoMemory.sessions[sid]?.title || '', items: structuredClone(demoMemory.sessions[sid]?.items || []), self: structuredClone(demoMemory.self), profile: { goal: '', context: '', auto_analyze: false, ...(demoProfiles[sid] || {}) }, auto_analyze_scope: demoSnapshot.config.auto_analyze_scope || 'all', auto_analyze: Boolean(demoSnapshot.config.auto_analyze) };
    else if (method === 'session_profile_save') { const p = demoProfiles[sid] ||= { goal: '', context: '', auto_analyze: false }; for (const k of ['goal', 'context', 'auto_analyze']) if (k in params) p[k] = params[k]; result = { success: true, profile: structuredClone(p) }; }
    else if (method === 'style_learn') { demoStyle = { profile: '- 句子很短，常一句话分两三条发\n- 爱用「哈哈」「嗯嗯」「好嘞」，很少打句号\n- 对同事先说结论再补一句客气话\n- 答应时说「可以呀」，拒绝时说「这周有点满，下周再约？」\n- 基本不用「亲」「您」', examples: ['好嘞', '可以呀，我晚点发你', '哈哈哈这也太巧了', '这周有点满，下周再约？'], enabled: true, sample_count: 286, learned_at: now }; result = { success: true, sample_count: 286 }; }
    else if (method === 'style_get') result = structuredClone(demoStyle || { profile: '', examples: [], enabled: true, sample_count: 0, learned_at: null });
    else if (method === 'style_save') { if (!demoStyle) throw new Error('还没有学习过你的说话方式。'); if ('profile' in params) demoStyle.profile = params.profile; if ('enabled' in params) demoStyle.enabled = Boolean(params.enabled); }
    else if (method === 'style_clear') demoStyle = null;
    else if (method === 'memory_overview') result = { auto: demoMemory.auto, self: structuredClone(demoMemory.self), people: Object.entries(demoMemory.sessions).filter(([, s]) => s.items.length).map(([id, s]) => ({ session_id: id, title: s.title, count: s.items.length, preview: s.items.at(-1).text, latest: now })) };
    else if (method === 'memory_add') { const item = { id: `demo-memory-${Date.now()}`, text: String(params.text).slice(0, 120), source: 'manual', at: now }; if (sid === 'self') demoMemory.self.push(item); else (demoMemory.sessions[sid] ||= { title: demoSnapshot.current_session?.title || '', items: [] }).items.push(item); result = { success: true, item }; }
    else if (method === 'memory_update') { const item = all().find(i => i.id === params.id); if (!item) throw new Error('这条记忆已不存在。'); item.text = params.text; item.source = 'manual'; }
    else if (method === 'memory_delete') { demoMemory.self = demoMemory.self.filter(i => i.id !== params.id); for (const s of Object.values(demoMemory.sessions)) s.items = s.items.filter(i => i.id !== params.id); }
    else if (method === 'memory_auto') { demoMemory.auto = Boolean(params.enabled); result = { success: true, auto: demoMemory.auto }; }
    else if (method === 'reply_history') result = { items: structuredClone(demoHistory[sid] || []), title: demoSnapshot.current_session?.title || '' };
    else if (method === 'reply_history_clear') delete demoHistory[sid];
    else if (method === 'fill_history_reply') result = { success: true, message: '演示模式：未向微信写入内容' };
    demoMemoryCounts(); setState(structuredClone(demoSnapshot)); return result;
  }
  async function demoRequest(method, params) {
    if (!demoSnapshot) initializeDemo();
    if (method === 'bootstrap') return structuredClone(demoSnapshot);
    if (method === 'extract_followups') return { proposals: [{ title: '核对客户场景，准备下一轮方案', detail: '合成提案：确认后才保存。', evidence: [{ quote: '客户之前很在意落地' }], message_ids: [] }], warning: '合成演示，不调用模型。' };
    if (method === 'list_actions') return { items: demoSnapshot.actions || [], has_more: false };
    if (method === 'create_action') { const item = { ...params.action, id: `demo-action-${Date.now()}`, session_id: params.session_id, session_title: '合成客户会话', state: 'open', revision: 1, evidence: [] }; (demoSnapshot.actions ||= []).push(item); return item; }
    if (method === 'update_action') { const item = demoSnapshot.actions?.find(x => x.id === params.id); if (item) { item.state = params.state; item.revision++; } return item; }
    if (method === 'search_messages') return { items: [], has_more: false };
    if (['speak_text', 'stop_speech'].includes(method)) return { success: true, message: '合成演示不调用系统语音。' };
    if (method === 'run_agent') {
      const ids = Array.isArray(params.session_ids) ? params.session_ids.slice(0, 3) : [];
      if (!ids.length) throw new Error('请先选择至少一段合成对话。');
      await new Promise(resolve => setTimeout(resolve, 700));
      const cards = ids.map((id, i) => {
        const session = demoSessions.get(id) || (demoSnapshot.current_session?.id === id ? demoSnapshot.current_session : demoSnapshot.sessions.find(item => item.id === id));
        const messages = session?.messages || [];
        const last = messages.at(-1) || { id: `${id}-sample`, side: 'other', text: session?.preview || '我们找个时间再确认一下？' };
        return { session_id: id, title: session?.title || '合成会话', action: i === 0 ? 'reply_now' : 'wait', confidence: .82, risk: 1, reason: i === 0 ? '合成演示结果：对方提出了具体后续安排，适合给出简短回应。此结果不来自模型或真实会话。' : '合成演示结果：当前轮次适合先等待，不需要立即发送。此结果不来自模型或真实会话。', evidence: [{ message_id: last.id, side: last.side, text: last.text || '[媒体消息]' }], candidates: i === 0 ? ['好呀，我们可以先约个方便的时间，再把细节对一下。'] : [], status: 'sample' };
      });
      return { status: 'done', demo: true, label: '合成演示结果', cards, trace: ids.map(id => ({ session_id: id, tool: 'sample_analysis', status: 'demo_only' })) };
    }
    if (method === 'import_chat_records') { await new Promise(r => setTimeout(r, 900)); return { success: true, sessions: 16, messages: 128, message: '演示导入完成：16 个合成会话、128 条合成消息。未读取本地文件。' }; }
    if (method === 'list_sessions') { const all = demoSnapshot.sessions.filter(s => (!params.query || s.title.toLowerCase().includes(params.query.toLowerCase())) && (!params.source || params.source === 'all' || params.source === 'collected' ? true : params.source === s.source)); const start = Number(params.cursor || 0), limit = Number(params.limit || 12); return { items: structuredClone(all.slice(start, start + limit)), next_cursor: start + limit < all.length ? String(start + limit) : null, has_more: start + limit < all.length, total: all.length, available: true, source: 'demo' }; }
    if (method === 'load_media') { const message = demoSnapshot.current_session?.messages.find(m => m.id === params.message_id); return message?.kind === 'image' ? { available: true, media_url: 'demo-scene.svg', kind: 'image' } : { available: false, message: '演示语音没有附带音频文件，仅提供合成转写用于展示。' }; }
    if (method === 'choose_media') { if (!demoSnapshot.current_session) throw new Error('请先选择一个会话。'); const message = { id: `demo-${params.kind}-${Date.now()}`, side: 'other', sender: demoSnapshot.current_session.title, kind: params.kind, text: params.kind === 'image' ? '[图片]' : '[语音]', media_url: params.kind === 'image' ? 'demo-scene.svg' : undefined, duration: params.kind === 'voice' ? 8 : undefined, source: 'demo', timestamp: new Date().toISOString() }; demoSnapshot.current_session.messages.push(message); setState(structuredClone(demoSnapshot)); return { success: true, message: '已加入内置合成媒体，演示模式未读取本机文件。' }; }
    if (method === 'load_session_messages') return { messages: [], has_more: false, next_cursor: null, available: true };
    if (method === 'list_moments') { const all = demoSnapshot.moments.items.filter(m => !params.session_id || m.session_id === params.session_id); return { items: structuredClone(all), has_more: false, next_cursor: null, available: true, source: 'demo' }; }
    if (method === 'analyze_moment') { await new Promise(r => setTimeout(r, 1000)); return { like: true, recommendation: '可以点赞，评论保持轻松。', reason: '这是一条分享近况的动态，简单认可比追问细节更合适。演示建议来自合成数据。', comments: ['这样的傍晚，值得好好停一停。', '忙完还能抓住一点小确幸，真好。'] }; }
    if (method === 'manual_moment') { const item = { id: `demo-moment-${Date.now()}`, author: params.author, text: params.text, session_id: params.session_id, timestamp: new Date().toISOString(), source: 'manual', images: [] }; demoSnapshot.moments.items.unshift(item); return { item, moment_id: item.id }; }
    if (method === 'set_appearance') { Object.assign(demoSnapshot.appearance, params); setState(structuredClone(demoSnapshot)); return { appearance: structuredClone(demoSnapshot.appearance) }; }
    if (method === 'choose_background' || method === 'clear_background') { demoSnapshot.appearance.background_url = method === 'choose_background' ? 'demo-scene.svg' : ''; setState(structuredClone(demoSnapshot)); return { appearance: structuredClone(demoSnapshot.appearance) }; }
    if (method === 'transcribe_voice' || method === 'analyze_image') { const m = demoSnapshot.current_session?.messages.find(m => m.id === params.message_id); if (!m) throw new Error('演示消息未找到。'); if (method === 'transcribe_voice') m.transcript = '我想说的是，今晚我们主要看看开头的案例，十几分钟就好。'; else m.image_description = '演示图片：青绿色山峦与落日，用来测试图片消息的展示和分析入口。'; setState(structuredClone(demoSnapshot)); return { transcript: m.transcript, description: m.image_description }; }
    if (method === 'test_connection') return { success: true, message: '演示连接已通过。这是模拟结果，未请求任何模型服务。', mode: 'demo', generation_available: true };
    if (method.startsWith('memory_') || method.startsWith('reply_history') || method === 'fill_history_reply' || method.startsWith('session_profile') || method.startsWith('style_')) return demoMemoryRequest(method, params);
    if (method === 'save_config') { const c = { ...params.config }; for (const [secret, flag] of [['api_key', 'has_api_key'], ['reply_api_key', 'has_reply_api_key'], ['weflow_token', 'weflow_has_token'], ['work_api_key', 'has_work_api_key']]) { if (c[secret]) c[flag] = true; delete c[secret]; } Object.assign(demoSnapshot.config, c); }
    else if (method === 'start_capture') { demoSnapshot.status.capture = 'live'; if (demoSnapshot.current_session?.source === 'ocr') demoSnapshot.current_session.active = true; }
    else if (method === 'pause_capture') { demoSnapshot.status.capture = 'paused'; if (demoSnapshot.current_session) demoSnapshot.current_session.active = false; }
    else if (method === 'configure_auto_reply') { Object.assign(demoSnapshot.auto_reply, params, { enabled: false, paused: false, status: 'off', detail: '演示模式 · 设置仅更新合成状态，不会连接微信或发送消息。' }); }
    else if (method === 'start_auto_reply') { if (params.acknowledge_send !== true) throw new Error('启动前需要确认自动发送提示。'); demoSnapshot.auto_reply.enabled = true; demoSnapshot.auto_reply.paused = false; demoSnapshot.auto_reply.status = 'running'; demoSnapshot.auto_reply.detail = '演示模式 · 状态为合成数据，不会连接微信或发送消息。'; }
    else if (method === 'pause_auto_reply') { demoSnapshot.auto_reply.enabled = true; demoSnapshot.auto_reply.paused = true; demoSnapshot.auto_reply.status = 'paused'; demoSnapshot.auto_reply.detail = '演示模式 · 自动回复已暂停，没有发送消息。'; }
    else if (method === 'stop_auto_reply') { if (params.emergency !== true) throw new Error('紧急停止需要确认。'); demoSnapshot.auto_reply.enabled = false; demoSnapshot.auto_reply.paused = false; demoSnapshot.auto_reply.status = 'emergency'; demoSnapshot.auto_reply.detail = '演示模式 · 自动回复已紧急停止，没有发送消息。'; }
    else if (method === 'catch_up_auto_reply') {
      if (params.acknowledge_send !== true) throw new Error('运行单次历史补回前需要确认。');
      const session = demoSnapshot.auto_reply.allowlist.find(item => item.session_id === params.session_id);
      if (!session) throw new Error('只能选择已加入允许名单的合成会话。');
      demoSnapshot.auto_reply.catchup = { session_id: params.session_id, status: 'skipped', reason: 'demo_only' };
      demoSnapshot.auto_reply.recent = [{ id: `demo-catchup-${Date.now()}`, title: session.title, is_group: Boolean(session.is_group), at: new Date().toISOString(), status: 'skipped', reason: 'demo_only' }, ...(demoSnapshot.auto_reply.recent || [])].slice(0, 30);
      return { started: true };
    }
    else if (method === 'analyze') {
      demoSnapshot.status.analysis = 'running'; setState(structuredClone(demoSnapshot));
      await new Promise(resolve => setTimeout(resolve, 1300));
      demoSnapshot.analysis = demoAnalysis(params.session_id || demoSnapshot.current_session?.id); demoSnapshot.status.analysis = 'idle';
    } else if (method === 'regenerate_replies') {
      demoSnapshot.status.analysis = 'running'; setState(structuredClone(demoSnapshot));
      await new Promise(resolve => setTimeout(resolve, 1100));
      const tone = params.instruction ? `（${params.instruction}）` : '';
      demoSnapshot.analysis = { ...demoSnapshot.analysis, best_index: 1, candidates: ['好，具体场景我来补，今晚八点碰一下？', '可以，我先改开头，晚点发你。', '有道理，我们就从客户最在意的环节讲。', '行，你把重点发我，我整理好再约你。', '收到，今晚抽十分钟对一下。'].map((text, i) => ({ text: i === 0 && tone ? text + tone : text, score: null, reason: '' })) };
      demoSnapshot.status.analysis = 'idle';
    } else if (method === 'copy_reply') { if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(params.text); else { const t = el('textarea'); t.value = params.text; document.body.append(t); t.select(); const copied = document.execCommand('copy'); t.remove(); if (!copied) throw new Error('浏览器未允许复制，请使用桌面版。'); } }
    else if (method === 'fill_reply') { /* Intentionally no external action in demo mode. */ }
    else if (method === 'set_compact') return { enabled: params.enabled };
    else if (method === 'save_note' || method === 'save_contact') {
      const note = method === 'save_note', list = note ? demoSnapshot.notes : demoSnapshot.contacts, item = { ...(note ? params.note : params.contact) };
      if (!item.id) item.id = `demo-${Date.now()}`;
      const idx = list.findIndex(i => i.id === item.id); if (idx >= 0) list[idx] = item; else list.push(item);
    } else if (method === 'delete_note' || method === 'delete_contact') { const key = method === 'delete_note' ? 'notes' : 'contacts'; demoSnapshot[key] = demoSnapshot[key].filter(i => i.id !== params.id); }
    else if (method === 'clear_history') { demoSnapshot.sessions = []; demoSnapshot.current_session = null; demoSnapshot.analysis = null; }
    else if (method === 'manual_context') {
      const id = `demo-session-${Date.now()}`;
      const messages = params.text.split('\n').filter(Boolean).map((line, i) => { const me = /^我[:：]/.test(line); return { id: `${id}-${i}`, side: me ? 'me' : 'other', sender: me ? '我' : params.title, text: line.replace(/^(我|对方)[:：]\s*/, ''), timestamp: new Date().toISOString(), source: 'manual' }; });
      demoSnapshot.current_session = { id, title: params.title, messages, source: 'manual', active: false }; demoSnapshot.sessions.push({ id, title: params.title, count: messages.length, source: 'manual' }); demoSnapshot.analysis = null;
      demoSessions.set(id, structuredClone(demoSnapshot.current_session));
    } else if (method === 'select_session') {
      const item = demoSnapshot.sessions.find(s => s.id === params.session_id); if (!item) throw new Error('会话不存在。');
      if (!demoSessions.has(item.id)) demoSessions.set(item.id, { ...item, active: false, messages: [{ id: `${item.id}-text`, side: 'other', sender: item.title, kind: item.kind || 'text', text: item.preview, timestamp: new Date().toISOString(), source: 'demo' }] });
      demoSnapshot.current_session = structuredClone(demoSessions.get(item.id)); demoSnapshot.analysis = item.id === 'demo-session-1' ? demoAnalysis(item.id) : null;
    } else if (method === 'import_notes') demoSnapshot.notes.push({ id: `demo-note-${Date.now()}`, title: '导入的背景文本', content: params.text, tags: ['导入'], always: false });
    else if (method === 'refresh_sources') return { sources: ['演示微信窗口（合成数据）'] };
    else if (method === 'one_shot') { toast('演示模式：当前消息来自合成数据，未读取微信。'); }
    else if (method === 'open_data_folder') toast('演示模式没有本地数据文件夹。');
    else throw new Error(`演示模式未实现操作：${method}`);
    setState(structuredClone(demoSnapshot)); return { success: true };
  }
  function offline() {
    if (online || demo) return;
    const n = $('#offline-notice'); n.hidden = false; n.replaceChildren(icon('window', 15), el('span', '', '当前为浏览器预览。请通过 ChatBot 桌面快捷方式打开，以连接微信和本地模型设置。'));
    render(true);
  }
  function attachShell(channel) {
    // Frameless desktop window: the page draws the title bar, Qt does the moving and resizing.
    shell = channel?.objects?.shell || null; if (!shell) return;
    const bar = $('#titlebar'), controls = $('#window-controls');
    bar.classList.add('has-window-controls'); controls.hidden = false;
    const maxButton = controls.querySelector('[data-window="maximize"]');
    const paintMax = maximized => { maxButton.replaceChildren(icon(maximized ? 'winrestore' : 'winmax', 16)); maxButton.title = maximized ? '还原' : '最大化'; maxButton.setAttribute('aria-label', maxButton.title); document.documentElement.classList.toggle('window-maximized', Boolean(maximized)); };
    controls.querySelector('[data-window="minimize"]').append(icon('winmin', 16));
    controls.querySelector('[data-window="close"]').append(icon('winclose', 16));
    paintMax(false);
    controls.addEventListener('click', e => { const kind = e.target.closest('[data-window]')?.dataset.window; if (kind === 'minimize') shell.minimize(); else if (kind === 'maximize') shell.toggleMaximize(); else if (kind === 'close') shell.close(); });
    shell.maximizedChanged?.connect(paintMax);
    shell.isMaximized?.(paintMax);
    const draggable = target => !target.closest('button,a,input,select,textarea,[role="switch"],.window-controls');
    let press = null;
    bar.addEventListener('mousedown', e => { press = e.button === 0 && draggable(e.target) ? { x: e.screenX, y: e.screenY } : null; });
    window.addEventListener('mousemove', e => {
      if (!press || !(e.buttons & 1)) { press = null; return; }
      if (Math.abs(e.screenX - press.x) + Math.abs(e.screenY - press.y) < 4) return;
      press = null; shell.startMove();
    });
    window.addEventListener('mouseup', () => { press = null; });
    bar.addEventListener('dblclick', e => { if (draggable(e.target)) shell.toggleMaximize(); });
  }
  function connect() {
    if (typeof qt !== 'undefined' && typeof QWebChannel !== 'undefined') {
      new QWebChannel(qt.webChannelTransport, channel => {
        attachShell(channel);
        if (demo) { online = true; initializeDemo(); setState(structuredClone(demoSnapshot)); experience.startIntro(); return; }
        bridge = channel.objects.bridge; if (!bridge) { offline(); return; } online = true;
        bridge.response.connect(raw => {
          try { const response = typeof raw === 'string' ? JSON.parse(raw) : raw; const wait = pending.get(String(response.id)); if (!wait) return; clearTimeout(wait.timeout); pending.delete(String(response.id)); response.ok ? wait.resolve(response.data) : wait.reject(new Error(typeof response.error === 'string' ? response.error : response.error?.message || '操作未完成。')); } catch { toast('桌面服务返回的数据无法读取。', 'error'); }
        });
        bridge.event.connect(raw => {
          try { const event = typeof raw === 'string' ? JSON.parse(raw) : raw; if (event.type === 'state') setState(event.data); if (event.type === 'toast') toast(event.data?.message || '', event.data?.level); if (event.type === 'work_agent_progress') experience.handleWorkProgress(event.data); } catch { /* Ignore malformed events; never expose their raw content. */ }
        });
        sync().then(() => experience.startIntro()).catch(err => { toast(errorText(err), 'error'); render(true); });
      });
    } else if (demo) { online = true; initializeDemo(); setState(structuredClone(demoSnapshot)); experience.startIntro(); }
    else offline();
  }
  $('#compact-button').append(icon('compact', 17));
  $('#compact-button').addEventListener('click', () => toggleCompact().catch(err => toast(errorText(err), 'error')));
  $('#settings-button').append(icon('gear', 17));
  $('#settings-button').addEventListener('click', () => drawerTab ? closeDrawer() : openDrawer('settings'));
  $('#status-toggle').addEventListener('click', () => toggleCapture().catch(err => toast(errorText(err), 'error')));
  $('#auto-reply-pill').addEventListener('click', () => openDrawer('auto-reply'));
  $('#drawer-scrim').addEventListener('click', closeDrawer);
  $('.brand').addEventListener('click', e => { e.preventDefault(); go('workspace'); });
  $('#editor').addEventListener('click', e => { if (e.target === $('#editor')) { const r = $('#editor').getBoundingClientRect(); if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) $('#editor').close(); } });
  document.addEventListener('keydown', e => {
    if (e.key === 'Tab' && drawerTab && !document.querySelector('dialog[open]')) {
      const focusable = [...$('#drawer').querySelectorAll('button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), a[href], [tabindex="0"]')].filter(node => node.getClientRects().length);
      const first = focusable[0], last = focusable[focusable.length - 1];
      if (e.shiftKey && (document.activeElement === first || !$('#drawer').contains(document.activeElement))) { e.preventDefault(); last?.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first?.focus(); }
    }
    if ((e.ctrlKey || e.metaKey) && e.key === ',') { e.preventDefault(); drawerTab ? closeDrawer() : openDrawer('settings'); }
    if (e.key === 'Escape' && drawerTab && !document.querySelector('dialog[open]')) closeDrawer();
  });
  $('#app').classList.toggle('compact', compact);
  window.addEventListener('resize', () => {
    const next = window.innerWidth <= 640;
    if (next !== compact) { compact = next; $('#app').classList.toggle('compact', compact); render(); }
  });
  experience = window.ChatBotExperience.mount({ $, el, append, icon, button, iconButton, notice, empty, heading, tag, rpc, action, sync, setState, getState: () => currentState, getPage: () => page, go, render, toast, errorText, formatTime, valueText, available, showDialog, manualDialog, field, demo, importMoments: callback => relationships.importMoments(callback), confirmFollowup: async sid => { await rpc('select_session', { session_id: sid }); await sync(); workbench.actionDialog(); } });
  workbench = window.ChatBotWorkbench.mount({ $, el, append, button, heading, notice, empty, rpc, sync, getState: () => currentState, getPage: () => page, go, render, toast, errorText, showDialog, field, available, demo, openCatalog: (...args) => experience.openCatalog(...args) });
  relationships = window.ChatBotRelationships.mount({ $, el, append, button, heading, notice, empty, rpc, sync, getState: () => currentState, getPage: () => page, go, render, toast, errorText, showDialog, field, available, demo, openCatalog: (...args) => experience.openCatalog(...args) });
  connect();
})();
