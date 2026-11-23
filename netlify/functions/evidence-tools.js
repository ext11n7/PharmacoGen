function evidenceRecords(report = {}, dossier = {}) {
  const literature = dossier.literature?.details?.records || [];
  const variants = report.clinvar?.records || [];
  const annotations = dossier.clinpgx?.records || [];
  return [
    ...literature.filter(x => /^\d+$/.test(String(x.pmid || ''))).map(x => ({ id: `PMID:${x.pmid}`, source: 'PubMed', title: x.title || 'Публикация', text: x.abstract || '', context: (x.publication_types || []).join(', '), url: `https://pubmed.ncbi.nlm.nih.gov/${x.pmid}/` })),
    ...variants.filter(x => /^\d+$/.test(String(x.uid || ''))).map(x => ({ id: `ClinVar:${x.uid}`, source: 'ClinVar', title: x.title || 'Вариант', text: `${x.classification || ''}; ${(x.traits || []).join(', ')}`, context: x.review_status || '', url: `https://www.ncbi.nlm.nih.gov/clinvar/variation/${x.uid}/` })),
    ...annotations.filter(x => /^PA\d+$/.test(String(x.id || ''))).map(x => ({ id: `ClinPGx:${x.id}`, source: 'ClinPGx', title: x.title || 'Аннотация', text: (x.statements || []).map(s => `${s.allele || ''}: ${s.text || ''}`).join(' '), context: `Уровень источника: ${x.evidence_level || 'не указан'}; вариант: ${x.variant || 'не указан'}`, url: `https://www.clinpgx.org/clinicalAnnotation/${x.id}` })),
  ];
}

