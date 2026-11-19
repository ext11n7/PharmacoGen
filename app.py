from __future__ import annotations

import json
from typing import Any

import streamlit as st

from agents import run_investigation
from mcp_clients.router import MCPClientError, call_mcp_tool, list_mcp_catalog


st.set_page_config(page_title="PharmacoGen | обзор доказательств", page_icon="PG", layout="wide", initial_sidebar_state="collapsed")

TEXT = {
    "ru": {
        "language":"Язык","theme":"Тема","light":"Светлая","dark":"Тёмная","subtitle":"обзор фармакогенетических данных","workspace":"РАБОЧАЯ ОБЛАСТЬ","research":"Исследование","research_help":"Укажите препарат и ген, чтобы собрать проверяемый срез из двух открытых источников.","drug":"Препарат","drug_placeholder":"Например, warfarin","gene":"Ген","gene_placeholder":"Например, CYP2C9","run":"Собрать данные","sources":"Источники","source_data":"Открытые данные","source_openfda":"Сигналы безопасности","source_clinvar":"Генетические варианты","research_note":"Результат предназначен для исследования. Он не является медицинской рекомендацией и не доказывает причинность.","empty_title":"Начните исследование","empty_text":"В левой панели задайте пару «препарат + ген». Система нормализует запрос, параллельно проверит FAERS и ClinVar и покажет, на чём основан итог.","step_one":"Нормализация","step_two":"Сбор источников","step_three":"Синтез","step_one_text":"Приводим сущности к единому виду","step_two_text":"Сверяем два открытых API","step_three_text":"Формируем осторожный вывод","busy":"Собираем данные из источников","result":"Результат исследования","exploratory":"Есть сигнал","weak":"Сигнал слабый","incomplete":"Данные неполные","evidence":"Доказательства","workflow":"Ход обработки","limits":"Ограничения","reports":"сообщений","records":"записей","pathogenic":"патогенных","total":"Всего по запросу","preview":"В превью","serious":"серьёзных сообщений","frequent":"Частые реакции","variants_for_pair":"по паре ген + препарат","shown":"Показано","classification":"Классификация","review":"Проверка","evaluated":"Оценка","traits":"Признаки","source":"Источник","open_source":"Открыть источник","why":"Основание вывода","download":"Скачать отчёт JSON","generated":"Сформирован","no_data":"нет данных","agent_done":"готово","normalization":"Нормализация сущностей","faers_agent":"Сбор данных FAERS","clinvar_agent":"Поиск в ClinVar","synthesis_agent":"Синтез результата","normalization_detail":"Препарат и ген приведены к единому виду","faers_detail":"Получены сообщения о безопасности","clinvar_detail":"Получены варианты и их классификации","synthesis_detail":"Результаты сопоставлены с ограничениями","limitations":["FAERS основан на спонтанных сообщениях: их число не равно частоте и не доказывает причинность.","ClinVar описывает клиническую интерпретацию вариантов, но сам по себе не доказывает фармакогенетический эффект.","В этой версии нет данных пациента, дозировки, временной последовательности и поправки на сопутствующие препараты."],"about":"PharmacoGen","about_text":"Мультиагентный сбор фармакогенетических сигналов из FAERS и ClinVar."},
    "en": {
        "language":"Language","theme":"Theme","light":"Light","dark":"Dark","subtitle":"pharmacogenetic evidence review","workspace":"WORKSPACE","research":"Investigation","research_help":"Enter a drug and a gene to assemble a checkable view from two open sources.","drug":"Drug","drug_placeholder":"For example, warfarin","gene":"Gene","gene_placeholder":"For example, CYP2C9","run":"Collect data","sources":"Sources","source_data":"Open data","source_openfda":"Safety signals","source_clinvar":"Genetic variants","research_note":"For research use only. This result is not medical advice and does not prove causality.","empty_title":"Start an investigation","empty_text":"Set a drug + gene pair in the left panel. The system normalizes the query, checks FAERS and ClinVar in parallel, and explains the basis of its result.","step_one":"Normalize","step_two":"Collect sources","step_three":"Synthesize","step_one_text":"Unify the entities","step_two_text":"Check two open APIs","step_three_text":"Write a cautious result","busy":"Collecting data from sources","result":"Investigation result","exploratory":"Signal found","weak":"Weak signal","incomplete":"Incomplete data","evidence":"Evidence","workflow":"Processing","limits":"Limitations","reports":"reports","records":"records","pathogenic":"pathogenic","total":"Total for query","preview":"In preview","serious":"serious reports","frequent":"Frequent reactions","variants_for_pair":"for gene + drug pair","shown":"Shown","classification":"Classification","review":"Review","evaluated":"Evaluated","traits":"Traits","source":"Source","open_source":"Open source","why":"Basis of the result","download":"Download JSON report","generated":"Generated","no_data":"no data","agent_done":"done","normalization":"Entity normalization","faers_agent":"FAERS collection","clinvar_agent":"ClinVar search","synthesis_agent":"Result synthesis","normalization_detail":"Drug and gene were normalized","faers_detail":"Safety reports were collected","clinvar_detail":"Variants and classifications were collected","synthesis_detail":"Results were compared with limitations","limitations":["FAERS is based on spontaneous reports: report count is not frequency and does not prove causality.","ClinVar describes clinical variant interpretation, but does not prove a pharmacogenetic effect by itself.","This version has no patient-level data, dose, time sequence, or adjustment for concomitant drugs."],"about":"PharmacoGen","about_text":"Multi-agent collection of pharmacogenetic signals from FAERS and ClinVar."},
}


