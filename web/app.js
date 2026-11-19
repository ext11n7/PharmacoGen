const copy = {
  ru: { brand_subtitle:'исследовательская область', language:'Язык', eyebrow:'ЛАБОРАТОРИЯ ДОКАЗАТЕЛЬСТВ', title:'Карта связей<br><em>препарат × ген.</em>', intro:'Следите за источниками, работой агентов и итогом исследования в одном пространстве.', hero_visual_caption:'динамическая карта сигналов', live:'источники доступны', nav_workspace:'Рабочая область', nav_research:'Исследование', nav_history:'История', nav_sources:'Источники', new_research:'Новое исследование', clear:'Очистить', drug:'Препарат', gene:'Ген', variant:'Вариант / генотип', variant_optional:'необязательно', variant_hint:'Например: *2/*3, rs1057910', run:'Собрать доказательства', examples:'Быстрые примеры', sources:'Источники', faers_caption:'спонтанные сообщения', clinvar_caption:'интерпретация вариантов', note:'Исследовательский режим. Результат не является медицинской рекомендацией.', evidence_workspace:'Карта исследования', copy_query:'Копировать запрос', download:'Скачать отчёт', empty_kicker:'НОВОЕ ИССЛЕДОВАНИЕ', empty_title:'Соберите связку<br><em>препарат + ген.</em>', empty_text:'После запуска система проверит источники, покажет найденные сигналы и соберёт прозрачный журнал доказательств.', preview_kicker:'ПРЕДПРОСМОТР ОТЧЁТА', preview_title:'Сценарий исследования', preview_pair:'ПАРА ДЛЯ АНАЛИЗА', preview_wait:'значения появятся после запуска', preview_sources:'ИСТОЧНИКИ', preview_result:'РЕЗУЛЬТАТ', preview_faers_caption:'спонтанные сообщения', preview_clinvar_caption:'генетические варианты', preview_signal:'сигнал и качество данных', preview_steps:'3 этапа проверки', preview_ready:'готово к запуску', map_caption:'КАРТА СВЯЗЕЙ', map_drug:'Препарат', map_gene:'Ген', map_query:'точка запроса', map_safety:'сигналы безопасности', map_variants:'генетические варианты', map_status:'готово к сбору доказательств', loading:'Агенты проверяют источники', recent:'Последние исследования', clear_history:'Очистить историю', no_history:'История появится после первого запуска.', clear_history:'Очистить историю', evidence:'Журнал доказательств', workflow:'Конвейер агентов', limits:'Ограничения', result:'Итог журнала', signal:'Есть сигнал', weak:'Сигнал слабый', incomplete:'Данные неполные', reports:'сообщений', records:'записей', pathogenic:'патогенных', preview:'В превью', serious:'серьёзных сообщений', reactions:'Частые реакции', reaction_chart:'Распределение реакций', basis:'Основание вывода', shown:'Показано', no_data:'нет данных', done:'готово', total:'Всего по запросу', status:'Статус', generated:'Сформирован', source:'Источник', open:'Открыть источник', error:'Ошибка', footer:'Открытые источники · проверяемые гипотезы', copied:'Запрос скопирован', empty_input:'Укажите препарат и ген', api_error:'Не удалось собрать данные', faers:'Сигналы безопасности', clinvar:'Генетические варианты', signal_quality:'Качество сигнала', coverage:'Покрытие источниками', source_status:'Состояние источников', available:'доступен', unavailable:'недоступен', score_note:'оценка для навигации, не клинический балл', route_title:'МАРШРУТ ДОКАЗАТЕЛЬСТВ', route_caption:'два независимых источника', phenotype:'Предварительный фенотип', variant_status:'Статус варианта', preliminary:'предварительно', not_assessed:'не оценён', not_provided:'вариант не указан', evidence_matrix:'Матрица доказательств', evidence_source:'Источник', evidence_object:'Объект проверки', evidence_finding:'Найдено', evidence_level:'Уровень', variant_disclaimer:'Автоматическая пометка помогает навигации и не является клинической классификацией.', run_title:'Журнал работы агентов', run_caption:'каждый этап оставляет проверяемый след', steps:'этапа', limitations:['FAERS основан на спонтанных сообщениях: их число не равно частоте и не доказывает причинность.','ClinVar описывает клиническую интерпретацию вариантов, но сам по себе не доказывает фармакогенетический эффект.','В этой версии нет данных пациента, дозировки, временной последовательности и поправки на сопутствующие препараты.'], agents:['Нормализация сущностей','Сбор данных FAERS','Поиск в ClinVar','Синтез результата'] },
  en: { brand_subtitle:'research workspace', language:'Language', eyebrow:'EVIDENCE LAB', title:'Relation map<br><em>drug × gene.</em>', intro:'Track sources, agent work, and the final result in one research space.', hero_visual_caption:'dynamic signal map', live:'sources available', nav_workspace:'Workspace', nav_research:'Investigation', nav_history:'History', nav_sources:'Sources', new_research:'New investigation', clear:'Clear', drug:'Drug', gene:'Gene', variant:'Variant / genotype', variant_optional:'optional', variant_hint:'For example: *2/*3, rs1057910', run:'Collect evidence', examples:'Quick examples', sources:'Sources', faers_caption:'spontaneous reports', clinvar_caption:'variant interpretation', note:'Research mode. This result is not medical advice.', evidence_workspace:'Investigation map', copy_query:'Copy query', download:'Download report', empty_kicker:'NEW INVESTIGATION', empty_title:'Build a pair<br><em>drug + gene.</em>', empty_text:'Once started, the system checks both sources, shows the available signals, and builds a transparent evidence journal.', preview_kicker:'REPORT PREVIEW', preview_title:'Investigation scenario', preview_pair:'PAIR TO ANALYZE', preview_wait:'values appear after launch', preview_sources:'SOURCES', preview_result:'RESULT', preview_faers_caption:'spontaneous reports', preview_clinvar_caption:'genetic variants', preview_signal:'signal and data quality', preview_steps:'3 verification steps', preview_ready:'ready to launch', map_caption:'RELATION MAP', map_drug:'Drug', map_gene:'Gene', map_query:'query point', map_safety:'safety signals', map_variants:'genetic variants', map_status:'ready to collect evidence', loading:'Agents are checking sources', recent:'Recent investigations', clear_history:'Clear history', no_history:'History will appear after the first run.', evidence:'Evidence journal', workflow:'Agent pipeline', limits:'Limitations', result:'Journal result', signal:'Signal found', weak:'Weak signal', incomplete:'Incomplete data', reports:'reports', records:'records', pathogenic:'pathogenic', preview:'In preview', serious:'serious reports', reactions:'Frequent reactions', reaction_chart:'Reaction distribution', basis:'Basis of result', shown:'Shown', no_data:'no data', done:'done', total:'Total for query', status:'Status', generated:'Generated', source:'Source', open:'Open source', error:'Error', footer:'Open sources · checkable hypotheses', copied:'Query copied', empty_input:'Enter a drug and gene', api_error:'Could not collect data', faers:'Safety signals', clinvar:'Genetic variants', signal_quality:'Signal quality', coverage:'Source coverage', source_status:'Source status', available:'available', unavailable:'unavailable', score_note:'navigation aid, not a clinical score', route_title:'EVIDENCE ROUTE', route_caption:'two independent sources', phenotype:'Preliminary phenotype', variant_status:'Variant status', preliminary:'preliminary', not_assessed:'not assessed', not_provided:'variant not provided', evidence_matrix:'Evidence matrix', evidence_source:'Source', evidence_object:'Checked object', evidence_finding:'Finding', evidence_level:'Level', variant_disclaimer:'This automatic label supports navigation and is not a clinical classification.', run_title:'Agent work journal', run_caption:'each step leaves a checkable trace', steps:'steps', limitations:['FAERS is based on spontaneous reports: report count is not frequency and does not prove causality.','ClinVar describes clinical variant interpretation, but does not prove a pharmacogenetic effect by itself.','This version has no patient-level data, dose, time sequence, or adjustment for concomitant drugs.'], agents:['Entity normalization','FAERS collection','ClinVar search','Result synthesis'] }
};

