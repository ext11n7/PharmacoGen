const now = () => new Date().toISOString();

function asNumber(value) {
  const number = Number(value || 0);
  return Number.isFinite(number) ? number : 0;
}

async function fetchJson(url, params) {
  const query = new URLSearchParams(params);
  const response = await fetch(`${url}?${query.toString()}`, { signal: AbortSignal.timeout(10000) });
  if (!response.ok) throw new Error(`Источник вернул статус ${response.status}`);
  return response.json();
}

async function enrichPubmed(records) {
  const ids = records.map(x => String(x.pmid || '')).filter(x => /^\d+$/.test(x));
  if (!ids.length) return records;
  try {
    const data = await fetchJson('https://www.ebi.ac.uk/europepmc/webservices/rest/search', { query: `EXT_ID:(${ids.join(' OR ')}) AND SRC:MED`, format: 'json', resultType: 'core', pageSize: String(ids.length) });
    const matches = new Map((data.resultList?.result || []).map(item => [String(item.pmid), item]));
    return records.map(record => {
      const item = matches.get(String(record.pmid)) || {};
      return { ...record, abstract: String(item.abstractText || '').replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim(), publication_types: item.pubTypeList?.pubType || [], doi: item.doi || '', pmcid: item.pmcid || '', open_access: item.isOpenAccess === 'Y', abstract_source: 'Europe PMC / PubMed' };
    });
  } catch { return records.map(record => ({ ...record, abstract_unavailable: true })); }
}

async function searchCpic(drug, gene) {
  try {
    const rows = await fetchJson('https://api.cpicpgx.org/v1/guideline', { select: 'id,name,genes,url,version', name: `ilike.*${drug}*`, limit: '30' });
    const records = rows.filter(row => Array.isArray(row.genes) && row.genes.some(item => String(item).toUpperCase() === gene.toUpperCase()));
    return { status: 'ok', source: 'CPIC', query: { drug, gene }, total: records.length, records };
  } catch (error) { return { status: 'unavailable', source: 'CPIC', total: 0, records: [], error: error.message }; }
}

async function searchClinpgx(drug, gene, variant) {
  try {
    const payload = await fetchJson('https://api.clinpgx.org/v1/data/clinicalAnnotation', { 'relatedChemicals.name': drug, 'location.genes.symbol': gene });
    if (payload.status !== 'success' || !Array.isArray(payload.data)) throw Error('ClinPGx вернул неожиданный формат');
    const records = payload.data.filter(item => Array.isArray(item.relatedChemicals) && item.relatedChemicals.some(x => String(x.name || '').toLowerCase() === drug.toLowerCase()) && Array.isArray(item.location?.genes) && item.location.genes.some(x => String(x.symbol || '').toUpperCase() === gene.toUpperCase()) && /^PA\d+$/.test(String(item.accessionId || ''))).map(item => ({ id: item.accessionId, title: item.name || '', variant: item.location?.displayName || item.location?.rsid || '', evidence_level: item.levelOfEvidence?.term || '', url: `https://www.clinpgx.org/clinicalAnnotation/${item.accessionId}`, statements: (Array.isArray(item.allelePhenotypes) ? item.allelePhenotypes : []).slice(0, 4).map(row => ({ allele: row.allele || '', text: row.phenotype || '' })), scope: 'drug_gene_pair' }));
    return { status: 'ok', source: 'ClinPGx', query: { drug, gene, variant }, total: records.length, records: records.slice(0, 8) };
  } catch (error) { return { status: 'unavailable', source: 'ClinPGx', total: 0, records: [], error: error.message }; }
}

async function searchLiterature(drug, gene, variant, maxResults = 5) {
  const terms = [`"${drug}"[Title/Abstract]`, `"${gene}"[Title/Abstract]`];
  if (variant) terms.push(`"${variant}"[Title/Abstract]`);
  const query = terms.join(' AND ');
  try {
    const search = await fetchJson('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi', { db: 'pubmed', term: query, retmode: 'json', retmax: String(maxResults), sort: 'relevance' });
    const result = search.esearchresult || {};
    const ids = result.idlist || [];
    const records = [];
    if (ids.length) {
      const summary = await fetchJson('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi', { db: 'pubmed', id: ids.join(','), retmode: 'json' });
      for (const uid of summary.result?.uids || []) {
        const item = summary.result?.[uid] || {};
        records.push({ pmid: String(uid), title: item.title || '', journal: item.fulljournalname || '', pubdate: item.pubdate || '', url: `https://pubmed.ncbi.nlm.nih.gov/${uid}/` });
      }
    }
    const enriched = await enrichPubmed(records);
    const total = asNumber(result.count);
    return { summary: total ? `Найдено публикаций PubMed: ${total}.` : 'По строгому запросу публикации не найдены; гипотезу нужно проверить по расширенному запросу.', details: { status: 'ok', query, total, returned: enriched.length, records: enriched, source: 'PubMed / NCBI' }, next_steps: ['Проверить методы наиболее релевантных публикаций.', 'Сопоставить публикации с вариантом и классификацией ClinVar.'] };
  } catch (error) {
    return { summary: 'PubMed временно недоступен: гипотеза сформирована по текущему срезу.', details: { status: 'unavailable', query, total: 0, returned: 0, records: [], source: 'PubMed / NCBI', error: error.message }, next_steps: ['Повторить поиск публикаций позже.', 'Не усиливать гипотезу без проверки внешней литературы.'] };
  }
}

