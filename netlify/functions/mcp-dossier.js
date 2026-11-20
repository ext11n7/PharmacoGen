const now = () => new Date().toISOString();

function asNumber(value) {
  const number = Number(value || 0);
  return Number.isFinite(number) ? number : 0;
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
    trace: [{ direction: 'request', method: 'tools/call', tool, timestamp: now() }, { direction: 'response', tool, status: 'ok', timestamp: now() }],
    detail,
  };
}

function synthesize(input) {
  const available = Number(input.faers_available) + Number(input.clinvar_available);
  const hasSignal = input.faers_reports > 0 && input.clinvar_pathogenic_records > 0;
  const priority = hasSignal ? 'высокий' : available === 2 ? 'средний' : 'не определён';
  return {
    summary: hasSignal
      ? `Есть основание проверить связь ${input.drug} + ${input.gene}; это гипотеза, а не доказанный эффект.`
      : 'Данные собраны, но автоматического основания для сильной гипотезы недостаточно.',
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
    const prioritized = input.records.map((record, index) => ({
      ...prioritize({
        variant: record.title || record.accession || input.synthesis.variant,
        classification: record.classification,
        review_status: record.review_status,
      }),
      stage: makeStage(`Приоритет варианта ${index + 1}`, 'prioritize_variant_review_tool', 'Вариант направлен на ручную проверку.'),
    }));
    const stages = [
      makeStage('Синтез источников', 'synthesize_evidence_tool', 'Сводка FAERS и ClinVar сопоставлена.'),
      makeStage('Контроль качества', 'audit_evidence_quality_tool', quality.summary),
      ...prioritized.map((item) => item.stage),
    ];
    const nextSteps = [...synthesis.next_steps, ...quality.next_steps, ...prioritized.flatMap((item) => item.next_steps)];
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
        prioritized_variants: prioritized.map(({ stage, ...item }) => item),
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
