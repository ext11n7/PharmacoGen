"""Deterministic clinical calculators exposed through MCP.

The functions in this module contain no transport code. That makes the
calculations easy to test while the MCP wrappers keep the protocol boundary
explicit for the demonstration.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field


ToolResult = dict[str, Any]
Sex = Literal["female", "male"]
WeightKg = Annotated[float, Field(ge=1, le=400, description="Масса тела в килограммах")]
HeightCm = Annotated[float, Field(ge=50, le=250, description="Рост в сантиметрах")]
CreatinineMgDl = Annotated[float, Field(ge=0.1, le=20, description="Креатинин в мг/дл")]
AdultAge = Annotated[int, Field(ge=18, le=120, description="Возраст в годах")]
RespiratoryRate = Annotated[int, Field(ge=4, le=80, description="Частота дыхания в минуту")]
SystolicBp = Annotated[int, Field(ge=40, le=300, description="Систолическое давление")]
DiastolicBp = Annotated[int, Field(ge=20, le=200, description="Диастолическое давление")]
GcsEye = Annotated[int, Field(ge=1, le=4, description="Открывание глаз")]
GcsVerbal = Annotated[int, Field(ge=1, le=5, description="Речевая реакция")]
GcsMotor = Annotated[int, Field(ge=1, le=6, description="Двигательная реакция")]


def _number(value: float, name: str, minimum: float, maximum: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name}: ожидается число") from exc
    if not minimum <= number <= maximum:
        raise ValueError(f"{name}: допустимый диапазон от {minimum:g} до {maximum:g}")
    return number


def _integer(value: int, name: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{name}: ожидается целое число")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name}: ожидается целое число") from exc
    if not minimum <= number <= maximum:
        raise ValueError(f"{name}: допустимый диапазон от {minimum} до {maximum}")
    return number


def _result(
    *,
    value: float | int,
    unit: str,
    category: str,
    color: Literal["green", "yellow", "red"],
    interpretation: str,
    components: dict[str, Any],
    source: str,
) -> ToolResult:
    return {
        "value": value,
        "unit": unit,
        "category": category,
        "risk_color": color,
        "interpretation": interpretation,
        "components": components,
        "source": source,
        "disclaimer": "Расчёт предназначен для учебной демонстрации и не заменяет клиническое решение.",
    }


def calculate_bmi(weight_kg: WeightKg, height_cm: HeightCm) -> ToolResult:
    """Рассчитать индекс массы тела по массе в кг и росту в см."""
    weight = _number(weight_kg, "weight_kg", 1, 400)
    height = _number(height_cm, "height_cm", 50, 250)
    bmi = weight / (height / 100) ** 2
    if bmi < 18.5:
        category, color, interpretation = "дефицит массы", "yellow", "ИМТ ниже диапазона 18,5–24,9."
    elif bmi < 25:
        category, color, interpretation = "нормальный диапазон", "green", "ИМТ находится в диапазоне 18,5–24,9."
    elif bmi < 30:
        category, color, interpretation = "избыточная масса", "yellow", "ИМТ находится в диапазоне 25–29,9."
    else:
        category, color, interpretation = "ожирение", "red", "ИМТ равен 30 или выше."
    return _result(
        value=round(bmi, 1), unit="кг/м²", category=category, color=color,
        interpretation=interpretation, components={"масса, кг": weight, "рост, см": height},
        source="https://www.who.int/news-room/fact-sheets/detail/obesity-and-overweight",
    )


def calculate_ckd_epi(creatinine_mg_dl: CreatinineMgDl, age: AdultAge, sex: Sex) -> ToolResult:
    """Рассчитать оценочную СКФ по уравнению CKD-EPI 2021 без коэффициента расы."""
    creatinine = _number(creatinine_mg_dl, "creatinine_mg_dl", 0.1, 20)
    years = _integer(age, "age", 18, 120)
    if sex not in ("female", "male"):
        raise ValueError("sex: выберите female или male")
    k = 0.7 if sex == "female" else 0.9
    alpha = -0.241 if sex == "female" else -0.302
    egfr = 142 * min(creatinine / k, 1) ** alpha * max(creatinine / k, 1) ** -1.2 * 0.9938**years
    if egfr >= 90:
        category, color = "G1: нормальная или высокая", "green"
    elif egfr >= 60:
        category, color = "G2: слегка сниженная", "yellow"
    elif egfr >= 30:
        category, color = "G3: умеренно сниженная", "yellow"
    elif egfr >= 15:
        category, color = "G4: значительно сниженная", "red"
    else:
        category, color = "G5: крайне сниженная", "red"
    return _result(
        value=round(egfr, 1), unit="мл/мин/1,73 м²", category=category, color=color,
        interpretation="Оценочная СКФ по CKD-EPI 2021; показатель требует клинического контекста и повторной проверки.",
        components={"креатинин, мг/дл": creatinine, "возраст": years, "пол": sex, "уравнение": "CKD-EPI 2021"},
        source="https://www.kidney.org/professionals/kdoqi/gfr_calculator",
    )


def calculate_chadsvasc(
    age: AdultAge,
    sex: Sex,
    congestive_heart_failure: bool = False,
    hypertension: bool = False,
    diabetes: bool = False,
    stroke_history: bool = False,
    vascular_disease: bool = False,
) -> ToolResult:
    """Рассчитать CHA₂DS₂-VASc для учебной стратификации риска инсульта."""
    years = _integer(age, "age", 18, 120)
    if sex not in ("female", "male"):
        raise ValueError("sex: выберите female или male")
    age_points = 2 if years >= 75 else 1 if years >= 65 else 0
    score = age_points
    score += 1 if congestive_heart_failure else 0
    score += 1 if hypertension else 0
    score += 1 if diabetes else 0
    score += 2 if stroke_history else 0
    score += 1 if vascular_disease else 0
    score += 1 if sex == "female" else 0
    if score <= 1:
        category, color = "низкий балл", "green"
    elif score <= 3:
        category, color = "промежуточный балл", "yellow"
    else:
        category, color = "высокий балл", "red"
    return _result(
        value=score, unit="балл", category=category, color=color,
        interpretation="Балльная шкала поддерживает обсуждение риска при фибрилляции предсердий; решение о лечении принимает врач.",
        components={"возраст": years, "возрастные баллы": age_points, "сердечная недостаточность": congestive_heart_failure, "гипертония": hypertension, "диабет": diabetes, "инсульт/ТИА": stroke_history, "сосудистое заболевание": vascular_disease, "женский пол": sex == "female"},
        source="https://www.escardio.org/Guidelines/Clinical-Practice-Guidelines/Atrial-Fibrillation",
    )


def calculate_gcs(eye: GcsEye, verbal: GcsVerbal, motor: GcsMotor) -> ToolResult:
    """Рассчитать сумму по шкале комы Глазго."""
    eye_score = _integer(eye, "eye", 1, 4)
    verbal_score = _integer(verbal, "verbal", 1, 5)
    motor_score = _integer(motor, "motor", 1, 6)
    score = eye_score + verbal_score + motor_score
    if score >= 13:
        category, color = "легкое нарушение", "green"
    elif score >= 9:
        category, color = "умеренное нарушение", "yellow"
    else:
        category, color = "тяжелое нарушение", "red"
    return _result(
        value=score, unit="из 15", category=category, color=color,
        interpretation="Сумма GCS требует оценки в динамике и не заменяет осмотр пациента.",
        components={"открывание глаз": eye_score, "речевая реакция": verbal_score, "двигательная реакция": motor_score},
        source="https://www.glasgowcomascale.org/",
    )


def calculate_qsofa(respiratory_rate: RespiratoryRate, systolic_bp: SystolicBp, altered_mentation: bool) -> ToolResult:
    """Рассчитать qSOFA по частоте дыхания, систолическому давлению и сознанию."""
    respiratory = _integer(respiratory_rate, "respiratory_rate", 4, 80)
    pressure = _integer(systolic_bp, "systolic_bp", 40, 260)
    score = (1 if respiratory >= 22 else 0) + (1 if pressure <= 100 else 0) + (1 if altered_mentation else 0)
    color = "red" if score >= 2 else "yellow" if score == 1 else "green"
    return _result(
        value=score, unit="из 3", category="повышенная настороженность" if score >= 2 else "ниже порога qSOFA 2",
        color=color, interpretation="qSOFA не является самостоятельным диагнозом и требует оценки клинической картины.",
        components={"частота дыхания": respiratory, "систолическое давление": pressure, "изменение сознания": altered_mentation},
        source="https://www.sccm.org/SurvivingSepsisCampaign/Guidelines/Adult-Patients",
    )


def calculate_map(systolic_bp: SystolicBp, diastolic_bp: DiastolicBp) -> ToolResult:
    """Рассчитать среднее артериальное давление."""
    systolic = _integer(systolic_bp, "systolic_bp", 50, 300)
    diastolic = _integer(diastolic_bp, "diastolic_bp", 20, 200)
    if diastolic >= systolic:
        raise ValueError("diastolic_bp должно быть меньше systolic_bp")
    map_value = (systolic + 2 * diastolic) / 3
    color = "green" if 65 <= map_value <= 100 else "yellow"
    return _result(
        value=round(map_value, 1), unit="мм рт. ст.", category="обычный ориентир" if color == "green" else "вне обычного ориентира",
        color=color, interpretation="Расчётная величина для учебной оценки перфузионного давления.",
        components={"систолическое": systolic, "диастолическое": diastolic},
        source="https://www.ncbi.nlm.nih.gov/books/NBK538226/",
    )


def list_calculators() -> list[dict[str, Any]]:
    """Вернуть каталог методик, границы и единицы измерения."""
    return [
        {"name": "calculate_bmi", "title": "Индекс массы тела", "category": "общая практика", "parameters": {"weight_kg": {"type": "number", "min": 1, "max": 400, "unit": "кг"}, "height_cm": {"type": "number", "min": 50, "max": 250, "unit": "см"}}, "source": "https://www.who.int/news-room/fact-sheets/detail/obesity-and-overweight"},
        {"name": "calculate_ckd_epi", "title": "Оценочная СКФ CKD-EPI 2021", "category": "нефрология", "parameters": {"creatinine_mg_dl": {"type": "number", "min": 0.1, "max": 20, "unit": "мг/дл"}, "age": {"type": "integer", "min": 18, "max": 120, "unit": "лет"}, "sex": {"type": "enum", "values": ["female", "male"], "unit": ""}}, "source": "https://www.kidney.org/professionals/kdoqi/gfr_calculator"},
        {"name": "calculate_chadsvasc", "title": "CHA₂DS₂-VASc", "category": "кардиология", "parameters": {"age": {"type": "integer", "min": 18, "max": 120, "unit": "лет"}, "sex": {"type": "enum", "values": ["female", "male"], "unit": ""}, "congestive_heart_failure": {"type": "boolean", "default": False, "unit": ""}, "hypertension": {"type": "boolean", "default": False, "unit": ""}, "diabetes": {"type": "boolean", "default": False, "unit": ""}, "stroke_history": {"type": "boolean", "default": False, "unit": ""}, "vascular_disease": {"type": "boolean", "default": False, "unit": ""}}, "source": "https://www.escardio.org/Guidelines/Clinical-Practice-Guidelines/Atrial-Fibrillation"},
        {"name": "calculate_gcs", "title": "Шкала комы Глазго", "category": "реанимация", "parameters": {"eye": {"type": "integer", "min": 1, "max": 4, "unit": "балл"}, "verbal": {"type": "integer", "min": 1, "max": 5, "unit": "балл"}, "motor": {"type": "integer", "min": 1, "max": 6, "unit": "балл"}}, "source": "https://www.glasgowcomascale.org/"},
        {"name": "calculate_qsofa", "title": "qSOFA", "category": "реанимация", "parameters": {"respiratory_rate": {"type": "integer", "min": 4, "max": 80, "unit": "в минуту"}, "systolic_bp": {"type": "integer", "min": 40, "max": 260, "unit": "мм рт. ст."}, "altered_mentation": {"type": "boolean", "unit": ""}}, "source": "https://www.sccm.org/SurvivingSepsisCampaign/Guidelines/Adult-Patients"},
        {"name": "calculate_map", "title": "Среднее артериальное давление", "category": "реанимация", "parameters": {"systolic_bp": {"type": "integer", "min": 50, "max": 300, "unit": "мм рт. ст."}, "diastolic_bp": {"type": "integer", "min": 20, "max": 200, "unit": "мм рт. ст."}}, "source": "https://www.ncbi.nlm.nih.gov/books/NBK538226/"},
    ]
