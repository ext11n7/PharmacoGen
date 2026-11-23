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
  assert.ok(body.trace.some(item => item.packet.method === 'initialize'));
  assert.ok(body.trace.some(item => item.packet.method === 'tools/list'));
});

test('rejects empty input and unavailable transports', async () => {
  assert.equal((await call({ source: 'cloud', tool: 'search_pharmacogenetic_literature_tool', arguments: {} })).statusCode, 400);
  assert.equal((await call({ source: 'external' })).statusCode, 503);
});
