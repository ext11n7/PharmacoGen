"""Deterministic teaching calculators required by Practical assignment 2.

Bounds below are application input limits, not definitions of normal physiology.
No patient values are silently invented; example values are explicitly labelled.
"""
from typing import Annotated, Literal
from pydantic import Field

Weight = Annotated[float, Field(strict=True, ge=20, le=300, description='Масса тела взрослого, кг', json_schema_extra={'unit': 'кг', 'examples': [70]})]
Height = Annotated[float, Field(strict=True, ge=100, le=250, description='Рост взрослого, см', json_schema_extra={'unit': 'см', 'examples': [175]})]
Age = Annotated[int, Field(strict=True, ge=18, le=120, description='Возраст взрослого, лет', json_schema_extra={'unit': 'лет', 'examples': [60]})]
Creatinine = Annotated[float, Field(strict=True, ge=0.2, le=20, description='Креатинин сыворотки, мг/дл; не мкмоль/л', json_schema_extra={'unit': 'мг/дл', 'examples': [1.0]})]

LIMITATION = 'Учебный расчёт, не персональная рекомендация. При пропущенном или неизмеримом компоненте расчёт не выполняют.'

def result(title, value, unit, components, formula, interpretation, source, category, status='neutral'):
    return {'title': title, 'value': value, 'unit': unit, 'components': components, 'formula': formula, 'interpretation': interpretation, 'source_url': source, 'category': category, 'status': status, 'limitation': LIMITATION}

def calculate_bmi(weight_kg: Weight, height_cm: Height) -> dict:
    """ИМТ / BMI: учебная оценка массы тела взрослого по росту и массе."""
    value = weight_kg / (height_cm / 100) ** 2
    label = 'Недостаточная масса' if value < 18.5 else 'Диапазон 18,5–24,9' if value < 25 else 'Избыточная масса' if value < 30 else 'Диапазон ожирения'
    return result('Индекс массы тела', round(value, 2), 'кг/м²', {'масса, кг': weight_kg, 'рост, см': height_cm}, 'масса / (рост в метрах)²', label + '. Скрининговый показатель; не учитывает состав тела, беременность и индивидуальный контекст.', 'https://www.cdc.gov/bmi/adult-calculator/bmi-categories.html', 'Общая медицина', 'green' if 18.5 <= value < 25 else 'yellow')

def calculate_gcs(eye: Literal[1, 2, 3, 4], verbal: Literal[1, 2, 3, 4, 5], motor: Literal[1, 2, 3, 4, 5, 6]) -> dict:
    """Шкала комы Глазго / GCS: сумма трёх оцениваемых компонентов E, V, M."""
    return result('Шкала Глазго', eye + verbal + motor, 'баллов', {'E — открывание глаз': eye, 'V — речевой ответ': verbal, 'M — двигательный ответ': motor}, 'GCS = E + V + M', 'Диапазон суммы 3–15. Если компонент нельзя оценить (например, речь при интубации), не подставляйте ему произвольный балл. Всегда сообщайте отдельные E, V и M.', 'https://www.glasgowcomascale.org/what-is-gcs/', 'Реанимация')

def calculate_creatinine_clearance(age_years: Age, weight_kg: Weight, creatinine_mg_dl: Creatinine, sex: Literal['male', 'female']) -> dict:
    """Клиренс креатинина Cockcroft–Gault: взрослые, стабильный креатинин, не расчёт дозы."""
    factor = 0.85 if sex == 'female' else 1.0
    value = (140 - age_years) * weight_kg / (72 * creatinine_mg_dl) * factor
    return result('Клиренс креатинина Cockcroft–Gault', round(value, 2), 'мл/мин', {'возраст': age_years, 'масса, кг': weight_kg, 'креатинин, мг/дл': creatinine_mg_dl, 'коэффициент формулы': factor}, '(140 − возраст) × масса / (72 × креатинин); × 0,85 для female', 'Оценка клиренса креатинина, не нормированная СКФ. Не применять при нестабильном креатинине; выбор массы при ожирении требует отдельной методики. Индивидуальная доза не рассчитывается.', 'https://pubmed.ncbi.nlm.nih.gov/1244564/', 'Нефрология')

def calculate_bsa(weight_kg: Weight, height_cm: Height) -> dict:
    """Площадь поверхности тела / BSA по Mosteller, без подбора доз."""
    return result('Площадь поверхности тела Mosteller', round((weight_kg * height_cm / 3600) ** 0.5, 3), 'м²', {'масса, кг': weight_kg, 'рост, см': height_cm}, '√(рост × масса / 3600)', 'Антропометрическая оценка площади поверхности тела. Не является назначением или расчётом дозы.', 'https://pubmed.ncbi.nlm.nih.gov/3657876/', 'Общая медицина')

def calculate_shock_index(heart_rate: Annotated[int, Field(strict=True, ge=20, le=250, description='Частота сердечных сокращений, уд/мин', json_schema_extra={'unit': 'уд/мин', 'examples': [80]})], systolic_bp: Annotated[float, Field(strict=True, ge=40, le=260, description='Систолическое давление, мм рт. ст.', json_schema_extra={'unit': 'мм рт. ст.', 'examples': [120]})]) -> dict:
    """Шоковый индекс / Shock index: отношение ЧСС к систолическому давлению."""
    return result('Шоковый индекс', round(heart_rate / systolic_bp, 3), 'отношение', {'ЧСС': heart_rate, 'систолическое АД': systolic_bp}, 'ЧСС / систолическое АД', 'Одиночное отношение не устанавливает шок. Интерпретация зависит от возраста, лекарств, беременности и клинической ситуации; автоматическая стратификация риска не выполняется.', 'https://pubmed.ncbi.nlm.nih.gov/?term=shock+index+heart+rate+systolic+blood+pressure', 'Неотложная помощь')

CALCULATORS = [calculate_bmi, calculate_gcs, calculate_creatinine_clearance, calculate_bsa, calculate_shock_index]

def register_clinical_tools(server, extended=True):
    from pydantic import TypeAdapter
    for fn in CALCULATORS if extended else CALCULATORS[:3]:
        server.tool()(fn)

    @server.tool()
    def list_calculators() -> dict:
        """Каталог калькуляторов: методика, параметры, единицы, ограничения и первоисточники."""
        rows = []
        for fn in CALCULATORS if extended else CALCULATORS[:3]:
            schema = TypeAdapter(fn).json_schema()
            rows.append({'name': fn.__name__, 'description': fn.__doc__, 'inputSchema': schema})
        return {'calculators': rows, 'note': 'Границы параметров — ограничения учебного приложения. Примеры не являются данными пациента. Медицинские значения не подставляются автоматически.'}