function formulateHypotheses(input, literature) {
  const hypotheses = [];
  const literatureCount = asNumber(literature?.details?.total);
  const titles = (literature?.details?.records || []).slice(0, 3).map((item) => item.title).filter(Boolean).join('; ');
  const reaction = input.top_reaction || 'профиль реакций';
  if (input.variant && input.clinvar_records) {
    hypotheses.push({ type: 'вариант-ответ', statement: `Вариант ${input.variant} может быть связан с изменённым ответом на ${input.drug} у носителей варианта ${input.gene}.`, confidence: literatureCount && input.clinvar_pathogenic_records ? 'средняя' : 'низкая', basis: `ClinVar: ${input.clinvar_records} записей; патогенных или вероятно патогенных: ${input.clinvar_pathogenic_records}; публикаций PubMed: ${literatureCount}.`, next_step: 'Сопоставить вариант с фармакогенетической рекомендацией и дизайном найденных исследований.' });
  }
  if (input.faers_reports) {
    hypotheses.push({ type: 'сигнал безопасности', statement: `Профиль сообщений FAERS по ${input.drug} может содержать сигнал, который стоит проверить в контексте ${input.gene}.`, confidence: 'низкая', basis: `FAERS: ${input.faers_reports} сообщений; частая реакция: «${reaction}»; серьёзные сообщения: ${(input.faers_serious_rate || 0).toLocaleString('ru-RU', { style: 'percent', maximumFractionDigits: 1 })}.`, next_step: 'Проверить временную последовательность, сопутствующие препараты и наличие генотипа в первичных данных.' });
  }
  if (literatureCount) {
    hypotheses.push({ type: 'литературная проверка', statement: `Связь ${input.drug} × ${input.gene} имеет публикационный контекст и заслуживает предметной проверки.`, confidence: literatureCount >= 3 ? 'средняя' : 'низкая', basis: `В PubMed найдено публикаций: ${literatureCount}.${titles ? ` Пример: ${titles.slice(0, 180)}.` : ''}`, next_step: 'Прочитать методы и критерии включения, затем сравнить их с текущим срезом.' });
  }
  if (!hypotheses.length) hypotheses.push({ type: 'пробел данных', statement: `Для ${input.drug} × ${input.gene} пока недостаточно признаков для содержательной гипотезы.`, confidence: 'не определена', basis: 'Нет записей FAERS, ClinVar или публикаций, на которых можно строить проверяемое предположение.', next_step: 'Расширить запрос, указать вариант или повторить сбор данных.' });
  return { summary: `Сформировано гипотез: ${hypotheses.length}. Первая требует проверки, а не принятия как факт.`, details: { hypotheses, literature_count: literatureCount }, next_steps: hypotheses.map((item) => item.next_step) };
}

function reportArguments(report) {
  const query = report.normalized_query || report.query || {};
  const faers = report.faers || {};
  const clinvar = report.clinvar || {};
  if (!query.drug || !query.gene) throw new Error('В отчёте нет препарата или гена');
  const records = Array.isArray(clinvar.records) ? clinvar.records.filter((item) => item && typeof item === 'object').slice(0, 3) : [];
  const reactions = Array.isArray(faers.top_reactions) ? faers.top_reactions : [];
  return {
    query: {
      drug: String(query.drug),
      gene: String(query.gene),
      variant: String(query.variant || ''),
    },
    faers,
    clinvar,
    records,
    synthesis: {
      drug: String(query.drug),
      gene: String(query.gene),
      variant: String(query.variant || ''),
      faers_available: faers.status === 'ok',
      faers_reports: asNumber(faers.total_reports),
      faers_serious_rate: asNumber(faers.serious_rate),
      clinvar_available: clinvar.status === 'ok',
      clinvar_records: asNumber(clinvar.total_records),
      clinvar_pathogenic_records: asNumber(clinvar.pathogenic_records),
      top_reaction: String(reactions[0]?.term || ''),
    },
  };
}

