# Развёртывание PharmacoGen

## Netlify

Проект подготовлен под Netlify: папка `web` публикуется как статический сайт, `netlify/functions/investigate.js` собирает данные FAERS и ClinVar, а `netlify/functions/mcp-dossier.js` запускает многоэтапное исследовательское досье поверх готового отчёта.

1. Откройте [Netlify](https://app.netlify.com/) и выберите `Add new site` → `Import an existing project`.
2. Подключите репозиторий с этой папкой или загрузите проект через Netlify CLI.
3. Укажите корень проекта, оставьте настройки из `netlify.toml` и запустите deploy.

Через CLI:

```bash
npm install -g netlify-cli
netlify login
netlify init
netlify deploy --prod
```

`netlify.toml` уже задаёт `web` как publish-директорию, подключает `netlify/functions` и перенаправляет `/api/investigate` и `/api/mcp/dossier` в функции. На опубликованном сайте досье выполняется serverless-функцией; локально доступны полноценные MCP-транспорты stdio и network.

После публикации проверьте адрес сайта и кнопку «Собрать доказательства». Для Netlify не нужны отдельные ключи API: используются открытые запросы к openFDA и NCBI.

## Запуск на VPS через Docker

```bash
docker compose up -d --build
```

После запуска приложение будет доступно на порту `8503`:

```text
http://SERVER_IP:8503
```

Проверка состояния:

```bash
curl http://127.0.0.1:8503/api/health
```

Ожидаемый ответ:

```json
{"status":"ok"}
```

## Запуск без Docker

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python web_server.py
```

Для доступа из сети запустите сервер с `PHARMACOGEN_HOST=0.0.0.0` и откройте порт `8503` в файрволе.

## Что нужно для публичного URL

Для настоящего внешнего сервера нужны IP-адрес или домен и доступ к нему по SSH либо панель выбранного хостинга. В этом комплекте уже есть Docker-конфигурация, поэтому запуск на VPS сводится к копированию папки и команде `docker compose up -d --build`.

## Проверка проекта

```bash
.venv/bin/pytest -q
```

Приложение использует открытые API openFDA FAERS и NCBI ClinVar. Результат является исследовательским, не является медицинской рекомендацией и не доказывает причинность.
