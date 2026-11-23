function analyze(name, { report = {}, dossier = {} }) {
  const query = report.normalized_query || report.query || {};
  const faers = report.faers || {}, clinvar = report.clinvar || {};
  const articles = dossier.literature?.details?.records || [];
  const annotations = dossier.clinpgx?.records || [];
  const variant = String(query.variant || '').trim();
  const items = [];
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
module.exports = { analyze };