const $ = (selector) => document.querySelector(selector);
const state = { lang: localStorage.getItem('pg-lang') || 'ru', theme: localStorage.getItem('pg-theme') || 'light', report: null };
let lastPayload = null;

function esc(value) { return String(value ?? '').replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[char])); }
function t(key) { return copy[state.lang][key] ?? key; }
function fmt(value) { return new Intl.NumberFormat(state.lang === 'ru' ? 'ru-RU' : 'en-US').format(Number(value || 0)); }
function applyLanguage() {
  document.documentElement.lang = state.lang;
  document.querySelectorAll('[data-i18n]').forEach((node) => { node.innerHTML = t(node.dataset.i18n); });
  $('#languageSelect').value = state.lang;
  renderHistory();
  if (state.report) renderReport(state.report);
}
function applyTheme() { document.body.classList.toggle('light', state.theme === 'light'); localStorage.setItem('pg-theme', state.theme); }
function toast(message) { const node = document.createElement('div'); node.className = 'toast'; node.textContent = message; document.body.appendChild(node); requestAnimationFrame(() => node.classList.add('show')); setTimeout(() => { node.classList.remove('show'); setTimeout(() => node.remove(), 220); }, 1800); }
function bindGlare() { document.querySelectorAll('.query-rail, .results-panel, .evidence-card, .history-item').forEach((node) => { if (node.dataset.glareBound) return; node.dataset.glareBound = 'true'; node.addEventListener('pointermove', (event) => { const rect = node.getBoundingClientRect(); node.style.setProperty('--mx', `${event.clientX - rect.left}px`); node.style.setProperty('--my', `${event.clientY - rect.top}px`); }); }); }
function setLoading(loading) { $('#emptyState').classList.toggle('hidden', loading || Boolean(state.report)); $('#loadingState').classList.toggle('hidden', !loading); $('#reportState').classList.toggle('hidden', loading || !state.report); $('#runButton').disabled = loading; $('#runButton').querySelector('.button-label').textContent = loading ? t('loading') : t('run'); }
function statusLabel(confidence) { return confidence === 'exploratory' ? t('signal') : confidence === 'weak' ? t('weak') : t('incomplete'); }
function statusHeadline(report) { const key = report.synthesis?.confidence || 'incomplete'; if (state.lang === 'en') return key === 'exploratory' ? `There is a reason to check ${esc(report.normalized_query.drug)} + ${esc(report.normalized_query.gene)}.` : key === 'weak' ? 'The data is collected, but a strong hypothesis is not supported.' : 'The report is incomplete: one or both sources are unavailable.'; return key === 'exploratory' ? `Есть основание проверить связь ${esc(report.normalized_query.drug)} + ${esc(report.normalized_query.gene)}.` : key === 'weak' ? 'Данные собраны, но сильная гипотеза не подтверждена.' : 'Отчёт неполный: один или оба источника недоступны.'; }

