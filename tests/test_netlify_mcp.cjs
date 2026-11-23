const { test } = require('node:test');
const assert = require('node:assert/strict');
const { handler } = require('../netlify/functions/mcp-call');
const call = body => handler({ httpMethod: 'POST', body: JSON.stringify(body) });

test('MCP handshake and tool listing come from a real client and server', async () => {
  const response = await call({ source: 'cloud' });
  const body = JSON.parse(response.body);
  assert.equal(response.statusCode, 200);
  assert.equal(body.transport, 'in-memory');
  assert.equal(body.tools[0].name, 'search_pharmacogenetic_literature_tool');
  assert.equal(body.tools.length, 4);
  assert.ok(body.trace.some(item => item.packet.method === 'initialize'));
  assert.ok(body.trace.some(item => item.packet.method === 'tools/list'));
});

test('variant comparison is grounded in retrieved annotations and handles no match', async () => {
  const report = { query: { drug: 'warfarin', gene: 'CYP2C9', variant: 'rs1799853' } };
  const dossier = { clinpgx: { records: [{ id: 'PA123', variant: 'rs1799853', url: 'https://www.clinpgx.org/clinicalAnnotation/PA123' }] } };
  const response = await call({ source: 'cloud', tool: 'match_variant_tool', arguments: { report, dossier } });
  const value = JSON.parse(response.body).result.structuredContent;
  assert.equal(value.items[0].label, 'PA123');
  dossier.clinpgx.records[0].variant = 'rs999';
  const noMatch = JSON.parse((await call({ source: 'cloud', tool: 'match_variant_tool', arguments: { report, dossier } })).body).result.structuredContent;
  assert.equal(noMatch.items[0].label, 'Совпадение не найдено');
});

test('rejects empty input and unavailable transports', async () => {
  assert.equal((await call({ source: 'cloud', tool: 'search_pharmacogenetic_literature_tool', arguments: {} })).statusCode, 400);
  assert.equal((await call({ source: 'external' })).statusCode, 503);
});