function analyze(name, { report = {}, dossier = {}, term = '', record_a = '', record_b = '' }) {
  const query = report.normalized_query || report.query || {};
  const faers = report.faers || {}, clinvar = report.clinvar || {};
  const articles = dossier.literature?.details?.records || [];
  const annotations = dossier.clinpgx?.records || [];
  const variant = String(query.variant || '').trim();
  const items = [];
  if (name === 'search_evidence_tool') {
    const needle = term.trim().toLocaleLowerCase();
    if (needle.length < 2 || needle.length > 100) throw Error('Поисковая фраза должна содержать от 2 до 100 символов.');
    for (const row of evidenceRecords(report, dossier)) {
      const content = `${row.title}\n${row.text}\n${row.context}`;
      const position = content.toLocaleLowerCase().indexOf(needle);
      if (position >= 0) items.push({ label: `${row.source} · ${row.id}`, text: `${position > 90 ? '…' : ''}${content.slice(Math.max(0, position - 90), position + needle.length + 150).replace(/\s+/g, ' ')}${position + needle.length + 150 < content.length ? '…' : ''}`, url: row.url });
    }
    if (!items.length) items.push({ label: 'Совпадений нет', text: `В загруженных записях не найдена фраза «${term}». Это не означает, что сведений нет в источнике целиком.` });
    return { summary: `Поиск по досье: ${term}`, items, limitation: 'Ищем буквальное совпадение в загруженных названиях, аннотациях и описаниях, без перевода и поиска по полным текстам.' };
  }
  if (name === 'compare_records_tool') {
    if (!record_a || !record_b || record_a === record_b) throw Error('Выберите две разные записи.');
    const records = evidenceRecords(report, dossier);
    const selected = [record_a, record_b].map(id => records.find(row => row.id === id));
    if (selected.some(row => !row)) throw Error('Запись не найдена в текущем досье.');
    for (const row of selected) items.push({ label: `${row.source} · ${row.id}`, text: `${row.title}. ${row.context ? `${row.context}. ` : ''}${row.text ? row.text.slice(0, 1200) : 'Текст для сравнения недоступен.'}`, url: row.url });
    return { summary: 'Две записи рядом', items, limitation: 'Это сопоставление исходных полей, а не оценка согласованности или доказательство связи. Записи могут описывать разные варианты и признаки.' };
  }
  if (name === 'inspect_publications_tool') {
    for (const row of articles.slice(0, 5)) items.push({ label: `PMID ${row.pmid || '—'} · ${(row.publication_types || []).join(', ') || 'Тип не указан'}`, text: `${row.title || 'Без названия'}. ${row.abstract ? 'Аннотация доступна.' : 'Аннотация недоступна.'}`, url: row.url });
    if (!items.length) items.push({ label: 'Публикации отсутствуют', text: 'Повторите поиск или попробуйте запрос без варианта.' });
    return { summary: 'Разбор найденных публикаций', items, limitation: 'Тип публикации указан источником и не является оценкой качества. Изучите методы и полный текст.' };
  }
  if (name === 'inspect_clinvar_tool') {
    for (const row of (clinvar.records || []).slice(0, 5)) items.push({ label: row.accession || row.uid || 'ClinVar', text: `${row.title || 'Без названия'}; классификация: ${row.classification || 'не указана'}; статус проверки: ${row.review_status || 'не указан'}; признаки: ${(row.traits || []).join(', ') || 'не указаны'}.`, url: row.url });
    if (!items.length) items.push({ label: clinvar.status === 'ok' ? 'Записи не найдены' : 'Записи недоступны', text: 'Повторите запрос к ClinVar или уточните вариант.' });
    return { summary: `Разбор записей ClinVar · ${query.gene || 'ген'}`, items, limitation: 'Классификация относится к указанному признаку и не устанавливает эффект препарата. Проверяйте условия интерпретации в источнике.' };
  }
  if (name === 'audit_research_tool') {
    items.push({ label: 'FAERS', text: faers.status === 'ok' ? `Источник ответил; найдено сообщений по препарату: ${faers.total_reports ?? 0}. Наличие сообщения не доказывает причинность и связь с геном.` : 'Источник недоступен; повторите сбор.' });
    items.push({ label: 'ClinVar', text: clinvar.status === 'ok' ? `Источник ответил; найдено записей: ${clinvar.total_records ?? 0}. Классификацию нужно читать в контексте указанного признака.` : 'Источник недоступен; повторите сбор.' });
    items.push({ label: 'Публикации', text: articles.length ? `В досье ${articles.length} записей; аннотация доступна у ${articles.filter(x => x.abstract).length}. Число публикаций не измеряет силу доказательств.` : 'Записи публикаций отсутствуют или недоступны.' });
    items.push({ label: 'Вариант', text: variant ? `В запросе указан ${variant}. Совпадение требуется проверить по исходным записям.` : 'Вариант не указан: уточните его для более предметного поиска.' });
    return { summary: 'Проверка полноты исследовательского досье', items, limitation: 'Это проверка наличия данных, а не оценка клинической значимости.' };
  }
  if (name === 'match_variant_tool') {
    if (!variant) return { summary: 'Вариант не указан', items: [{ label: 'Следующий шаг', text: 'Укажите идентификатор варианта, например rs1799853, и повторите исследование.' }], limitation: 'Без варианта сопоставление невозможно.' };
    const needle = variant.toLowerCase();
    const matches = annotations.filter(x => String(x.variant || '').toLowerCase().split(/[^a-z0-9*]+/).includes(needle));
    for (const row of matches) items.push({ label: row.id || 'ClinPGx', text: `${row.title || 'Аннотация'}; обозначение в записи: ${row.variant || 'не указано'}. Проверьте аллели и текст записи.`, url: row.url });
    if (!items.length) items.push({ label: 'Совпадение не найдено', text: `Среди ${annotations.length} загруженных аннотаций ClinPGx не найдено точного обозначения ${variant}. Это не доказывает отсутствия связи: обозначения и объём выдачи могут различаться.` });
    return { summary: `Проверка обозначения ${variant}`, items, limitation: 'Проверяется только текстовое совпадение обозначения, а не биологическая эквивалентность или клинический эффект.' };
  }
  if (name === 'plan_review_tool') {
    items.push({ label: '1 · Уточнить вариант', text: variant ? `Проверить ${variant} и его обозначения в первичной записи.` : 'Выбрать конкретный вариант гена для проверки.' });
    items.push({ label: '2 · Изучить материалы', text: articles.length ? 'Прочитать методы и результаты найденных публикаций; сравнить популяцию и исследуемый вариант.' : 'Повторить поиск публикаций или расширить запрос.' });
    items.push({ label: '3 · Проверить рекомендации', text: (dossier.cpic?.records || []).length ? 'Открыть найденный документ CPIC и проверить, относится ли он к варианту и вопросу.' : 'Проверить наличие подходящего руководства CPIC или повторить запрос.' });
    items.push({ label: '4 · Проверить ограничения', text: 'Не интерпретировать сообщения FAERS как доказательство связи с геном или частоту реакции.' });
    return { summary: 'План следующего этапа исследования', items, limitation: 'План составлен по наличию данных, а не на основе автоматической оценки качества исследований.' };
  }
  throw Error('Инструмент не найден');
}
module.exports = { analyze, evidenceRecords };
