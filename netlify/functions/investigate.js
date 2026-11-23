const ALIAS_MAP = {
  coumadin: 'warfarin',
  варфарин: 'warfarin',
  кумадин: 'warfarin',
  карбамазепин: 'carbamazepine',
  тегретол: 'carbamazepine',
  клопидогрел: 'clopidogrel',
  плавикс: 'clopidogrel',
};

const sourceUrls = {
  faers: 'https://open.fda.gov/apis/drug/event/',
  clinvar: 'https://www.ncbi.nlm.nih.gov/clinvar/',
};

const now = () => new Date().toISOString();
const event = (agent, status, message) => ({ agent, status, message, timestamp: now() });

function normalizeTerm(value) {
  const clean = String(value || '').trim().replace(/\s+/g, ' ');
  return ALIAS_MAP[clean.toLowerCase()] || clean;
}

function normalizeVariant(value) {
  return String(value || '').trim().replace(/\s+/g, '');
}

function interpretVariant(gene, variant) {
  if (!variant) return {
    status: 'not_provided',
    label: 'Вариант не указан',
    phenotype: 'Фенотип не определён',
    basis: 'Добавьте rs-идентификатор или генотип для предварительного сопоставления.',
    confidence: 'not_assessed',
  };
  const token = variant.toLowerCase();
  const known = { cyp2c9: ['*2', '*3'], cyp2c19: ['*2', '*3'], 'hla-b': ['*57:01', '*15:02'] };
  const matched = known[gene.toLowerCase()] || [];
  if (matched.some((item) => token.includes(item.toLowerCase()))) return {
    status: 'review',
    label: 'Есть вариант для отдельной проверки',
    phenotype: 'Возможна изменённая функция',
    basis: 'Сработало предварительное сопоставление по гену и обозначению аллеля; клиническая интерпретация не выполняется автоматически.',
    confidence: 'exploratory',
  };
  return {
    status: 'review',
    label: 'Вариант найден в запросе',
    phenotype: 'Фенотип требует проверки',
    basis: 'Вариант передан в поиск источников; для вывода нужна подтверждённая классификация и контекст генотипа.',
    confidence: 'exploratory',
  };
}

async function getJson(url, params) {
  const query = new URLSearchParams(params);
  const response = await fetch(`${url}?${query}`);
  if (!response.ok) throw new Error(`Источник вернул статус ${response.status}`);
  return response.json();
}

async function searchFaers(drug) {
  const search = `patient.drug.openfda.generic_name:"${drug}"`;
  let summary;
  try { summary = await getJson('https://api.fda.gov/drug/event.json', { search, limit: '1' }); }
  catch (error) {
    if (error.message === 'Источник вернул статус 404') return { status: 'ok', source: sourceUrls.faers, query: search, total_reports: 0, preview_reports: 0, serious_preview: 0, serious_rate: 0, top_reactions: [] };
    throw error;
  }
  const total = Number(summary?.meta?.results?.total || 0);
  const preview = await getJson('https://api.fda.gov/drug/event.json', { search, limit: '20' });
  let serious = 0;
  const reactions = new Map();
  for (const report of preview.results || []) {
    if (String(report.serious || '0') === '1') serious += 1;
    for (const item of report.patient?.reaction || []) {
      const term = item.reactionmeddrapt;
      if (term) reactions.set(term, (reactions.get(term) || 0) + 1);
    }
  }
  const previewReports = (preview.results || []).length;
  return {
    status: 'ok', source: sourceUrls.faers, query: search, total_reports: total,
    preview_reports: previewReports, serious_preview: serious,
    serious_rate: previewReports ? serious / previewReports : 0,
    top_reactions: [...reactions.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8).map(([term, count]) => ({ term, count })),
    sample_report_id: preview.results?.[0]?.safetyreportid || null,
    disclaimer: summary?.meta?.disclaimer || null,
  };
}

async function searchClinvar(gene, drug, variant) {
  let term = `${gene}[gene name]`;
  if (drug) term += ` AND ${drug}[All Fields]`;
  if (variant) term += ` AND ${variant}[All Fields]`;
  const search = await getJson('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi', { db: 'clinvar', term, retmode: 'json', retmax: '10' });
  const result = search.esearchresult || {};
  const ids = result.idlist || [];
  const records = [];
  if (ids.length) {
    const summary = await getJson('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi', { db: 'clinvar', id: ids.join(','), retmode: 'json' });
    for (const uid of summary.result?.uids || []) {
      const record = summary.result?.[uid] || {};
      const classification = record.germline_classification || {};
      records.push({
        uid, accession: record.accession || '', title: record.title || '',
        classification: classification.description || 'Unknown',
        review_status: classification.review_status || '',
        last_evaluated: classification.last_evaluated || '',
        traits: (classification.trait_set || []).map((item) => item.trait_name || ''),
        url: `https://www.ncbi.nlm.nih.gov/clinvar/variation/${uid}/`,
      });
    }
  }
  const pathogenic = records.filter((item) => item.classification.toLowerCase().includes('pathogenic')).length;
  return { status: 'ok', source: sourceUrls.clinvar, query: term, total_records: Number(result.count || 0), returned_records: records.length, pathogenic_records: pathogenic, records };
}