def tr(key: str) -> Any:
    return TEXT[st.session_state.language][key]


def num(value: int | float) -> str:
    return f"{value:,}".replace(",", " ") if st.session_state.language == "ru" else f"{value:,}"


def wordmark(text: str) -> str:
    return "".join(f'<span class="pg-letter">{char}</span>' for char in text)


def styles() -> None:
    dark = st.session_state.theme == "dark"
    color = {"bg":"#111415" if dark else "#F7F8F8", "surface":"#181D1F" if dark else "#FFFFFF", "alt":"#202628" if dark else "#F0F2F2", "ink":"#F0F4F3" if dark else "#172224", "muted":"#99A6A7" if dark else "#6D7A7C", "line":"#303A3D" if dark else "#DCE3E3", "strong":"#4A5658" if dark else "#C8D1D2"}
    css = """
    <style>
    :root { color-scheme: __SCHEME__; }
    html,body,[data-testid="stAppViewContainer"] { background:__BG__; color:__INK__; }
    [data-testid="stHeader"] { background:transparent; }
    [data-testid="stSidebar"] { display:none; }
    .block-container { max-width:1440px; padding:24px 42px 48px; }
    .pg-header { display:flex; align-items:center; justify-content:space-between; gap:24px; padding-bottom:18px; border-bottom:1px solid __LINE__; margin-bottom:30px; }
    .pg-brand { display:flex; align-items:center; gap:12px; }
    .pg-mark { display:grid; place-items:center; width:34px; height:34px; border:1px solid #0F766E; border-radius:8px; color:#0F766E; font-size:11px; font-weight:800; }
    .pg-brand-name { color:__INK__; font-size:16px; font-weight:760; }
    .pg-letter { display:inline-block; transition:color .18s ease, transform .18s ease, text-shadow .18s ease; }
    .pg-letter:hover { color:transparent; -webkit-text-stroke:1px #0F766E; text-shadow:0 0 10px rgba(15,118,110,.24); transform:translateY(-2px) rotate(-2deg); }
    .pg-brand-sub { color:__MUTED__; font-size:12px; margin-top:3px; }
    .pg-label { color:__MUTED__; font-size:11px; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }
    .pg-kicker { color:#0F766E; font-size:11px; font-weight:800; letter-spacing:.1em; text-transform:uppercase; margin:2px 0 9px; }
    .pg-panel-title { color:__INK__; font-size:14px; font-weight:760; margin-bottom:5px; }
    .pg-panel-copy { color:__MUTED__; font-size:12px; line-height:1.5; margin-bottom:18px; }
    .pg-source { display:flex; align-items:center; gap:10px; border-top:1px solid __LINE__; padding:10px 0; }
    .pg-source-icon { display:grid; place-items:center; width:25px; height:25px; border:1px solid __STRONG__; border-radius:6px; color:#0F766E; font-size:9px; font-weight:800; }
    .pg-source-name { color:__INK__; font-size:12px; font-weight:700; }
    .pg-source-type { color:__MUTED__; font-size:11px; margin-top:2px; }
    .pg-note { color:__MUTED__; border-left:2px solid #D99A46; padding:8px 0 8px 11px; font-size:12px; line-height:1.5; margin-top:18px; }
    .pg-empty { border-top:1px solid __LINE__; border-bottom:1px solid __LINE__; padding:76px 30px 74px; animation:pg-enter .24s ease-out both; }
    .pg-empty-mark { color:#0F766E; font-size:11px; font-weight:800; letter-spacing:.1em; margin-bottom:14px; }
    .pg-empty h1 { color:__INK__; font-size:27px; letter-spacing:-.03em; margin:0 0 10px; }
    .pg-empty p { color:__MUTED__; max-width:590px; font-size:14px; line-height:1.6; margin:0; }
    .pg-steps { display:grid; grid-template-columns:repeat(3,1fr); gap:24px; margin-top:50px; }
    .pg-step { border-top:1px solid __STRONG__; padding-top:11px; }
    .pg-step-num { color:#0F766E; font-size:11px; font-weight:800; }
    .pg-step-title { color:__INK__; font-size:13px; font-weight:760; margin-top:8px; }
    .pg-step-copy { color:__MUTED__; font-size:12px; line-height:1.45; margin-top:4px; }
    .pg-result-head { display:flex; align-items:flex-start; justify-content:space-between; gap:18px; padding-bottom:17px; border-bottom:1px solid __LINE__; animation:pg-enter .24s ease-out both; }
    .pg-result-title { color:__INK__; font-size:21px; line-height:1.25; letter-spacing:-.02em; margin:0; }
    .pg-query { color:__MUTED__; font:12px ui-monospace,SFMono-Regular,Menlo,monospace; margin-top:7px; }
    .pg-status { display:inline-flex; align-items:center; gap:7px; color:__INK__; background:__ALT__; border:1px solid __LINE__; border-radius:999px; padding:6px 9px; font-size:11px; font-weight:760; white-space:nowrap; }
    .pg-dot { width:7px; height:7px; border-radius:50%; background:#D99A46; }
    .pg-stat-row { display:grid; grid-template-columns:repeat(4,1fr); border-bottom:1px solid __LINE__; margin-bottom:22px; }
    .pg-stat { padding:17px 16px 17px 0; border-right:1px solid __LINE__; margin-right:16px; }
    .pg-stat:last-child { border-right:0; margin-right:0; }
    .pg-stat-label { color:__MUTED__; font-size:11px; }
    .pg-stat-value { color:__INK__; font-size:17px; font-weight:760; margin-top:5px; }
    .pg-stat-value small { color:__MUTED__; font-size:11px; font-weight:500; }
    .pg-source-block { border:1px solid __LINE__; background:__SURFACE__; padding:16px; animation:pg-enter .24s ease-out both; }
    .pg-source-heading { color:__INK__; font-size:14px; font-weight:760; }
    .pg-source-caption { color:__MUTED__; font-size:11px; margin-top:4px; }
    .pg-source-number { color:__INK__; font-size:19px; font-weight:760; margin-top:15px; }
    .pg-source-number small { color:__MUTED__; font-size:11px; font-weight:500; }
    .pg-reason { color:__MUTED__; border-top:1px solid __LINE__; margin-top:15px; padding-top:12px; font-size:12px; line-height:1.5; }
    .pg-subheading { color:__INK__; font-size:14px; font-weight:760; margin:26px 0 9px; }
    .pg-agent { display:grid; grid-template-columns:22px 1fr auto; align-items:center; gap:9px; border-top:1px solid __LINE__; padding:12px 0; }
    .pg-agent-index { color:#0F766E; font-size:11px; font-weight:800; }
    .pg-agent-name { color:__INK__; font-size:13px; font-weight:700; }
    .pg-agent-detail { color:__MUTED__; font-size:11px; margin-top:3px; }
    .pg-agent-state { color:#0F766E; font-size:10px; font-weight:800; text-transform:uppercase; }
    .pg-limit { color:__MUTED__; border-top:1px solid __LINE__; padding:13px 0; font-size:13px; line-height:1.55; }
    .pg-footer { color:__MUTED__; border-top:1px solid __LINE__; margin-top:34px; padding-top:15px; font-size:11px; }
    [data-testid="stVerticalBlockBorderWrapper"] { background:__SURFACE__; border-color:__LINE__; border-radius:10px; }
    [data-testid="stTextInput"] label,[data-testid="stSelectbox"] label { color:__MUTED__ !important; font-size:11px !important; font-weight:700 !important; }
    [data-testid="stTextInput"] input { background:__ALT__; color:__INK__; border:1px solid __LINE__; border-radius:7px; font-size:13px; transition:border-color .15s ease,box-shadow .15s ease; }
    [data-testid="stTextInput"] input:focus { border-color:#0F766E; box-shadow:0 0 0 2px rgba(15,118,110,.14); }
    [data-testid="stSelectbox"]>div>div { background:__SURFACE__; color:__INK__; border-color:__LINE__; border-radius:7px; font-size:12px; }
    .stButton>button,[data-testid="stFormSubmitButton"]>button { min-height:40px; background:#0F766E; color:#FFF; border:1px solid #0F766E; border-radius:7px; font-size:12px; font-weight:760; transition:background .15s ease,transform .15s ease,box-shadow .15s ease; }
    .stButton>button:hover,[data-testid="stFormSubmitButton"]>button:hover { background:#0B625D; color:#FFF; transform:translateY(-1px); box-shadow:0 5px 12px rgba(15,118,110,.18); }
    .stTabs [data-baseweb="tab-list"] { gap:2px; border-bottom:1px solid __LINE__; }
    .stTabs [data-baseweb="tab"] { color:__MUTED__; font-size:12px; padding:9px 12px; }
    .stTabs [aria-selected="true"] { color:__INK__; }
    .stTabs [data-baseweb="tab-highlight"] { background:#0F766E; }
    [data-testid="stDataFrame"] { border:1px solid __LINE__; }
    .stDownloadButton>button { background:transparent; color:__INK__; border:1px solid __STRONG__; border-radius:7px; font-size:12px; }
    @keyframes pg-enter { from { opacity:0; transform:translateY(4px); } to { opacity:1; transform:translateY(0); } }
    @media(max-width:850px) { .block-container { padding:18px 18px 36px; } .pg-header { align-items:flex-start; flex-direction:column; } .pg-steps { grid-template-columns:1fr; gap:16px; margin-top:34px; } .pg-stat-row { grid-template-columns:repeat(2,1fr); } .pg-stat:nth-child(2) { border-right:0; } }
    </style>
    """
    css = css.replace("__SCHEME__", "dark" if dark else "light")
    for key, value in color.items():
        css = css.replace(f"__{key.upper()}__", value)
    st.markdown(css, unsafe_allow_html=True)


