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

test('Gemini uses server-side key and accepts a cited response', async () => {
  process.env.GEMINI_API_KEY = 'test-gemini';
  delete process.env.PHARMACOGEN_LLM_MODEL;
  global.fetch = async (url, options) => {
    assert.match(url, /generativelanguage\.googleapis\.com/);
    assert.equal(options.headers['x-goog-api-key'], 'test-gemini');
    return { ok: true, json: async () => ({ candidates: [{ content: { parts: [{ text: JSON.stringify({ sections: [{ title: 'Обзор', paragraphs: [{ text: 'Текст', source_ids: ['PMID:1'] }] }] }) }] } }] }) };
  };
  const result = JSON.parse((await analysis.handler(event)).body);
  assert.equal(result.status, 'ok');
  assert.equal(result.model, 'gemini-2.5-flash');
  delete process.env.GEMINI_API_KEY;
});

test('Groq is selected when its key is configured', async () => {
  process.env.GROQ_API_KEY = 'test-groq';
  delete process.env.PHARMACOGEN_LLM_MODEL;
  global.fetch = async (url, options) => {
    assert.equal(url, 'https://api.groq.com/openai/v1/chat/completions');
    assert.equal(options.headers.Authorization, 'Bearer test-groq');
    assert.equal(JSON.parse(options.body).model, 'llama-3.3-70b-versatile');
    return { ok: true, json: async () => ({ choices: [{ message: { content: JSON.stringify({ sections: [{ title: 'Обзор', paragraphs: [{ text: 'Текст', source_ids: ['PMID:1'] }] }] }) } }] }) };
  };
  assert.equal(JSON.parse((await analysis.handler(event)).body).status, 'ok');
  delete process.env.GROQ_API_KEY;
});