function stat(label, value, unit) { return `<div class="metric"><div class="metric-label">${esc(label)}</div><div class="metric-value">${esc(value)} <small>${esc(unit)}</small></div></div>`; }
function sourceCard(kind, title, value, unit, subline) { const url = kind === 'FAERS' ? 'https://open.fda.gov/apis/drug/event/' : 'https://www.ncbi.nlm.nih.gov/clinvar/'; return `<article class="evidence-card"><div class="evidence-card-head"><div><h4>${esc(kind)} · ${esc(title)}</h4><div class="caption">${kind === 'FAERS' ? 'openFDA' : 'NCBI ClinVar'}</div></div><a class="source-open" href="${url}" target="_blank" rel="noreferrer">${t('open')} ↗</a></div><div class="evidence-number">${esc(value)} <small>${esc(unit)}</small></div><div class="subline">${subline}</div></article>`; }
function renderTable(rows, type) {
  if (!rows?.length) return `<p class="muted">${t('no_data')}</p>`;
  if (type === 'reactions') return `<table class="data-table reactions-table"><thead><tr><th>${state.lang === 'ru' ? 'Реакция' : 'Reaction'}</th><th>${state.lang === 'ru' ? 'Количество' : 'Count'}</th></tr></thead><tbody>${rows.map((row) => `<tr><td>${esc(row.term)}</td><td>${esc(row.count)}</td></tr>`).join('')}</tbody></table>`;
  return `<table class="data-table variants-table"><thead><tr><th>${state.lang === 'ru' ? 'Вариант' : 'Variant'}</th><th>${state.lang === 'ru' ? 'Классификация' : 'Classification'}</th><th>${state.lang === 'ru' ? 'Признаки' : 'Traits'}</th></tr></thead><tbody>${rows.map((row) => `<tr><td>${esc(row.title)}</td><td class="muted-cell">${esc(row.classification)}</td><td class="muted-cell">${esc((row.traits || []).join(', '))}</td></tr>`).join('')}</tbody></table>`;
}
function reactionChart(rows) {
  if (!rows?.length) return '';
  const visibleRows = rows.slice(0, 8);
  const max = Math.max(...visibleRows.map((row) => Number(row.count) || 0), 1);
  return `<div class="chart-block"><div class="chart-block-head"><div><div class="subheading">${t('reaction_chart')}</div><div class="chart-caption">FAERS</div></div><span class="chart-total">${visibleRows.length} ${t('records')}</span></div><div class="bar-chart">${visibleRows.map((row) => `<div class="bar-item" title="${esc(row.term)}"><span class="bar-value">${esc(row.count)}</span><i style="height:${Math.max(12, Math.round((Number(row.count) || 0) / max * 100))}%"></i><small>${esc(row.term)}</small></div>`).join('')}</div></div>`;
}
function relationNetwork(report, faersStatus, clinvarStatus, sourceState) {
  const sourceTile = (kind, title, isAvailable) => `<article class="network-source-tile"><div class="network-source-main"><span class="network-glyph">${kind === 'FAERS' ? 'F' : 'C'}</span><div><b>${kind}</b><small>${esc(title)}</small></div></div>${sourceState(isAvailable)}</article>`;
  return `<div class="report-network"><div class="network-route"><div class="network-entity network-drug"><span class="network-glyph">D</span><span><b>${esc(report.normalized_query.drug)}</b><small>${state.lang === 'ru' ? 'препарат' : 'drug'}</small></span></div><span class="route-arrow" aria-hidden="true">→</span><div class="network-route-core"><span>${t('route_title')}</span><strong>FAERS + ClinVar</strong><small>${t('route_caption')}</small></div><span class="route-arrow" aria-hidden="true">→</span><div class="network-entity network-gene"><span class="network-glyph">G</span><span><b>${esc(report.normalized_query.gene)}</b><small>${state.lang === 'ru' ? 'ген' : 'gene'}</small></span></div></div><div class="network-source-grid">${sourceTile('FAERS', t('faers'), faersStatus)}${sourceTile('ClinVar', t('clinvar'), clinvarStatus)}</div></div>`;
}
function variantPanel(report) {
  const variant = report.normalized_query?.variant || '';
  const interpretation = report.synthesis?.variant || {};
  return `<section class="variant-panel"><div class="variant-panel-head"><div><span class="eyebrow">${t('variant')}</span><h4>${esc(variant || t('not_provided'))}</h4></div><span class="variant-badge">${variant ? t('preliminary') : t('not_assessed')}</span></div><div class="variant-grid"><div><span>${t('phenotype')}</span><strong>${esc(interpretation.phenotype || t('not_assessed'))}</strong></div><div><span>${t('variant_status')}</span><strong>${esc(interpretation.label || t('not_assessed'))}</strong></div></div><p>${esc(interpretation.basis || t('variant_hint'))}</p><small>${t('variant_disclaimer')}</small></section>`;
}
function evidenceMatrix(report) {
  const faers = report.faers || {}, clinvar = report.clinvar || {}, query = report.normalized_query || {};
  const variant = query.variant ? ` · ${query.variant}` : ` · ${t('not_provided')}`;
  const rows = [
    { source: 'FAERS', object: query.drug || '', finding: faers.status === 'ok' ? `${fmt(faers.total_reports)} ${t('reports')}` : t('unavailable'), level: faers.status === 'ok' ? t('preliminary') : t('unavailable') },
    { source: 'ClinVar', object: `${query.gene || ''}${variant}`, finding: clinvar.status === 'ok' ? `${fmt(clinvar.pathogenic_records)} ${t('pathogenic')}` : t('unavailable'), level: clinvar.status === 'ok' ? t('preliminary') : t('unavailable') },
  ];
  return `<section class="evidence-matrix"><div class="matrix-head"><div><span class="eyebrow">${t('evidence_matrix')}</span><p>${t('variant_disclaimer')}</p></div><span class="matrix-count">${rows.length} ${t('records')}</span></div><div class="matrix-table"><div class="matrix-row matrix-header"><span>${t('evidence_source')}</span><span>${t('evidence_object')}</span><span>${t('evidence_finding')}</span><span>${t('evidence_level')}</span></div>${rows.map((row) => `<div class="matrix-row"><strong>${esc(row.source)}</strong><span>${esc(row.object)}</span><span>${esc(row.finding)}</span><em>${esc(row.level)}</em></div>`).join('')}</div></section>`;
}
function renderReport(report) {
  const faers = report.faers || {}, clinvar = report.clinvar || {}, synthesis = report.synthesis || {};
  const faersTotal = faers.status === 'ok' ? fmt(faers.total_reports) : t('no_data');
  const clinvarTotal = clinvar.status === 'ok' ? fmt(clinvar.total_records) : t('no_data');
  const pathogenic = clinvar.status === 'ok' ? fmt(clinvar.pathogenic_records) : t('no_data');
  const confidence = synthesis.confidence || 'incomplete';
  const serious = faers.status === 'ok' ? `${faers.serious_preview} ${t('serious')} / ${faers.preview_reports}` : t('no_data');
  const reasons = synthesis.why || [];
  const faersQuality = faers.status === 'ok' ? Math.min(100, 42 + Math.min(35, Math.log10(Math.max(1, faers.total_reports)) * 12) + (faers.preview_reports ? 18 : 0)) : 0;
  const clinvarQuality = clinvar.status === 'ok' ? Math.min(100, 38 + Math.min(42, clinvar.returned_records * 8) + (clinvar.pathogenic_records ? 20 : 0)) : 0;
  const coverage = Math.round(((faers.status === 'ok' ? 1 : 0) + (clinvar.status === 'ok' ? 1 : 0)) / 2 * 100);
  const faersStatus = faers.status === 'ok', clinvarStatus = clinvar.status === 'ok';
  const sourceState = (isOk) => `<span class="source-state ${isOk ? 'is-ok' : 'is-error'}"><i></i>${isOk ? t('available') : t('unavailable')}</span>`;
  const agentEvents = (report.events || []).filter((event) => event.agent);
  const agentStrip = `<div class="agent-console"><div class="agent-console-head"><div><span class="eyebrow">${t('run_title')}</span><p>${t('run_caption')}</p></div><span class="agent-count">${agentEvents.length} / 4 ${t('steps')}</span></div><div class="agent-strip">${agentEvents.map((event, index) => `<div class="agent-step ${event.status === 'error' ? 'is-error' : 'is-done'}"><span class="agent-step-index">0${index + 1}</span><span class="agent-step-dot"></span><span class="agent-step-label">${esc(copy[state.lang].agents[index] || event.agent)}</span></div>`).join('')}</div></div>`;
  $('#reportState').innerHTML = `<div class="report-head"><div><span class="eyebrow">${t('result')}</span><h3>${statusHeadline(report)}</h3><div class="report-query">${esc(report.normalized_query.drug)} &nbsp;×&nbsp; ${esc(report.normalized_query.gene)}${report.normalized_query.variant ? ` &nbsp;×&nbsp; ${esc(report.normalized_query.variant)}` : ''}</div></div><span class="status-pill"><i></i>${statusLabel(confidence)}</span></div><div class="metrics">${stat('FAERS', faersTotal, t('reports'))}${stat('ClinVar', clinvarTotal, t('records'))}${stat('ClinVar', pathogenic, t('pathogenic'))}${stat(t('status'), statusLabel(confidence), '')}</div><div class="signal-overview"><div class="quality-panel"><div class="quality-head"><span>${t('signal_quality')}</span><strong>${Math.round((faersQuality + clinvarQuality) / 2)}<small>/100</small></strong></div><div class="quality-bar"><span style="width:${Math.round((faersQuality + clinvarQuality) / 2)}%"></span></div><p>${t('score_note')}</p></div><div class="coverage-panel"><div class="quality-head"><span>${t('coverage')}</span><strong>${coverage}<small>%</small></strong></div><div class="coverage-bars"><i class="${faersStatus ? 'on' : ''}"></i><i class="${clinvarStatus ? 'on' : ''}"></i></div><p>FAERS · ClinVar</p></div></div>${relationNetwork(report, faersStatus, clinvarStatus, sourceState)}${variantPanel(report)}<div class="tabs"><button class="tab active" data-tab="evidence">${t('evidence')}</button><button class="tab" data-tab="workflow">${t('workflow')}</button><button class="tab" data-tab="limits">${t('limits')}</button></div><div class="tab-panel" data-panel="evidence"><div class="evidence-grid">${sourceCard('FAERS', t('faers'), faersTotal, t('reports'), `${t('preview')}: ${esc(serious)}`)}${sourceCard('ClinVar', t('clinvar'), clinvarTotal, t('records'), `${t('shown')}: ${clinvar.status === 'ok' ? fmt(clinvar.returned_records) : t('no_data')}`)}</div>${evidenceMatrix(report)}${reactionChart(faers.top_reactions)}<div class="subheading">${t('reactions')}</div><div class="table-toolbar"><span>${faers.top_reactions?.length || 0} ${t('records')}</span><input class="table-filter" data-filter="reactions" placeholder="${state.lang === 'ru' ? 'Фильтр реакций…' : 'Filter reactions…'}" /></div>${renderTable(faers.top_reactions, 'reactions')}<div class="subheading">${t('basis')}</div><div class="reason-list">${reasons.map((reason) => `<div class="reason">${esc(reason)}</div>`).join('')}</div><div class="subheading">${t('clinvar')}</div><div class="table-toolbar"><span>${clinvar.records?.length || 0} ${t('records')}</span><input class="table-filter" data-filter="variants" placeholder="${state.lang === 'ru' ? 'Фильтр вариантов…' : 'Filter variants…'}" /></div>${renderTable(clinvar.records, 'variants')}</div><div class="tab-panel hidden" data-panel="workflow">${(report.events || []).filter((event) => event.agent).map((event, index) => `<div class="agent-row"><div class="agent-number">0${index + 1}</div><div><div class="agent-name">${esc(copy[state.lang].agents[index] || event.agent)}</div><div class="agent-detail">${esc(event.message)}</div></div><div class="agent-status">${event.status === 'error' ? t('error') : t('done')}</div></div>`).join('')}</div><div class="tab-panel hidden" data-panel="limits">${(t('limitations')).map((item) => `<div class="limit-row">${esc(item)}</div>`).join('')}<div class="generated">${t('generated')}: ${esc((report.generated_at || '').slice(0, 19).replace('T', ' '))} UTC</div></div>`;
  $('#reportState .tabs').insertAdjacentHTML('beforebegin', agentStrip);
  $('#reportState').querySelectorAll('.tab').forEach((button) => button.addEventListener('click', () => { $('#reportState').querySelectorAll('.tab').forEach((tab) => tab.classList.toggle('active', tab === button)); $('#reportState').querySelectorAll('[data-panel]').forEach((panel) => panel.classList.toggle('hidden', panel.dataset.panel !== button.dataset.tab)); }));
  $('#reportState').querySelectorAll('.table-filter').forEach((input) => input.addEventListener('input', () => { const table = input.closest('.tab-panel').querySelector(`.${input.dataset.filter === 'reactions' ? 'reactions-table' : 'variants-table'}`); if (table) table.querySelectorAll('tbody tr').forEach((row) => row.classList.toggle('filtered-out', !row.textContent.toLowerCase().includes(input.value.toLowerCase()))); }));
  bindGlare();
  setLoading(false);
}

