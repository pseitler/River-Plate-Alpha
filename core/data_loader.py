"""
==========================================================
 DATA LOADER — metals_model/core/data_loader.py
==========================================================
Centralized loader and cleaner for:
- Gold CSV
- Silver CSV
- Holdings CSV

Not heavily used since engine.py directly loads files,
but kept for modularity and future extension.
==========================================================
"""

import pandas as pd


def load_gold_silver(gold_path, silver_path):
    """Load and clean gold and silver CSVs."""

    gold = pd.read_csv(gold_path)
    silver = pd.read_csv(silver_path)

    for df in [gold, silver]:
        df['Price'] = (
            df['Price']
            .astype(str)
            .str.replace(',', '', regex=False)
        )
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
        df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')

    gold = gold.sort_values('Date')
    silver = silver.sort_values('Date')

    return gold, silver


def load_holdings(path, sep=';'):
    """Load holdings with custom separator."""
    hold = pd.read_csv(path, sep=sep)
    return hold