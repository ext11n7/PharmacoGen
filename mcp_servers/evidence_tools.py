"""Rule-based review of evidence already gathered by the research agents."""

def audit_research(report: dict, dossier: dict) -> dict:
    query = report.get('normalized_query') or report.get('query') or {}
    faers, clinvar = report.get('faers') or {}, report.get('clinvar') or {}
    articles = ((dossier.get('literature') or {}).get('details') or {}).get('records') or []
    items = [
        {'label': 'FAERS', 'text': f"Источник ответил; сообщений по препарату: {faers.get('total_reports', 0)}. Сообщение не доказывает причинность или связь с геном." if faers.get('status') == 'ok' else 'Источник недоступен; повторите сбор.'},
        {'label': 'ClinVar', 'text': f"Источник ответил; записей: {clinvar.get('total_records', 0)}. Классификацию нужно читать в контексте признака." if clinvar.get('status') == 'ok' else 'Источник недоступен; повторите сбор.'},
        {'label': 'Публикации', 'text': f"Записей в досье: {len(articles)}; аннотаций: {sum(bool(x.get('abstract')) for x in articles)}. Число публикаций не измеряет силу доказательств."},
        {'label': 'Вариант', 'text': f"Указан {query['variant']}; проверьте совпадение в источнике." if query.get('variant') else 'Вариант не указан; уточните его для предметного поиска.'},
    ]
    return {'summary': 'Проверка полноты исследовательского досье', 'items': items, 'limitation': 'Наличие данных не является оценкой клинической значимости.'}


def match_variant(report: dict, dossier: dict) -> dict:
    import re
    query = report.get('normalized_query') or report.get('query') or {}
    variant = str(query.get('variant') or '').strip()
    records = (dossier.get('clinpgx') or {}).get('records') or []
    if not variant:
        return {'summary': 'Вариант не указан', 'items': [{'label': 'Следующий шаг', 'text': 'Укажите вариант, например rs1799853, и повторите исследование.'}], 'limitation': 'Без варианта сопоставление невозможно.'}
    matched = [row for row in records if variant.lower() in re.split(r'[^a-z0-9*]+', str(row.get('variant') or '').lower())]
    items = [{'label': x.get('id') or 'ClinPGx', 'text': f"{x.get('title', '')}; обозначение: {x.get('variant', '')}. Проверьте текст записи.", 'url': x.get('url', '')} for x in matched]
    if not items:
        items = [{'label': 'Совпадение не найдено', 'text': f'В {len(records)} загруженных аннотациях точное обозначение не найдено. Это не доказывает отсутствие связи.'}]
    return {'summary': f'Проверка обозначения {variant}', 'items': items, 'limitation': 'Проверяется текстовое совпадение, а не биологическая эквивалентность или клинический эффект.'}


def plan_review(report: dict, dossier: dict) -> dict:
    query = report.get('normalized_query') or report.get('query') or {}
    variant = query.get('variant')
    articles = ((dossier.get('literature') or {}).get('details') or {}).get('records') or []
    guidelines = (dossier.get('cpic') or {}).get('records') or []
    return {'summary': 'План следующего этапа исследования', 'items': [
        {'label': '1 · Уточнить вариант', 'text': f'Проверить обозначения {variant} в первичной записи.' if variant else 'Выбрать конкретный вариант гена.'},
        {'label': '2 · Изучить публикации', 'text': 'Прочитать методы и результаты найденных работ и сравнить исследуемый вариант.' if articles else 'Повторить или расширить поиск публикаций.'},
        {'label': '3 · Проверить рекомендации', 'text': 'Открыть документ CPIC и проверить его применимость.' if guidelines else 'Проверить наличие подходящего руководства CPIC.'},
        {'label': '4 · Учесть ограничения', 'text': 'Не интерпретировать сообщения FAERS как доказательство связи с геном или частоту реакции.'},
    ], 'limitation': 'План основан на наличии данных, а не на автоматической оценке качества работ.'}


def inspect_publications(report: dict, dossier: dict) -> dict:
    records = ((dossier.get('literature') or {}).get('details') or {}).get('records') or []
    items = []
    for record in records[:5]:
        types = record.get('publication_types') or []
        label = ', '.join(map(str, types)) or 'Тип публикации не указан'
        abstract = 'Аннотация доступна.' if record.get('abstract') else 'Аннотация недоступна.'
        items.append({'label': f"PMID {record.get('pmid', '—')} · {label}", 'text': f"{record.get('title', 'Без названия')}. {abstract}", 'url': record.get('url', '')})
    if not items:
        items.append({'label': 'Публикации отсутствуют', 'text': 'Повторите поиск или попробуйте запрос без варианта.'})
    return {'summary': 'Разбор найденных публикаций', 'items': items, 'limitation': 'Тип публикации указан источником и не является автоматической оценкой качества. Для вывода нужно изучить методы и полный текст.'}


def inspect_clinvar(report: dict, dossier: dict) -> dict:
    query = report.get('normalized_query') or report.get('query') or {}
    source = report.get('clinvar') or {}
    records = source.get('records') or []
    items = []
    for record in records[:5]:
        traits = record.get('traits') or []
        items.append({'label': str(record.get('accession') or record.get('uid') or 'ClinVar'), 'text': f"{record.get('title') or 'Без названия'}; классификация: {record.get('classification') or 'не указана'}; статус проверки: {record.get('review_status') or 'не указан'}; признаки: {', '.join(map(str, traits)) or 'не указаны'}.", 'url': record.get('url', '')})
    if not items:
        items.append({'label': 'Записи недоступны' if source.get('status') != 'ok' else 'Записи не найдены', 'text': 'Повторите запрос к ClinVar или уточните обозначение варианта.'})
    return {'summary': f"Разбор записей ClinVar · {query.get('gene') or 'ген'}", 'items': items, 'limitation': 'Классификация ClinVar относится к указанному признаку и не устанавливает эффект препарата. Открывайте исходные записи и проверяйте условия интерпретации.'}