async function runInvestigation(event) {
  event?.preventDefault();
  const drug = $('#drugInput').value.trim(), gene = $('#geneInput').value.trim(), variant = $('#variantInput').value.trim();
  if (!drug || !gene) { toast(t('empty_input')); return; }
  state.report = null; setLoading(true);
  try { const response = await fetch('/api/investigate', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ drug, gene, variant }) }); const data = await response.json(); if (!response.ok) throw new Error(data.error || t('api_error')); state.report = data; lastPayload = { drug, gene, variant }; saveHistory(lastPayload); renderReport(data); } catch (error) { $('#loadingState').innerHTML = `<p>${t('api_error')}</p><small>${esc(error.message)}</small>`; } finally { $('#runButton').disabled = false; }
}
function saveHistory(item) { const history = JSON.parse(localStorage.getItem('pg-history') || '[]').filter((entry) => !(entry.drug === item.drug && entry.gene === item.gene && (entry.variant || '') === (item.variant || ''))); history.unshift({ ...item, date: new Date().toISOString() }); localStorage.setItem('pg-history', JSON.stringify(history.slice(0, 6))); renderHistory(); }
function renderHistory() { const history = JSON.parse(localStorage.getItem('pg-history') || '[]'); $('#historyList').innerHTML = history.length ? history.map((item) => `<div class="history-item"><button data-history="${esc(item.drug)}|${esc(item.gene)}|${esc(item.variant || '')}" type="button"><strong>${esc(item.drug)} × ${esc(item.gene)}${item.variant ? ` × ${esc(item.variant)}` : ''}</strong><small>${new Date(item.date).toLocaleDateString(state.lang === 'ru' ? 'ru-RU' : 'en-US')}</small></button><span class="external">↗</span></div>`).join('') : `<p class="muted">${t('no_history')}</p>`; $('#historyList').querySelectorAll('[data-history]').forEach((button) => button.addEventListener('click', () => { const [drug, gene, variant = ''] = button.dataset.history.split('|'); $('#drugInput').value = drug; $('#geneInput').value = gene; $('#variantInput').value = variant; runInvestigation(); })); }
function downloadReport() { if (!state.report) { toast(t('empty_input')); return; } const blob = new Blob([JSON.stringify(state.report, null, 2)], { type:'application/json' }); const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = 'pharmacogen-report.json'; link.click(); URL.revokeObjectURL(link.href); }

