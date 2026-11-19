"""Local network MCP server using Streamable HTTP on port 8000."""

from __future__ import annotations

import logging
import os

from mcp.server import MCPServer

from .clinical_tools import (
    calculate_bmi,
    calculate_chadsvasc,
    calculate_ckd_epi,
    calculate_gcs,
    calculate_map,
    calculate_qsofa,
    list_calculators,
    Sex,
    AdultAge,
    CreatinineMgDl,
    HeightCm,
    WeightKg,
    GcsEye,
    GcsVerbal,
    GcsMotor,
    RespiratoryRate,
    SystolicBp,
    DiastolicBp,
)


logging.basicConfig(level=logging.INFO, format="[network-mcp] %(message)s")
mcp = MCPServer(
    "pharmacogen-network",
    description="Локальный каталог клинических методик PharmacoGen",
    instructions="Сначала вызовите tools/list, затем передайте проверенные параметры в tools/call.",
    version="1.0.0",
)


@mcp.tool()
def calculate_bmi_tool(weight_kg: WeightKg, height_cm: HeightCm) -> dict:
    """Рассчитать индекс массы тела."""
    return calculate_bmi(weight_kg, height_cm)


@mcp.tool()
def calculate_ckd_epi_tool(creatinine_mg_dl: CreatinineMgDl, age: AdultAge, sex: Sex) -> dict:
    """Рассчитать оценочную СКФ CKD-EPI 2021."""
    return calculate_ckd_epi(creatinine_mg_dl, age, sex)


@mcp.tool()
def calculate_chadsvasc_tool(
    age: AdultAge,
    sex: Sex,
    congestive_heart_failure: bool = False,
    hypertension: bool = False,
    diabetes: bool = False,
    stroke_history: bool = False,
    vascular_disease: bool = False,
) -> dict:
    """Рассчитать CHA₂DS₂-VASc."""
    return calculate_chadsvasc(
        age, sex, congestive_heart_failure, hypertension, diabetes, stroke_history, vascular_disease
    )


@mcp.tool()
def calculate_gcs_tool(eye: GcsEye, verbal: GcsVerbal, motor: GcsMotor) -> dict:
    """Рассчитать сумму по шкале комы Глазго."""
    return calculate_gcs(eye, verbal, motor)


@mcp.tool()
def calculate_qsofa_tool(respiratory_rate: RespiratoryRate, systolic_bp: SystolicBp, altered_mentation: bool) -> dict:
    """Рассчитать qSOFA."""
    return calculate_qsofa(respiratory_rate, systolic_bp, altered_mentation)


@mcp.tool()
def calculate_map_tool(systolic_bp: SystolicBp, diastolic_bp: DiastolicBp) -> dict:
    """Рассчитать среднее артериальное давление."""
    return calculate_map(systolic_bp, diastolic_bp)


@mcp.tool()
def list_calculators_tool() -> list[dict]:
    """Показать каталог всех локальных клинических методик."""
    return list_calculators()


def main() -> None:
    port = int(os.environ.get("PHARMACOGEN_MCP_PORT", "8000"))
    host = os.environ.get("PHARMACOGEN_MCP_HOST", "127.0.0.1")
    mcp.run(transport="streamable-http", host=host, port=port, streamable_http_path="/mcp")


if __name__ == "__main__":
    main()
