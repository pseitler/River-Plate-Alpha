"""
==========================================================
 TRACK RECORD MANAGER — metals_model/core/track_record.py
==========================================================
Maintains a persistent XLSX file tracking:
- Date
- Weekly signal
- Throttle active
- User stance
- ΔGSR%
- ΔSilver%
- Metals sleeve Δ%
- Notes

The engine automatically appends to the XLSX file.
==========================================================
"""

import os
import pandas as pd


TRACK_COLUMNS = [
    "Date",
    "Signal",
    "ThrottleActive",
    "GSR0",
    "GSR1",
    "DeltaGSR%",
    "Silver0",
    "Silver1",
    "DeltaSilver%",
    "MetalsDelta%",
    "UserStance",
    "Notes"
]


def load_track_record(path):
    """Load track record XLSX or create an empty DataFrame."""

    if os.path.exists(path):
        try:
            df = pd.read_excel(path)
            return df
        except Exception:
            pass

    # Empty track record
    return pd.DataFrame(columns=TRACK_COLUMNS)


def update_track_record(df, results):
    """Append a new row with results from this week."""

    GSR0 = results["gsr"]["GSR0"]
    GSR1 = results["gsr"]["GSR1"]
    Silver0 = results["holdings"]["Current Market price"].mean()  # approximate
    Silver1 = Silver0  # placeholder — holdings hold same prices
    throttle = results["throttle"]
    signal = results["signal"]

    delta_gsr = (GSR0 - GSR1) / GSR1 if GSR1 else None
    delta_silver = None  # cannot compute without historic holdings prices
    metals_delta = None  # computed by user or extended logic

    new_row = {
        "Date": results["date"],
        "Signal": signal,
        "ThrottleActive": throttle,
        "GSR0": GSR0,
        "GSR1": GSR1,
        "DeltaGSR%": delta_gsr,
        "Silver0": Silver0,
        "Silver1": Silver1,
        "DeltaSilver%": delta_silver,
        "MetalsDelta%": metals_delta,
        "UserStance": "",          # User fills manually after reading report
        "Notes": ""
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    return df