const mcpState = { catalog: null, source: 'stdio', tools: [], selected: null };
function mcpToolsForSource() { return mcpState.source === 'external' ? (mcpState.catalog?.external_tools || []) : (mcpState.catalog?.local_tools || []); }
function mcpSchema(tool) { return tool?.inputSchema || tool?.input_schema || { type: 'object', properties: {} }; }
function mcpProperties(tool) { return mcpSchema(tool).properties || {}; }
function mcpLabel(name) { return name.replace(/_tool$/, '').replaceAll('_', ' '); }
function renderMcpFields() {
  const properties = mcpProperties(mcpState.selected);
  const fields = Object.entries(properties);
  $('#mcpFormFields').innerHTML = fields.length ? fields.map(([name, schema]) => {
    const label = name.replaceAll('_', ' ');
    const type = schema.type || 'string';
    if (type === 'boolean') return `<label class="mcp-checkbox"><input data-mcp-field="${esc(name)}" type="checkbox" ${schema.default ? 'checked' : ''} /><span>${esc(label)}</span></label>`;
    if (type === 'enum' || schema.enum) return `<label class="mcp-field"><span>${esc(label)} <small>${esc(schema.unit || '')}</small></span><select data-mcp-field="${esc(name)}">${(schema.enum || schema.values || []).map((value) => `<option value="${esc(value)}">${esc(value)}</option>`).join('')}</select></label>`;
    const numeric = type === 'number' || type === 'integer';
    const step = type === 'integer' ? '1' : '0.1';
    const attrs = [`type="number"`, `step="${step}"`, schema.min !== undefined ? `min="${schema.min}"` : '', schema.max !== undefined ? `max="${schema.max}"` : '', schema.default !== undefined ? `value="${schema.default}"` : ''].filter(Boolean).join(' ');
    return `<label class="mcp-field"><span>${esc(label)} <small>${esc(schema.unit || '')}</small></span><input data-mcp-field="${esc(name)}" ${numeric ? attrs : 'type="text"'} placeholder="${esc(schema.description || '')}" /></label>`;
  }).join('') : '<p class="muted">У этого инструмента нет параметров.</p>';
}
function renderMcpTools() {
  const query = ($('#mcpToolSearch').value || '').trim().toLowerCase();
  mcpState.tools = mcpToolsForSource().filter((tool) => `${tool.title || ''} ${tool.name || ''} ${tool.category || ''}`.toLowerCase().includes(query));
  $('#mcpToolCount').textContent = `${mcpState.tools.length} инструментов`;
  $('#mcpToolSelect').innerHTML = mcpState.tools.map((tool) => `<option value="${esc(tool.name)}">${esc(tool.title || mcpLabel(tool.name))} · ${esc(tool.category || '')}</option>`).join('') || '<option value="">Нет совпадений</option>';
  const selectedName = mcpState.selected?.name;
  mcpState.selected = mcpState.tools.find((tool) => tool.name === selectedName) || mcpState.tools[0] || null;
  if (mcpState.selected) $('#mcpToolSelect').value = mcpState.selected.name;
  $('#mcpToolDescription').textContent = mcpState.selected ? `${mcpState.selected.name} · ${mcpState.selected.source || 'локальный MCP'}` : 'Инструмент не найден.';
  renderMcpFields();
}
async function loadMcpCatalog() {
  try {
    const response = await fetch('/api/mcp/catalog');
    mcpState.catalog = await response.json();
    renderMcpTools();
  } catch (error) {
    $('#mcpToolDescription').textContent = `Не удалось загрузить каталог: ${error.message}`;
  }
}
function mcpArguments() {
  const result = {};
  document.querySelectorAll('[data-mcp-field]').forEach((field) => {
    const schema = mcpProperties(mcpState.selected)[field.dataset.mcpField] || {};
    if (field.type === 'checkbox') result[field.dataset.mcpField] = field.checked;
    else if (schema.type === 'number') result[field.dataset.mcpField] = Number(field.value);
    else if (schema.type === 'integer') result[field.dataset.mcpField] = Number.parseInt(field.value, 10);
    else result[field.dataset.mcpField] = field.value;
  });
  return result;
}
function extractMcpValue(data) {
  const result = data?.result || {};
  if (result.structuredContent) return result.structuredContent;
  const content = result.content || [];
  const textBlock = content.find((item) => item.type === 'text' && item.text);
  if (textBlock) { try { return JSON.parse(textBlock.text); } catch { return { text: textBlock.text }; } }
  return result;
}
function renderMcpResult(data) {
  const value = extractMcpValue(data);
  const result = value?.result || value;
  const first = result?.value !== undefined ? result : null;
  $('#mcpToolResult').innerHTML = `<div class="mcp-result-head"><div><strong>${esc(data.tool?.name || mcpState.selected?.name || 'MCP')}</strong><small>${esc(data.source)}${data.cache_hit ? ' · кэш' : ' · свежий вызов'}</small></div><span class="mcp-cache">${data.cache_hit ? 'HIT' : 'MISS'}</span></div>${first ? `<div class="mcp-result-value">${esc(first.value)} <small>${esc(first.unit || '')}</small></div><span class="mcp-result-category ${esc(first.risk_color || 'yellow')}">${esc(first.category || 'результат')}</span><p class="mcp-result-copy">${esc(first.interpretation || '')}</p><p class="mcp-result-copy">${Object.entries(first.components || {}).map(([key, item]) => `${esc(key)}: ${esc(item)}`).join(' · ')}</p>` : `<p class="mcp-result-copy">${esc(JSON.stringify(result, null, 2))}</p>`}`;
  $('#mcpTrace code').textContent = JSON.stringify(data.trace || [], null, 2);
  $('#mcpRawResult code').textContent = JSON.stringify(data, null, 2);
}
async function callMcpTool(event) {
  event.preventDefault();
  if (!mcpState.selected) { toast('Выберите инструмент'); return; }
  const button = $('#mcpRunButton');
  button.disabled = true;
  button.querySelector('.button-label').textContent = 'Вызов MCP…';
  try {
    const response = await fetch('/api/mcp/call', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ source:mcpState.source, tool:mcpState.selected.name, arguments:mcpArguments() }) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'MCP вернул ошибку');
    renderMcpResult(data);
    document.querySelector('.mcp-inspector').open = true;
  } catch (error) {
    $('#mcpToolResult').innerHTML = `<p class="mcp-result-copy">Ошибка MCP: ${esc(error.message)}</p>`;
  } finally {
    button.disabled = false;
    button.querySelector('.button-label').textContent = 'Вызвать через MCP';
  }
}
function selectMcpSource(source) {
  mcpState.source = source;
  document.querySelectorAll('.mcp-source-card').forEach((card) => card.classList.toggle('active', card.querySelector('input').value === source));
  renderMcpTools();
}

