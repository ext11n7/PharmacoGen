const { test } = require('node:test');
const assert = require('node:assert/strict');
const analysis = require('../netlify/functions/analysis');

const event = { httpMethod: 'POST', body: JSON.stringify({ report: { query: { drug: 'warfarin', gene: 'CYP2C9' } }, dossier: { literature: { details: { records: [{ pmid: '1', title: 'Paper', abstract: 'An abstract' }] } } } }) };

test('unconfigured model is reported without calling a provider', async () => {
  delete process.env.OPENAI_API_KEY;
  delete process.env.PHARMACOGEN_LLM_MODEL;
  const response = await analysis.handler(event);
  assert.equal(JSON.parse(response.body).status, 'not_configured');
});

test('model output is rejected when its citation was not supplied', async () => {
  process.env.OPENAI_API_KEY = 'test-only';
  process.env.PHARMACOGEN_LLM_MODEL = 'test-model';
  global.fetch = async () => ({ ok: true, json: async () => ({ choices: [{ message: { content: JSON.stringify({ sections: [{ title: 'Обзор', paragraphs: [{ text: 'Текст', source_ids: ['PMID:999'] }] }] }) } }] }) });
  const response = await analysis.handler(event);
  assert.equal(JSON.parse(response.body).status, 'unavailable');
});

test('model output with an available citation is returned', async () => {
  global.fetch = async () => ({ ok: true, json: async () => ({ choices: [{ message: { content: JSON.stringify({ sections: [{ title: 'Обзор', paragraphs: [{ text: 'Текст', source_ids: ['PMID:1'] }] }] }) } }] }) });
  const response = await analysis.handler(event);
  assert.equal(JSON.parse(response.body).status, 'ok');
});
