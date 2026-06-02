import os
from typing import Optional


def get_repo_root() -> str:
    """Directory containing this file (project root)."""
    return os.path.dirname(os.path.abspath(__file__))


def data_dir(*parts: str) -> str:
    return os.path.join(get_repo_root(), "data", *parts)


def market_prices_path(country: str, region: Optional[str] = None) -> str:
    if country == "US":
        name = f"{region} Market Prices.xlsx"
    else:
        name = f"{country} Market Prices.xlsx"
    return data_dir("market_prices", name)


def grid_frequency_path(country: str, region: Optional[str], year: int) -> str:
    if country == "US":
        filename = f"f_{region}_{year}.mat"
    else:
        filename = f"f_{country}_{year}.mat"
    return data_dir("grid_frequency", filename)


def setpoint_mat_path(country: str, region: Optional[str], year: int) -> str:
    if country == "US":
        filename = f"Pset_{region}_{year}.mat"
    else:
        filename = f"Pset_{country}_{year}.mat"
    return data_dir("setpoint_power", filename)


def setpoint_xlsx_path(country: str) -> str:
    return data_dir("setpoint_power", f"Pset_{country}.xlsx")