$('#researchForm').addEventListener('submit', runInvestigation);
$('#clearForm').addEventListener('click', () => { $('#drugInput').value = ''; $('#geneInput').value = ''; $('#variantInput').value = ''; $('#drugInput').focus(); state.report = null; setLoading(false); });
$('#clearHistory').addEventListener('click', () => { localStorage.removeItem('pg-history'); renderHistory(); });
$('#downloadReport').addEventListener('click', downloadReport);
$('#copyQuery').addEventListener('click', async () => { const variant = $('#variantInput').value.trim(); const query = `${$('#drugInput').value.trim()} × ${$('#geneInput').value.trim()}${variant ? ` × ${variant}` : ''}`; await navigator.clipboard?.writeText(query); toast(t('copied')); });
$('#themeToggle').addEventListener('click', () => { state.theme = state.theme === 'dark' ? 'light' : 'dark'; applyTheme(); });
$('#languageSelect').addEventListener('change', (event) => { state.lang = event.target.value; localStorage.setItem('pg-lang', state.lang); applyLanguage(); });
$('#navHistory').addEventListener('click', () => $('#historyList').scrollIntoView({ behavior: 'smooth', block: 'center' }));
$('#navSources').addEventListener('click', () => $('.source-list').scrollIntoView({ behavior: 'smooth', block: 'center' }));
document.querySelectorAll('.quick-chip').forEach((chip) => chip.addEventListener('click', () => { $('#drugInput').value = chip.dataset.drug; $('#geneInput').value = chip.dataset.gene; $('#variantInput').value = chip.dataset.variant || ''; runInvestigation(); }));
document.querySelectorAll('input[name="mcpSource"]').forEach((input) => input.addEventListener('change', () => selectMcpSource(input.value)));
$('#mcpToolSearch').addEventListener('input', renderMcpTools);
$('#mcpToolSelect').addEventListener('change', (event) => { mcpState.selected = mcpState.tools.find((tool) => tool.name === event.target.value) || null; $('#mcpToolDescription').textContent = mcpState.selected ? `${mcpState.selected.name} · ${mcpState.selected.source || 'локальный MCP'}` : 'Инструмент не найден.'; renderMcpFields(); });
$('#mcpToolForm').addEventListener('submit', callMcpTool);
applyTheme(); applyLanguage(); bindGlare(); setLoading(false);
loadMcpCatalog();
