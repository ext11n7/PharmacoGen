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
  assert.equal(body.tools.length, 8);
  assert.ok(body.trace.some(item => item.packet.method === 'initialize'));
  assert.ok(body.trace.some(item => item.packet.method === 'tools/list'));
});

test('search and comparison operate on selected source records', async () => {
  const report = { query: { drug: 'warfarin', gene: 'CYP2C9' }, clinvar: { records: [{ uid: '123', title: 'CYP2C9 variant', classification: 'drug response', traits: ['bleeding'] }] } };
  const dossier = { literature: { details: { records: [{ pmid: '42', title: 'Warfarin study', abstract: 'Bleeding was reported.' }] } } };
  const invoke = async (tool, extra) => JSON.parse((await call({ source: 'cloud', tool, arguments: { report, dossier, ...extra } })).body).result.structuredContent;
  const hits = await invoke('search_evidence_tool', { term: 'bleeding' });
  assert.deepEqual(hits.items.map(x => x.label), ['PubMed · PMID:42', 'ClinVar · ClinVar:123']);
  const compared = await invoke('compare_records_tool', { record_a: 'PMID:42', record_b: 'ClinVar:123' });
  assert.equal(compared.items.length, 2);
  assert.match(compared.items[0].text, /Bleeding/);
  assert.match(compared.items[1].text, /drug response/);
  const invalid = await call({ source: 'cloud', tool: 'compare_records_tool', arguments: { report, dossier, record_a: 'PMID:42', record_b: 'PMID:42' } });
  assert.equal(invalid.statusCode, 400);
  const noHits = await invoke('search_evidence_tool', { term: 'no such text' });
  assert.equal(noHits.items[0].label, 'Совпадений нет');
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
