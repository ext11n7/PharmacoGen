const localTools = [
  {
    name: 'synthesize_evidence_tool',
    title: 'Синтез доказательств',
    category: 'анализ текущего отчёта',
    source: 'серверная функция PharmacoGen',
    inputSchema: {
      type: 'object',
      properties: {
        drug: { type: 'string', description: 'Препарат' },
        gene: { type: 'string', description: 'Символ гена' },
        variant: { type: 'string', description: 'Вариант или генотип' },
        faers_available: { type: 'boolean', default: false, description: 'FAERS ответил' },
        faers_reports: { type: 'integer', minimum: 0, maximum: 1000000, default: 0, unit: 'сообщений' },
        faers_serious_rate: { type: 'number', minimum: 0, maximum: 1, default: 0, unit: 'доля' },
        clinvar_available: { type: 'boolean', default: false, description: 'ClinVar ответил' },
        clinvar_records: { type: 'integer', minimum: 0, maximum: 1000000, default: 0, unit: 'записей' },
        clinvar_pathogenic_records: { type: 'integer', minimum: 0, maximum: 1000000, default: 0, unit: 'записей' },
        top_reaction: { type: 'string', description: 'Самая частая реакция' },
      },
      required: ['drug', 'gene'],
    },
  },
  {
    name: 'prioritize_variant_review_tool',
    title: 'Приоритет проверки варианта',
    category: 'ClinVar',
    source: 'серверная функция PharmacoGen',
    inputSchema: {
      type: 'object',
      properties: {
        drug: { type: 'string', description: 'Препарат' },
        gene: { type: 'string', description: 'Символ гена' },
        variant: { type: 'string', description: 'Вариант из записи ClinVar' },
        classification: { type: 'string', description: 'Классификация ClinVar' },
        review_status: { type: 'string', description: 'Статус проверки ClinVar' },
        traits: { type: 'string', description: 'Связанные признаки' },
      },
      required: ['drug', 'gene'],
    },
  },
  {
    name: 'audit_evidence_quality_tool',
    title: 'Контроль качества данных',
    category: 'проверка полноты',
    source: 'серверная функция PharmacoGen',
    inputSchema: {
      type: 'object',
      properties: {
        faers_available: { type: 'boolean', default: false, description: 'FAERS ответил' },
        faers_reports: { type: 'integer', minimum: 0, maximum: 1000000, default: 0, unit: 'сообщений' },
        clinvar_available: { type: 'boolean', default: false, description: 'ClinVar ответил' },
        clinvar_records: { type: 'integer', minimum: 0, maximum: 1000000, default: 0, unit: 'записей' },
        has_variant: { type: 'boolean', default: false, description: 'Вариант указан' },
        has_source_links: { type: 'boolean', default: false, description: 'Ссылки сохранены' },
      },
      required: [],
    },
  },
  {
    name: 'search_pharmacogenetic_literature_tool',
    title: 'Поиск фармакогенетической литературы',
    category: 'PubMed / NCBI',
    source: 'PubMed / NCBI через MCP',
    inputSchema: {
      type: 'object',
      properties: {
        drug: { type: 'string', description: 'Препарат' },
        gene: { type: 'string', description: 'Символ гена' },
        variant: { type: 'string', description: 'Вариант или генотип' },
        max_results: { type: 'integer', minimum: 1, maximum: 10, default: 5, unit: 'публикаций' },
      },
      required: ['drug', 'gene'],
    },
  },
  {
    name: 'formulate_hypotheses_tool',
    title: 'Формирование проверяемых гипотез',
    category: 'синтез исследования',
    source: 'серверная функция PharmacoGen',
    inputSchema: {
      type: 'object',
      properties: {
        drug: { type: 'string', description: 'Препарат' },
        gene: { type: 'string', description: 'Символ гена' },
        variant: { type: 'string', description: 'Вариант или генотип' },
        faers_reports: { type: 'integer', minimum: 0, maximum: 1000000, default: 0, unit: 'сообщений' },
        faers_serious_rate: { type: 'number', minimum: 0, maximum: 1, default: 0, unit: 'доля' },
        clinvar_records: { type: 'integer', minimum: 0, maximum: 1000000, default: 0, unit: 'записей' },
        clinvar_pathogenic_records: { type: 'integer', minimum: 0, maximum: 1000000, default: 0, unit: 'записей' },
        literature_count: { type: 'integer', minimum: 0, maximum: 1000000, default: 0, unit: 'публикаций' },
        top_reaction: { type: 'string', description: 'Самая частая реакция' },
        literature_titles: { type: 'string', description: 'Заголовки найденных публикаций' },
      },
      required: ['drug', 'gene'],
    },
  },
];

exports.handler = async function handler(event) {
  if (event.httpMethod !== 'GET') return { statusCode: 405, body: JSON.stringify({ error: 'Используйте GET' }) };
  return {
    statusCode: 200,
    headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' },
    body: JSON.stringify({
      sources: [
        { id: 'cloud', title: 'MCP на Netlify', description: 'Клиент и сервер MCP в одной функции; внутренний транспорт. Инструмент ищет публикации PubMed.' },
        { id: 'stdio', title: 'Аналитический режим', description: 'На Netlify запрос выполняется серверной функцией поверх данных текущего отчёта.' },
        { id: 'network', title: 'Серверный режим', description: 'Тот же набор аналитических инструментов доступен через публичную функцию.' },
        { id: 'external', title: 'Внешний medical-mcp', description: 'Внешний источник требует отдельного URL или ключа и не включён в публичный демо-деплой.' },
      ],
      local_tools: localTools,
      external_tools: [],
    }),
  };
};
