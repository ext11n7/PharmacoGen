const { synthesizeEvidence, auditEvidence, prioritizeVariant, searchLiterature, formulateHypotheses } = require('./mcp-dossier');

const now = () => new Date().toISOString();
const asNumber = (value) => Number.isFinite(Number(value)) ? Number(value) : 0;
const asBoolean = (value) => value === true || value === 'true';

function required(argumentsObject, fields) {
  const missing = fields.filter((name) => String(argumentsObject[name] || '').trim() === '');
  if (missing.length) throw new Error(`Заполните: ${missing.join(', ')}`);
}

async function callTool(tool, args) {
  if (tool === 'synthesize_evidence_tool') {
    required(args, ['drug', 'gene']);
    return synthesizeEvidence({
      drug: String(args.drug), gene: String(args.gene), variant: String(args.variant || ''),
      faers_available: asBoolean(args.faers_available), faers_reports: asNumber(args.faers_reports),
      faers_serious_rate: asNumber(args.faers_serious_rate), clinvar_available: asBoolean(args.clinvar_available),
      clinvar_records: asNumber(args.clinvar_records), clinvar_pathogenic_records: asNumber(args.clinvar_pathogenic_records),
      top_reaction: String(args.top_reaction || ''),
    });
  }
  if (tool === 'prioritize_variant_review_tool') {
    required(args, ['drug', 'gene']);
    return prioritizeVariant({ drug: String(args.drug), gene: String(args.gene), variant: String(args.variant || ''), classification: String(args.classification || ''), review_status: String(args.review_status || ''), traits: String(args.traits || '') });
  }
  if (tool === 'audit_evidence_quality_tool') {
    return auditEvidence({ faers_available: asBoolean(args.faers_available), faers_reports: asNumber(args.faers_reports), clinvar_available: asBoolean(args.clinvar_available), clinvar_records: asNumber(args.clinvar_records), has_variant: asBoolean(args.has_variant), has_source_links: asBoolean(args.has_source_links) });
  }
  if (tool === 'search_pharmacogenetic_literature_tool') {
    required(args, ['drug', 'gene']);
    return searchLiterature(String(args.drug), String(args.gene), String(args.variant || ''), Math.min(10, Math.max(1, asNumber(args.max_results) || 5)));
  }
  if (tool === 'formulate_hypotheses_tool') {
    required(args, ['drug', 'gene']);
    return formulateHypotheses({
      drug: String(args.drug), gene: String(args.gene), variant: String(args.variant || ''),
      faers_reports: asNumber(args.faers_reports), faers_serious_rate: asNumber(args.faers_serious_rate),
      clinvar_records: asNumber(args.clinvar_records), clinvar_pathogenic_records: asNumber(args.clinvar_pathogenic_records),
      top_reaction: String(args.top_reaction || ''),
    }, { details: { total: asNumber(args.literature_count), records: String(args.literature_titles || '').split('; ').filter(Boolean).map((title) => ({ title })) } });
  }
  throw new Error('Инструмент MCP не найден');
}

exports.handler = async function handler(event) {
  if (event.httpMethod !== 'POST') return { statusCode: 405, body: JSON.stringify({ error: 'Используйте POST' }) };
  return { statusCode: 503, headers: { 'Content-Type': 'application/json; charset=utf-8' }, body: JSON.stringify({ error: 'На Netlify MCP-сервер не подключён. Для настоящего вызова запустите приложение локально.' }) };
  try {
    const payload = JSON.parse(event.body || '{}');
    const source = String(payload.source || 'stdio');
    const tool = String(payload.tool || '');
    const args = payload.arguments && typeof payload.arguments === 'object' ? payload.arguments : {};
    if (!tool) throw new Error('Выберите инструмент MCP');
    if (source === 'external') throw new Error('Внешний MCP не включён в публичный Netlify-деплой');
    const result = await callTool(tool, args);
    const trace = [
      { direction: 'request', packet: { jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: tool, arguments: args } } },
      { direction: 'response', packet: { jsonrpc: '2.0', id: 1, result } },
    ];
    return { statusCode: 200, headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' }, body: JSON.stringify({ source: 'netlify-function', tool: { name: tool }, result: { structuredContent: result }, trace, cache_hit: false }) };
  } catch (error) {
    return { statusCode: 400, headers: { 'Content-Type': 'application/json; charset=utf-8' }, body: JSON.stringify({ error: error.message }) };
  }
};