function synthesis(drug, gene, variant, faers, clinvar) {
  const faersOk = faers.status === 'ok';
  const clinvarOk = clinvar.status === 'ok';
  const pathogenic = clinvarOk ? clinvar.pathogenic_records : 0;
  let confidence = 'incomplete';
  let headline = 'Отчёт неполный: один или оба источника недоступны.';
  if (faersOk && clinvarOk) {
    confidence = 'weak';
    headline = 'Данные собраны, но автоматического основания для сильной гипотезы недостаточно.';
  }
  return {
    headline, confidence, variant: interpretVariant(gene, variant),
    why: [
      faersOk ? `FAERS: ${faers.total_reports.toLocaleString('ru-RU')} сообщений по препарату ${drug}.` : 'FAERS: данные недоступны.',
      clinvarOk ? `ClinVar: ${pathogenic.toLocaleString('ru-RU')} записей с классификацией pathogenic/likely pathogenic для ${gene}.` : 'ClinVar: данные недоступны.',
      'FAERS содержит сообщения по препарату, но не устанавливает генотип или причинную связь.',
    ],
    limitations: [
      'FAERS основан на спонтанных сообщениях: число сообщений не равно частоте и не доказывает причинность.',
      'ClinVar описывает клиническую интерпретацию вариантов, но сам по себе не доказывает фармакогенетический эффект.',
      'В этой версии нет индивидуальных данных пациента, дозировки, временной последовательности или поправки на сопутствующие препараты.',
    ],
    not_medical_advice: true,
  };
}

exports.handler = async function handler(eventRequest) {
  if (eventRequest.httpMethod !== 'POST') return { statusCode: 405, body: JSON.stringify({ error: 'Используйте POST' }) };
  try {
    const payload = JSON.parse(eventRequest.body || '{}');
    const drugInput = String(payload.drug || '').trim();
    const geneInput = String(payload.gene || '').trim();
    const variantInput = String(payload.variant || '').trim();
    if (!drugInput || !geneInput) return { statusCode: 400, body: JSON.stringify({ error: 'Укажите препарат и ген' }) };
    const normalized = { drug: normalizeTerm(drugInput), gene: geneInput.toUpperCase() };
    if (variantInput) normalized.variant = normalizeVariant(variantInput);
    const events = [event('Entity Agent', 'done', `Нормализованы сущности: ${normalized.drug} + ${normalized.gene}${normalized.variant ? ` + ${normalized.variant}` : ''}`)];
    let faers;
    let clinvar;
    try { events.push(event('FAERS Agent', 'running', `Запрос openFDA FAERS для ${normalized.drug}`)); faers = await searchFaers(normalized.drug); events.push(event('FAERS Agent', 'done', `Найдено сообщений: ${faers.total_reports.toLocaleString('ru-RU')}`)); } catch (error) { faers = { status: 'error', error: error.message, source: sourceUrls.faers }; events.push(event('FAERS Agent', 'error', error.message)); }
    try { events.push(event('ClinVar Agent', 'running', `Поиск ClinVar для пары ${normalized.gene} + ${normalized.drug}`)); clinvar = await searchClinvar(normalized.gene, normalized.drug, normalized.variant || ''); events.push(event('ClinVar Agent', 'done', `Получено записей ClinVar: ${clinvar.total_records.toLocaleString('ru-RU')}`)); } catch (error) { clinvar = { status: 'error', error: error.message, source: sourceUrls.clinvar }; events.push(event('ClinVar Agent', 'error', error.message)); }
    events.push(event('Synthesis Agent', 'running', 'Сопоставление доказательств и проверка ограничений'));
    const result = synthesis(normalized.drug, normalized.gene, normalized.variant || '', faers, clinvar);
    events.push(event('Synthesis Agent', 'done', `Итоговая сила сигнала: ${result.confidence}`));
    const query = { drug: drugInput, gene: geneInput };
    if (variantInput) query.variant = variantInput;
    return { statusCode: 200, headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' }, body: JSON.stringify({ query, normalized_query: normalized, faers, clinvar, synthesis: result, events, generated_at: now() }) };
  } catch (error) {
    return { statusCode: 500, body: JSON.stringify({ error: `Не удалось собрать данные: ${error.message}` }) };
  }
}
