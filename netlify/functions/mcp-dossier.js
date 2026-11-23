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
    const total = asNumber(result.count);
    return { summary: total ? `Найдено публикаций PubMed: ${total}.` : 'По строгому запросу публикации не найдены; гипотезу нужно проверить по расширенному запросу.', details: { status: 'ok', query, total, returned: records.length, records, source: 'PubMed / NCBI' }, next_steps: ['Проверить методы наиболее релевантных публикаций.', 'Сопоставить публикации с вариантом и классификацией ClinVar.'] };
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
    const synthesis = synthesize(input.synthesis);
    const quality = audit({
      ...input.synthesis,
      has_variant: Boolean(input.synthesis.variant),
      has_source_links: Boolean(input.faers.source && input.clinvar.source),
    });
    const literature = await searchLiterature(input.synthesis.drug, input.synthesis.gene, input.synthesis.variant, 5);
    const prioritized = input.records.map((record, index) => ({
      ...prioritize({
        variant: record.title || record.accession || input.synthesis.variant,
        classification: record.classification,
        review_status: record.review_status,
      }),
      stage: makeStage(`Приоритет варианта ${index + 1}`, 'prioritize_variant_review_tool', 'Вариант направлен на ручную проверку.'),
    }));
    const hypotheses = { summary: 'Исследовательский вопрос подготовлен для проверки по источникам.', details: { hypotheses: [{ type: 'вопрос для исследования', statement: `Связан ли ${input.synthesis.gene}${input.synthesis.variant ? ` (${input.synthesis.variant})` : ''} с ответом на ${input.synthesis.drug}?`, confidence: 'не оценена', basis: 'Ответ требует проверки отдельных публикаций и их методов. Совпадение поисковых терминов не доказывает связь.', next_step: 'Открыть найденные публикации и проверить результаты, участников и конкретный вариант.' }] }, next_steps: ['Проверить результаты и методы найденных публикаций.'] };
    const stages = [
      makeStage('Синтез источников', 'synthesize_evidence_tool', 'Сводка FAERS и ClinVar сопоставлена.'),
      makeStage('Контроль качества', 'audit_evidence_quality_tool', quality.summary),
      makeStage('Поиск публикаций', 'search_pharmacogenetic_literature_tool', literature.summary),
      ...prioritized.map((item) => item.stage),
      makeStage('Формирование гипотез', 'formulate_hypotheses_tool', hypotheses.summary),
    ];
    const nextSteps = [...synthesis.next_steps, ...quality.next_steps, ...literature.next_steps, ...prioritized.flatMap((item) => item.next_steps), ...hypotheses.next_steps];
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' },
      body: JSON.stringify({
        status: 'ok',
        transport: 'netlify-function',
        workflow: { title: 'Исследовательское досье', stages, completed: stages.length, total: stages.length },
        query: input.query,
        synthesis,
        quality,
        literature,
        prioritized_variants: prioritized.map(({ stage, ...item }) => item),
        hypotheses,
        next_steps: [...new Set(nextSteps)].slice(0, 8),
        limitations: [
          'На Netlify досье собирается серверной функцией по уже загруженному отчёту; локальный режим дополнительно демонстрирует настоящий MCP-транспорт stdio/network.',
          'FAERS содержит спонтанные сообщения: их количество не равно частоте и не доказывает причинность.',
          'ClinVar-классификация не доказывает фармакогенетический эффект без дополнительного контекста.',
        ],
        trace: stages.flatMap((stage) => stage.trace),
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
