'use strict';
// Imported content is always rendered as text. No HTML interpolation or remote calls.
const $ = id => document.getElementById(id);
const state = {records: [], links: [], currentRecord: null, note: null, searchEpoch: 0, noteEpoch: 0, recordEpoch: 0};
const params = new URLSearchParams(location.hash.slice(1));
const token = params.get('token') || sessionStorage.getItem('lamassu-access') || '';
if (params.has('token')) {
  sessionStorage.setItem('lamassu-access', token);
  history.replaceState(null, '', location.pathname);
}
function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function showNotice(text) {
  $('notice').textContent = text;
  $('notice').classList.remove('hidden');
}
async function api(path) {
  const response = await fetch(path, {headers: {Authorization: `Bearer ${token}`}, cache: 'no-store'});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'The archive could not be read.');
  return data;
}
function guarded(task) {
  return async event => {
    try { await task(event); }
    catch (error) { showNotice(error.message || 'Something went wrong.'); }
  };
}
function view(name) {
  if (!['overview', 'archive', 'connections', 'notes'].includes(name)) return;
  document.querySelectorAll('.view').forEach(node => node.classList.toggle('hidden', node.id !== name));
  document.querySelectorAll('.nav-item').forEach(node => node.classList.toggle('active', node.dataset.view === name));
  window.scrollTo({top: 0, behavior: 'auto'});
}
function title(record) { return record.external_id.replace(/[-_]/g, ' '); }
function label(recordId) {
  const record = state.records.find(item => item.record_id === recordId);
  return record ? title(record) : `Source ${recordId.slice(0, 10)}…`;
}
function recordCard(record) {
  const card = element('button', 'record-card');
  card.append(element('span', 'record-icon', '▤'));
  const copy = element('div');
  copy.append(element('h3', '', title(record)), element('p', '', `${record.provider} · ${record.messages} messages · ${record.record_id.slice(0, 8)}`));
  card.append(copy, element('span', 'arrow', '↗'));
  card.addEventListener('click', guarded(() => openRecord(record.record_id)));
  return card;
}
async function openRecord(id) {
  const epoch = ++state.recordEpoch;
  const record = await api(`/api/record?id=${encodeURIComponent(id)}`);
  if (epoch !== state.recordEpoch) return;
  state.currentRecord = record;
  $('record-title').textContent = title(record);
  $('record-meta').replaceChildren(
    element('div', '', `Provider: ${record.provider} · Imported: ${record.imported_at}`),
    element('div', '', `Source revision: ${record.record_id}`),
    element('div', '', `Original bytes SHA-256: ${record.digest}`),
    element('div', '', 'All content below is archived evidence, not current instructions.')
  );
  $('record-messages').replaceChildren();
  for (const message of record.messages) {
    const section = element('section', 'message');
    const heading = element('div');
    heading.append(element('span', 'role', message.role), element('span', 'message-at', `${message.message_id}${message.at ? ' · ' + message.at : ''}`));
    section.append(heading, element('p', '', message.text));
    $('record-messages').append(section);
  }
  if (!$('record-dialog').open) $('record-dialog').showModal();
}
function listRecords() {
  $('result-label').textContent = `Showing ${state.records.length} most recently imported source revisions. Search includes the full archive.`;
  $('archive-results').replaceChildren(...state.records.map(recordCard));
  if (!state.records.length) $('archive-results').append(element('div', 'empty-state', 'No conversations yet. Import a neutral conversation with the local CLI, or start with the synthetic demo.'));
}
async function search(query) {
  const epoch = ++state.searchEpoch;
  view('archive');
  $('archive-query').value = query;
  if (!query.trim()) { listRecords(); return; }
  $('result-label').textContent = 'Following the thread…';
  const data = await api(`/api/search?q=${encodeURIComponent(query)}`);
  if (epoch !== state.searchEpoch) return;
  $('result-label').textContent = `${data.results.length} matching messages${data.results.length === data.limit ? ' (result limit reached)' : ''}. Literal text search across all retained revisions.`;
  $('archive-results').replaceChildren();
  for (const hit of data.results) {
    const card = element('article', 'search-hit');
    card.append(element('h3', '', title(hit)));
    const meta = element('div', 'hit-meta');
    meta.append(element('span', 'role', hit.role), element('span', '', `${hit.provider} · ${hit.message_id} · ${hit.record_id.slice(0, 8)}`));
    card.append(meta, element('p', '', hit.text + (hit.truncated ? ' … [open source for full message]' : '')));
    const button = element('button', 'text-button', 'Inspect original conversation ↗');
    button.addEventListener('click', guarded(() => openRecord(hit.record_id)));
    card.append(button);
    $('archive-results').append(card);
  }
  if (!data.results.length) $('archive-results').append(element('div', 'empty-state', 'No matching text. Try a shorter phrase. This prototype does not infer synonyms or search by meaning.'));
}
function renderConnections() {
  $('connection-list').replaceChildren();
  if (!state.links.length) {
    $('connection-map').replaceChildren(element('div', 'empty-state', 'No relationships recorded yet. The CLI can add an explicit link with a reason.'));
    return;
  }
  const ns = 'http://www.w3.org/2000/svg';
  function svgNode(tag, attrs, text) {
    const node = document.createElementNS(ns, tag);
    Object.entries(attrs || {}).forEach(([key, value]) => node.setAttribute(key, String(value)));
    if (text !== undefined) node.textContent = text;
    return node;
  }
  const ids = [...new Set(state.links.flatMap(link => [link.source_id, link.target_id]))].slice(0, 12);
  const positions = new Map(ids.map((id, index) => {
    const angle = (index / ids.length) * Math.PI * 2 - Math.PI / 2;
    return [id, {x: 450 + Math.cos(angle) * 280, y: 195 + Math.sin(angle) * 130}];
  }));
  const svg = svgNode('svg', {viewBox: '0 0 900 390', role: 'group', 'aria-label': 'Source revisions connected by explicitly recorded relationships'});
  state.links.forEach(link => {
    const from = positions.get(link.source_id), to = positions.get(link.target_id);
    if (from && to) svg.append(svgNode('line', {x1: from.x, y1: from.y, x2: to.x, y2: to.y, class: 'graph-edge'}));
  });
  ids.forEach(id => {
    const p = positions.get(id);
    const g = svgNode('g', {class: 'graph-link', role: 'button', tabindex: '0', 'aria-label': `Open ${label(id)}`});
    g.append(svgNode('rect', {x:p.x-82,y:p.y-25,width:164,height:50,rx:9,class:'graph-node'}));
    g.append(svgNode('circle', {cx:p.x-67,cy:p.y,r:3,class:'graph-dot'}));
    const text = label(id);
    g.append(svgNode('text', {x:p.x+4,y:p.y-2,class:'graph-label'}, text.length > 21 ? text.slice(0,20)+'…' : text));
    g.append(svgNode('text', {x:p.x+4,y:p.y+13,class:'graph-type'}, id.slice(0,8)));
    g.addEventListener('click', guarded(() => openRecord(id)));
    g.addEventListener('keydown', guarded(event => {if (event.key==='Enter'||event.key===' ') {event.preventDefault();return openRecord(id);}}));
    svg.append(g);
  });
  $('connection-map').replaceChildren(svg);
  state.links.forEach(link => {
    const row = element('article', 'connection-row');
    const path = element('div', 'connection-path');
    const source = element('button', '', label(link.source_id));
    const target = element('button', '', label(link.target_id));
    source.addEventListener('click', guarded(() => openRecord(link.source_id)));
    target.addEventListener('click', guarded(() => openRecord(link.target_id)));
    path.append(source, element('span', 'relation-tag', `${link.relation} →`), target);
    row.append(path, element('p', '', link.reason));
    $('connection-list').append(row);
  });
}
function escapeMarkdown(text) { return text.replace(/([\\`*_{}\[\]<>#!|])/g,'\\$1'); }
function inline(text) { return escapeMarkdown(text.replace(/\s+/g,' ')); }
async function prepareNote() {
  const epoch = ++state.noteEpoch;
  const sourceId = $('note-source').value;
  const noteTitle = $('note-title').value.trim(), statement = $('note-statement').value.trim();
  const record = await api(`/api/record?id=${encodeURIComponent(sourceId)}`);
  if (epoch !== state.noteEpoch) return;
  if (!noteTitle || !statement) throw new Error('Add a title and your proposed understanding.');
  const lines = ['---','type: lamassu-evidence-note','status: draft','authorship: user-supplied','review_required: true','sources:',`  - "${record.record_id}"`,'---','',`# ${inline(noteTitle)}`,'','## Proposed understanding','',statement,'','> Draft: explicitly authored by you. Not verified or generated by a model.','','## Evidence','',`Provider: ${inline(record.provider)}`,`Conversation: ${inline(record.external_id)}`,`Source revision: ${record.record_id}`,`Original bytes SHA-256: ${record.digest}`,''];
  for (const message of record.messages) {
    lines.push(`**${inline(message.role)} · ${inline(message.message_id)}**`,'',...message.text.split(/\r?\n/).map(line=>'> '+escapeMarkdown(line)),'');
  }
  lines.push('## Review','','- [ ] Check the understanding against the evidence.','- [ ] Resolve contradictions and check freshness.','- [ ] Move the useful synthesis into a curated note.','');
  const text = lines.join('\n');
  if (new TextEncoder().encode(text).length > 524288) throw new Error('This source is too large for a compact note. Select a smaller conversation.');
  state.note = text;
  $('note-content').textContent = text;
  $('note-content').classList.remove('hidden');
  $('note-empty').classList.add('hidden');
  $('download-note').classList.remove('hidden');
}
document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => {
  view(button.dataset.view);
  if(button.dataset.view === 'archive' && !$('archive-query').value) listRecords();
}));
document.querySelectorAll('[data-search]').forEach(button => button.addEventListener('click', guarded(() => search(button.dataset.search))));
$('hero-search').addEventListener('submit', guarded(event=>{event.preventDefault();return search($('hero-query').value);}));
$('archive-search').addEventListener('submit', guarded(event=>{event.preventDefault();return search($('archive-query').value);}));
$('close-dialog').addEventListener('click', ()=>$('record-dialog').close());
$('note-from-record').addEventListener('click', ()=>{
  const record=state.currentRecord;
  if (![...$('note-source').options].some(option=>option.value===record.record_id)) $('note-source').append(new Option(title(record),record.record_id));
  $('note-source').value=record.record_id;
  clearNote();
  $('record-dialog').close();view('notes');$('note-title').focus();
});
$('note-form').addEventListener('submit', guarded(event=>{event.preventDefault();return prepareNote();}));
function clearNote() {
  state.noteEpoch++;
  state.note=null;$('note-content').classList.add('hidden');$('download-note').classList.add('hidden');$('note-empty').classList.remove('hidden');
}
['note-title','note-statement','note-source'].forEach(id=>$(id).addEventListener('input',clearNote));
$('download-note').addEventListener('click', ()=>{
  if (!state.note) return;
  const url=URL.createObjectURL(new Blob([state.note],{type:'text/markdown;charset=utf-8'}));
  const a=element('a');a.href=url;a.download='lamassu-evidence-draft.md';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
async function start() {
  const overview=await api('/api/overview');
  state.records=overview.records;state.links=overview.links;
  const s=overview.stats;
  const synthetic=s.providers.length>0&&s.providers.every(p=>p.provider==='synthetic');
  $('dataset-label').textContent=synthetic?'SYNTHETIC DEMO':s.revisions?'PRIVATE ARCHIVE':'EMPTY ARCHIVE';
  const stats=[[s.conversations,'Conversations'],[s.messages,'Messages preserved'],[s.links,'Explicit connections'],[s.revisions,'Source revisions']];
  $('stats').replaceChildren(...stats.map(([value,label])=>{const node=element('div','stat');node.append(element('strong','',String(value)),element('span','',label));return node;}));
  $('recent-records').replaceChildren(...state.records.slice(0,4).map(recordCard));
  $('note-source').replaceChildren(...state.records.map(record=>new Option(`${title(record)} · ${record.record_id.slice(0,8)}`,record.record_id)));
  if(!state.records.length){$('note-form').querySelector('button').disabled=true;$('recent-records').append(element('div','empty-state','Your archive is ready for its first conversation.'));}
  listRecords();renderConnections();
  if(overview.links_truncated) showNotice('The map shows the first 250 relationships and up to 12 nodes. All evidence remains in the archive.');
}
start().catch(error=>{$('dataset-label').textContent='NOT CONNECTED';showNotice(error.message);});