if "language" not in st.session_state:
    st.session_state.language = "ru"
if "theme" not in st.session_state:
    st.session_state.theme = "light"
styles()

header, lang_col, theme_col = st.columns([6.8, 1.25, 1.25], vertical_alignment="center")
with header:
    st.markdown(f'<header class="pg-header"><div class="pg-brand"><div class="pg-mark">PG</div><div><div class="pg-brand-name pg-wordmark">{wordmark("PharmacoGen")}</div><div class="pg-brand-sub">{tr("subtitle")}</div></div></div><div class="pg-label">{tr("workspace")}</div></header>', unsafe_allow_html=True)
with lang_col:
    st.session_state.language = st.selectbox(tr("language"), ["ru", "en"], index=0 if st.session_state.language == "ru" else 1, format_func=lambda x: "Русский" if x == "ru" else "English", key="language_select")
with theme_col:
    st.session_state.theme = st.selectbox(tr("theme"), ["light", "dark"], index=0 if st.session_state.theme == "light" else 1, format_func=lambda x: tr("light") if x == "light" else tr("dark"), key="theme_select")
styles()

left, main = st.columns([0.29, 0.71], gap="large")
with left:
    st.markdown(f'<div class="pg-label">{tr("research")}</div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(f'<div class="pg-panel-title">{tr("research")}</div><div class="pg-panel-copy">{tr("research_help")}</div>', unsafe_allow_html=True)
        with st.form("research_form", clear_on_submit=False):
            drug = st.text_input(tr("drug"), value="warfarin", placeholder=tr("drug_placeholder"))
            gene = st.text_input(tr("gene"), value="CYP2C9", placeholder=tr("gene_placeholder"))
            submit = st.form_submit_button(tr("run"), width="stretch")
    st.markdown(f'<div class="pg-label" style="margin-top:28px;">{tr("sources")}</div>', unsafe_allow_html=True)
    with st.container(border=True):
        for short, title, url in [("FDA", "openFDA FAERS", "https://open.fda.gov/apis/drug/event/"), ("NCBI", "NCBI ClinVar", "https://www.ncbi.nlm.nih.gov/clinvar/")]:
            st.markdown(f'<div class="pg-source"><div class="pg-source-icon">{short}</div><div><div class="pg-source-name">{title}</div><div class="pg-source-type">{tr("source_data")}</div></div></div>', unsafe_allow_html=True)
            st.link_button(tr("open_source"), url, width="content")
    st.markdown(f'<div class="pg-note">{tr("research_note")}</div>', unsafe_allow_html=True)

if submit:
    with st.spinner(tr("busy")):
        st.session_state.report = run_investigation(drug, gene)
report = st.session_state.get("report")

with main:
    if report is None:
        st.markdown(f'<section class="pg-empty"><div class="pg-empty-mark">PHARMACOGEN / 01</div><h1>{tr("empty_title")}</h1><p>{tr("empty_text")}</p><div class="pg-steps"><div class="pg-step"><div class="pg-step-num">01</div><div class="pg-step-title">{tr("step_one")}</div><div class="pg-step-copy">{tr("step_one_text")}</div></div><div class="pg-step"><div class="pg-step-num">02</div><div class="pg-step-title">{tr("step_two")}</div><div class="pg-step-copy">{tr("step_two_text")}</div></div><div class="pg-step"><div class="pg-step-num">03</div><div class="pg-step-title">{tr("step_three")}</div><div class="pg-step-copy">{tr("step_three_text")}</div></div></div></section>', unsafe_allow_html=True)
    else:
        faers, clinvar, synthesis = report.faers, report.clinvar, report.synthesis
        drug_norm, gene_norm = report.normalized_query["drug"], report.normalized_query["gene"]
        confidence_key = synthesis.get("confidence", "incomplete")
        confidence_label = tr({"exploratory":"exploratory", "weak":"weak", "incomplete":"incomplete"}.get(confidence_key, "incomplete"))
        if confidence_key == "exploratory":
            headline = f"Есть основание проверить связь {drug_norm} + {gene_norm}." if st.session_state.language == "ru" else f"There is a reason to check {drug_norm} + {gene_norm}."
        elif confidence_key == "weak":
            headline = "Данные собраны, но сильная гипотеза не подтверждена." if st.session_state.language == "ru" else "The data is collected, but a strong hypothesis is not supported."
        else:
            headline = "Отчёт неполный: один или оба источника недоступны." if st.session_state.language == "ru" else "The report is incomplete: one or both sources are unavailable."
        st.markdown(f'<div class="pg-result-head"><div><div class="pg-kicker">{tr("result")}</div><h1 class="pg-result-title">{headline}</h1><div class="pg-query">{drug_norm}  +  {gene_norm}</div></div><div class="pg-status"><span class="pg-dot"></span>{confidence_label}</div></div>', unsafe_allow_html=True)
        faers_total = num(faers.get("total_reports", 0)) if faers.get("status") == "ok" else tr("no_data")
        clinvar_total = num(clinvar.get("total_records", 0)) if clinvar.get("status") == "ok" else tr("no_data")
        pathogenic_total = num(clinvar.get("pathogenic_records", 0)) if clinvar.get("status") == "ok" else tr("no_data")
        stats = [("FAERS", faers_total, tr("reports")), ("ClinVar", clinvar_total, tr("records")), ("ClinVar", pathogenic_total, tr("pathogenic")), (tr("result"), confidence_label, "")]
        st.markdown('<div class="pg-stat-row">' + ''.join(f'<div class="pg-stat"><div class="pg-stat-label">{a}</div><div class="pg-stat-value">{b} <small>{c}</small></div></div>' for a,b,c in stats) + '</div>', unsafe_allow_html=True)
        tab_evidence, tab_workflow, tab_limits = st.tabs([tr("evidence"), tr("workflow"), tr("limits")])
        with tab_evidence:
            faers_col, clinvar_col = st.columns(2, gap="large")
            with faers_col:
                st.markdown(f'<div class="pg-source-block"><div class="pg-source-heading">FAERS · {tr("source_openfda")}</div><div class="pg-source-caption">openFDA</div><div class="pg-source-number">{faers_total} <small>{tr("reports")}</small></div></div>', unsafe_allow_html=True)
                if faers.get("status") == "ok":
                    st.markdown(f'<div class="pg-reason"><b>{tr("preview")}:</b> {faers["serious_preview"]} {tr("serious")} из {faers["preview_reports"]}</div>', unsafe_allow_html=True)
                    reaction_label = "Реакция" if st.session_state.language == "ru" else "Reaction"
                    count_label = "Количество" if st.session_state.language == "ru" else "Count"
                    st.markdown(f'<div class="pg-subheading">{tr("frequent")}</div>', unsafe_allow_html=True)
                    st.dataframe([{reaction_label:x["term"], count_label:x["count"]} for x in faers.get("top_reactions", [])], width="stretch", hide_index=True)
                    st.link_button(tr("open_source"), faers["source"], width="content")
                else: st.error(faers.get("error", tr("no_data")))
            with clinvar_col:
                st.markdown(f'<div class="pg-source-block"><div class="pg-source-heading">ClinVar · {tr("source_clinvar")}</div><div class="pg-source-caption">NCBI</div><div class="pg-source-number">{clinvar_total} <small>{tr("variants_for_pair")}</small></div></div>', unsafe_allow_html=True)
                if clinvar.get("status") == "ok":
                    st.markdown(f'<div class="pg-reason"><b>{tr("shown")}:</b> {num(clinvar["returned_records"])} {tr("records")}</div>', unsafe_allow_html=True)
                    variant_label = "Вариант" if st.session_state.language == "ru" else "Variant"
                    rows = [{variant_label:x.get("title", ""), tr("classification"):x.get("classification", ""), tr("review"):x.get("review_status", ""), tr("evaluated"):x.get("last_evaluated", ""), tr("traits"): ", ".join(x.get("traits", [])), tr("source"):x.get("url", "")} for x in clinvar.get("records", [])]
                    st.dataframe(rows, width="stretch", hide_index=True, column_config={tr("source"):st.column_config.LinkColumn(tr("source"))})
                    st.link_button(tr("open_source"), clinvar["source"], width="content")
                else: st.error(f"ClinVar: {clinvar.get('error', tr('no_data'))}")
            st.markdown(f'<div class="pg-subheading">{tr("why")}</div>', unsafe_allow_html=True)
            serious_rate = faers.get("serious_rate")
            reasons = [f"FAERS: {faers_total} сообщений по препарату {drug_norm}." if st.session_state.language == "ru" else f"FAERS: {faers_total} reports for {drug_norm}.", f"ClinVar: {pathogenic_total} записей с классификацией pathogenic/likely pathogenic для {gene_norm}." if st.session_state.language == "ru" else f"ClinVar: {pathogenic_total} pathogenic/likely pathogenic records for {gene_norm}.", f"Доля серьёзных сообщений в превью FAERS: {serious_rate:.1%}." if st.session_state.language == "ru" and serious_rate is not None else f"Serious reports in the FAERS preview: {serious_rate:.1%}." if serious_rate is not None else f"{tr('serious')}: {tr('no_data')}."]
            for reason in reasons: st.markdown(f'<div class="pg-reason">{reason}</div>', unsafe_allow_html=True)
        with tab_workflow:
            agents = [(tr("normalization"),tr("normalization_detail")),(tr("faers_agent"),tr("faers_detail")),(tr("clinvar_agent"),tr("clinvar_detail")),(tr("synthesis_agent"),tr("synthesis_detail"))]
            for index,(name,detail) in enumerate(agents,1): st.markdown(f'<div class="pg-agent"><div class="pg-agent-index">0{index}</div><div><div class="pg-agent-name">{name}</div><div class="pg-agent-detail">{detail}</div></div><div class="pg-agent-state">{tr("agent_done")}</div></div>', unsafe_allow_html=True)
        with tab_limits:
            for limitation in tr("limitations"): st.markdown(f'<div class="pg-limit">{limitation}</div>', unsafe_allow_html=True)
            st.caption(f"{tr('generated')}: {report.generated_at[:19].replace('T',' ')} UTC")
        st.download_button(tr("download"), data=json.dumps(report.to_dict(), ensure_ascii=False, indent=2), file_name="pharmacogen_report.json", mime="application/json", width="content")


st.markdown("## MCP-лаборатория")
st.caption("Три транспорта MCP, динамическая форма инструментов и инспектор JSON-RPC")
try:
    mcp_catalog = list_mcp_catalog()
    source_options = {item["title"]: item["id"] for item in mcp_catalog["sources"]}
    source_title = st.selectbox("Источник MCP", list(source_options), key="mcp_source_select")
    source_id = source_options[source_title]
    available_tools = mcp_catalog["external_tools"] if source_id == "external" else mcp_catalog["local_tools"]
    search_text = st.text_input("Поиск инструмента", placeholder="Например, нефрология или CKD", key="mcp_tool_search")
    search_lower = search_text.casefold().strip()
    filtered_tools = [tool for tool in available_tools if not search_lower or search_lower in f"{tool.get('title', '')} {tool.get('name', '')} {tool.get('category', '')}".casefold()]
    if not filtered_tools:
        st.warning("Инструменты по этому запросу не найдены.")
    else:
        tool_labels = {f"{tool.get('title', tool['name'])} · {tool.get('category', '')}": tool for tool in filtered_tools}
        selected_label = st.selectbox("Инструмент", list(tool_labels), key="mcp_tool_select")
        selected_tool = tool_labels[selected_label]
        st.caption(f"`{selected_tool['name']}` · источник методики: {selected_tool.get('source', 'MCP')}")
        schema = selected_tool.get("inputSchema", {})
        properties = schema.get("properties", {})
        with st.form("mcp_tool_form", clear_on_submit=False):
            arguments: dict[str, Any] = {}
            for name, definition in properties.items():
                label = name.replace("_", " ")
                field_type = definition.get("type", "string")
                if field_type == "boolean":
                    arguments[name] = st.checkbox(label, value=bool(definition.get("default", False)))
                elif field_type in {"integer", "number"}:
                    minimum = definition.get("min", definition.get("minimum", 0))
                    maximum = definition.get("max", definition.get("maximum", 100))
                    default = definition.get("default", minimum)
                    arguments[name] = st.number_input(label, min_value=float(minimum), max_value=float(maximum), value=float(default), step=1.0 if field_type == "integer" else 0.1)
                    if field_type == "integer":
                        arguments[name] = int(arguments[name])
                elif definition.get("enum") or definition.get("values"):
                    values = definition.get("enum") or definition.get("values")
                    arguments[name] = st.selectbox(label, values)
                else:
                    arguments[name] = st.text_input(label, value=str(definition.get("default", "")))
            mcp_submit = st.form_submit_button("Вызвать через MCP", width="stretch")
        if mcp_submit:
            with st.spinner("MCP-сервер обрабатывает tools/call…"):
                try:
                    st.session_state.mcp_result = call_mcp_tool(source_id, selected_tool["name"], arguments)
                except MCPClientError as exc:
                    st.session_state.mcp_result = {"error": str(exc)}
                except Exception as exc:
                    st.session_state.mcp_result = {"error": f"Непредвиденная ошибка MCP: {exc}"}
        mcp_result = st.session_state.get("mcp_result")
        if mcp_result:
            if mcp_result.get("error"):
                st.error(mcp_result["error"])
            else:
                result_payload = mcp_result.get("result", {})
                st.markdown("### Результат инструмента")
                st.json(result_payload)
                with st.expander("Инспектор JSON-RPC", expanded=True):
                    st.markdown("**Трасса `initialize` → `tools/list` → `tools/call`**")
                    st.json(mcp_result.get("trace", []))
                    st.markdown("**Схема выбранного инструмента**")
                    st.json(mcp_result.get("tool", {}))
except Exception as exc:
    st.error(f"Каталог MCP недоступен: {exc}")

st.markdown(f'<div class="pg-footer">{tr("about")}: {tr("about_text")} · openFDA FAERS · NCBI ClinVar</div>', unsafe_allow_html=True)
