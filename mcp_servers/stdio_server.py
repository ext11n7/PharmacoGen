"""Local MCP server using the stdio transport.

Run with: python -m mcp_servers.stdio_server
Only MCP messages go to stdout. Logs are sent to stderr.
"""

from __future__ import annotations

import logging

from mcp.server import MCPServer

from .clinical_tools import (
    calculate_bmi,
    calculate_chadsvasc,
    calculate_ckd_epi,
    calculate_gcs,
    list_calculators,
    Sex,
    AdultAge,
    CreatinineMgDl,
    HeightCm,
    WeightKg,
)


logging.basicConfig(level=logging.INFO, format="[stdio-mcp] %(message)s")
mcp = MCPServer(
    "pharmacogen-stdio",
    description="Три клинических калькулятора для демонстрации MCP stdio",
    instructions="Используйте tools/list для каталога и tools/call для расчёта.",
    version="1.0.0",
)


@mcp.tool()
def calculate_bmi_tool(weight_kg: WeightKg, height_cm: HeightCm) -> dict:
    """Рассчитать индекс массы тела."""
    return calculate_bmi(weight_kg, height_cm)


@mcp.tool()
def calculate_ckd_epi_tool(creatinine_mg_dl: CreatinineMgDl, age: AdultAge, sex: Sex) -> dict:
    """Рассчитать оценочную скорость клубочковой фильтрации CKD-EPI 2021."""
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
def list_calculators_tool() -> list[dict]:
    """Показать каталог методик, единицы измерения и границы параметров."""
    return list_calculators()[:3]


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
