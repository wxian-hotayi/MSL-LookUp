"""Excel/CSV output writer."""
import csv
from pathlib import Path

import pandas as pd


def read_input_file(filepath: str) -> pd.DataFrame:
    """Read Excel or CSV file and return DataFrame."""
    path = Path(filepath)
    suffix = path.suffix.lower()

    if suffix in [".xlsx", ".xls"]:
        return pd.read_excel(filepath)
    elif suffix == ".csv":
        return pd.read_csv(filepath)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def find_mpn_column(df: pd.DataFrame) -> str:
    """Find the MPN column in DataFrame."""
    mpn_candidates = ["MPN", "mpn", "Maker Part No", "Maker Part Number", "Part Number", "PartNo", "Part"]

    for col in mpn_candidates:
        if col in df.columns:
            return col

    for col in df.columns:
        col_lower = col.lower()
        if "mpn" in col_lower or "part" in col_lower and "number" in col_lower:
            return col

    raise ValueError(f"Could not find MPN column. Available columns: {list(df.columns)}")


def write_output_file(df: pd.DataFrame, mpn_msl_map: dict, output_path: str = None):
    """
    Write DataFrame with MSL column to Excel or CSV.

    If output_path is None, adds '_with_msl' before extension.
    """
    path = Path(output_path) if output_path else None

    # Add MSL column
    df = df.copy()
    df["MSL"] = df.apply(lambda row: get_msl_for_row(row, mpn_msl_map), axis=1)

    if path is None:
        input_path = Path(output_path) if output_path else Path("output")
        stem = input_path.stem
        suffix = input_path.suffix.lower()
        path = input_path.parent / f"{stem}_with_msl{suffix}"

    if path.suffix.lower() in [".xlsx", ".xls"]:
        df.to_excel(path, index=False)
    else:
        df.to_csv(path, index=False)

    return str(path)


def get_msl_for_row(row, mpn_msl_map: dict) -> str:
    """Get MSL value for a row based on MPN column."""
    mpn = str(row.get("MPN", row.get("mpn", "")))
    result = mpn_msl_map.get(mpn, {})
    return result.get("msl", result.get("msl", "")) if isinstance(result, dict) else result


def preview_data(df: pd.DataFrame, max_rows: int = 10) -> list:
    """Return preview of DataFrame as list of lists."""
    return [df.columns.tolist()] + df.head(max_rows).values.tolist()
