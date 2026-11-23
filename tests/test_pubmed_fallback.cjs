const { test } = require('node:test');
const assert = require('node:assert/strict');
const { mergePubmedXml } = require('../netlify/functions/mcp-dossier');
test('PubMed fallback maps abstracts and types by PMID and retains missing records', () => {
 const xml = '<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID Version="1">42</PMID><Article><Abstract><AbstractText Label="RESULTS">Observed <b>finding</b>.</AbstractText></Abstract><PublicationTypeList><PublicationType UI="D1">Review</PublicationType></PublicationTypeList></Article></MedlineCitation></PubmedArticle></PubmedArticleSet>';
 const records = mergePubmedXml([{pmid:'99'}, {pmid:'42'}], xml);
 assert.equal(records[0].abstract_unavailable, true);
 assert.match(records[1].abstract, /finding/);
 assert.deepEqual(records[1].publication_types, ['Review']);
});