function makeStage(title, tool, detail) {
  return {
    title,
    tool,
    status: 'done',
    trace: [],
    detail,
  };
}

function synthesize(input) {
  const available = Number(input.faers_available) + Number(input.clinvar_available);
  const hasSignal = input.faers_reports > 0 && input.clinvar_pathogenic_records > 0;
  const hasData = input.faers_reports > 0 || input.clinvar_records > 0;
  const priority = hasSignal ? 'высокий' : hasData && available === 2 ? 'средний' : hasData ? 'низкий' : 'не определён';
  return {
    summary: hasSignal
      ? `Есть основание проверить связь ${input.drug} + ${input.gene}; это гипотеза, а не доказанный эффект.`
      : hasData ? `Рабочая гипотеза для ${input.drug} + ${input.gene} сформирована; требуется проверка литературы и варианта.` : 'Срез пуст: нужно продолжить сбор данных.',
    details: {
      priority,
      available_sources: available,
      faers_reports: input.faers_reports,
      clinvar_records: input.clinvar_records,
      top_reaction: input.top_reaction || 'не выделена',
    },
    next_steps: [
      'Открыть исходные записи FAERS и ClinVar по сохранённым ссылкам.',
      hasSignal ? 'Проверить варианты с высоким приоритетом вручную.' : 'Уточнить вариант или расширить поисковый запрос.',
    ],
  };
}

function audit(input) {
  const missing = [];
  if (!input.faers_available) missing.push('ответ FAERS');
  if (!input.clinvar_available) missing.push('ответ ClinVar');
  if (!input.faers_reports) missing.push('число сообщений FAERS');
  if (!input.clinvar_records) missing.push('записи ClinVar');
  if (!input.has_source_links) missing.push('ссылки на источники');
  const qualityScore = Math.max(0, Math.round(100 - missing.length * 18));
  return {
    summary: missing.length ? 'Срез требует проверки перед интерпретацией.' : 'Срез достаточно полон для исследовательского просмотра.',
    details: { quality_score: qualityScore, missing, checked: 5 },
    next_steps: missing.length ? [`Проверить: ${missing.join(', ')}.`] : ['Сохранить ссылки и перейти к ручной проверке вариантов.'],
  };
}

function prioritize(input) {
  const text = `${input.classification} ${input.review_status}`.toLowerCase();
  const high = text.includes('pathogenic') || text.includes('likely pathogenic') || text.includes('expert');
  const priority = high ? 'высокий' : text.includes('conflicting') || text.includes('uncertain') ? 'средний' : 'обычный';
  return {
    summary: high ? 'Вариант стоит проверить в первую очередь.' : 'Вариант требует дополнительной проверки в источнике.',
    details: {
      variant: input.variant || 'вариант из записи ClinVar',
      priority,
      classification: input.classification || 'не указана',
      review_status: input.review_status || 'не указан',
    },
    next_steps: [
      'Открыть запись ClinVar и проверить дату оценки.',
      'Сопоставить вариант с клинической рекомендацией и контекстом пациента.',
    ],
  };
}

exports.handler = async function handler(event) {
  if (event.httpMethod !== 'POST') return { statusCode: 405, body: JSON.stringify({ error: 'Используйте POST' }) };
  try {
    const payload = JSON.parse(event.body || '{}');
    const report = payload.report;
    if (!report || typeof report !== 'object') throw new Error('Передайте готовый отчёт исследования');
    const input = reportArguments(report);
    const [literature, cpic, clinpgx] = await Promise.all([searchLiterature(input.synthesis.drug, input.synthesis.gene, input.synthesis.variant, 5), searchCpic(input.synthesis.drug, input.synthesis.gene), searchClinpgx(input.synthesis.drug, input.synthesis.gene, input.synthesis.variant)]);
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' },
      body: JSON.stringify({
        status: 'ok',
        transport: 'netlify-function',
        query: input.query,
        literature,
        cpic,
        clinpgx,
        limitations: [
          'На Netlify поиск PubMed выполняется серверной функцией; MCP доступен при локальном запуске.',
          'Совпадение поискового запроса не означает, что публикация подтверждает связь.',
        ],
        trace: [],
      }),
    };
  } catch (error) {
    return { statusCode: 400, headers: { 'Content-Type': 'application/json; charset=utf-8' }, body: JSON.stringify({ error: error.message }) };
  }
};

exports.synthesizeEvidence = synthesize;
exports.auditEvidence = audit;
exports.prioritizeVariant = prioritize;
exports.searchLiterature = searchLiterature;
exports.formulateHypotheses = formulateHypotheses;
