const { Client } = require('@modelcontextprotocol/sdk/client/index.js');
const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { InMemoryTransport } = require('@modelcontextprotocol/sdk/inMemory.js');
const { ListToolsRequestSchema, CallToolRequestSchema } = require('@modelcontextprotocol/sdk/types.js');
const { searchLiterature } = require('./mcp-dossier');
const { analyze, evidenceRecords } = require('./evidence-tools');

const tools = [{ name: 'search_pharmacogenetic_literature_tool', description: 'Поиск публикаций PubMed по препарату, гену и варианту', inputSchema: { type: 'object', properties: { drug: { type: 'string', minLength: 2, maxLength: 120 }, gene: { type: 'string', minLength: 2, maxLength: 40 }, variant: { type: 'string', maxLength: 120 } }, required: ['drug', 'gene'] } }, ...[['audit_research_tool', 'Проверка полноты досье'], ['match_variant_tool', 'Сопоставление обозначения варианта'], ['plan_review_tool', 'План дальнейшей проверки'], ['inspect_publications_tool', 'Разбор публикаций'], ['inspect_clinvar_tool', 'Разбор записей ClinVar']].map(([name, description]) => ({ name, description, inputSchema: { type: 'object', properties: { report: { type: 'object' }, dossier: { type: 'object' } }, required: ['report', 'dossier'] } }))];
for (const [name, description, fields] of [
  ['search_evidence_tool', 'Поиск фразы в собранных записях', ['term']],
  ['compare_records_tool', 'Сравнение двух выбранных записей', ['record_a', 'record_b']],
]) tools.push({ name, description, inputSchema: { type: 'object', properties: { report: { type: 'object' }, dossier: { type: 'object' }, ...Object.fromEntries(fields.map(field => [field, { type: 'string', minLength: 2, maxLength: 100 }])) }, required: ['report', 'dossier', ...fields] } });

exports.handler = async (event) => {
  const send = (statusCode, value) => ({ statusCode, headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' }, body: JSON.stringify(value) });
  if (event.httpMethod !== 'POST') return send(405, { error: 'Используйте POST' });
  if ((event.body || '').length > 200000) return send(400, { error: 'Слишком большой запрос' });
  let input;
  try { input = JSON.parse(event.body || '{}'); } catch { return send(400, { error: 'Неверный формат запроса' }); }
  if (input.source !== 'cloud') return send(503, { error: 'Этот транспорт доступен только локально. Выберите MCP на Netlify.' });
  const isCheck = !input.tool;
  if (!isCheck && !tools.some(tool => tool.name === input.tool)) return send(400, { error: 'Инструмент не найден.' });
  const args = input.arguments || {};
  if (!isCheck && input.tool === tools[0].name && (typeof args.drug !== 'string' || args.drug.trim().length < 2 || args.drug.length > 120 || typeof args.gene !== 'string' || args.gene.trim().length < 2 || args.gene.length > 40 || (args.variant != null && (typeof args.variant !== 'string' || args.variant.length > 120)))) return send(400, { error: 'Укажите препарат и ген (не менее двух символов).' });
  if (!isCheck && input.tool !== tools[0].name && (!args.report || !args.dossier || typeof args.report !== 'object' || typeof args.dossier !== 'object')) return send(400, { error: 'Сначала завершите исследование.' });
  if (!isCheck && input.tool === 'search_evidence_tool' && (typeof args.term !== 'string' || args.term.trim().length < 2 || args.term.trim().length > 100)) return send(400, { error: 'Введите фразу от 2 до 100 символов.' });
  if (!isCheck && input.tool === 'compare_records_tool' && (typeof args.record_a !== 'string' || typeof args.record_b !== 'string' || args.record_a === args.record_b || !args.record_a || !args.record_b || args.record_a.length > 100 || args.record_b.length > 100)) return send(400, { error: 'Выберите две разные записи.' });
  if (!isCheck && input.tool === 'compare_records_tool' && ![args.record_a, args.record_b].every(id => evidenceRecords(args.report, args.dossier).some(row => row.id === id))) return send(400, { error: 'Выбранная запись отсутствует в текущем досье.' });
  const trace = [];
  const server = new Server({ name: 'pharmacogen-netlify', version: '1.0.0' }, { capabilities: { tools: {} } });
  server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools }));
  server.setRequestHandler(CallToolRequestSchema, async request => {
    if (!tools.some(tool => tool.name === request.params.name)) throw new Error('Инструмент не найден');
    const a = request.params.arguments;
    const result = request.params.name === tools[0].name ? await searchLiterature(a.drug.trim(), a.gene.trim(), (a.variant || '').trim(), 5) : analyze(request.params.name, a);
    if (request.params.name === 'compare_records_tool') {
      const response = await require('./analysis').handler({ httpMethod: 'POST', body: JSON.stringify({ report: a.report, dossier: a.dossier, mode: 'comparison', record_ids: [a.record_a, a.record_b] }) });
      result.ai_comparison = JSON.parse(response.body);
      result.sources = evidenceRecords(a.report, a.dossier).filter(row => [a.record_a, a.record_b].includes(row.id)).map(({ id, url }) => ({ id, url }));
    }
    return { content: [{ type: 'text', text: JSON.stringify(result) }], structuredContent: result };
  });
  const client = new Client({ name: 'pharmacogen-client', version: '1.0.0' });
  const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
  for (const [transport, direction] of [[clientTransport, 'request'], [serverTransport, 'response']]) {
    const sendMessage = transport.send.bind(transport);
    transport.send = async (message, options) => { trace.push({ direction, packet: message }); return sendMessage(message, options); };
  }
  try {
    await server.connect(serverTransport);
    await client.connect(clientTransport);
    const listing = await client.listTools();
    if (isCheck) return send(200, { source: 'cloud', transport: 'in-memory', tools: listing.tools, trace });
    const result = await client.callTool({ name: input.tool, arguments: args });
    return send(200, { source: 'cloud', transport: 'in-memory', tool: { name: input.tool }, result, trace, cache_hit: false });
  } catch { return send(503, { error: 'Не удалось выполнить MCP-запрос. Попробуйте позже.' }); }
  finally { await client.close(); await server.close(); }
};
