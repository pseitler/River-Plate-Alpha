import pandas as pd

def generate_xlsx_report(results, outfile):
    df_perf = pd.DataFrame([{"Activo": a, "Actual": m["Current"], "1W": m["1W"], "1M": m["1M"]} for a, m in results['performance'].items()])
    df_diag = pd.DataFrame(results["diagnostic"])
    df_risk = pd.DataFrame(results["risk_data"])
    df_hold = results["holdings"].copy().sort_values("Layer").drop(columns=['Lots'], errors='ignore')
    
    # Modelos Cuantitativos
    df_models = pd.DataFrame([
        {"Modelo": "1. Arbitraje GLD/GDX", "Metrica": "Z-Score Spread", "Valor": results['mod1_arb']['Z-Score Spread'], "Senal": results['mod1_arb']['Señal Arbitraje']},
        {"Modelo": "2. Intermercados", "Metrica": "GMI>SMA16 y Gold>SMA68", "Valor": "-", "Senal": results['mod2_intermarket']['Señal']},
        {"Modelo": "3. GSR & Force Index", "Metrica": "Force Index EMA", "Valor": results['mod3_force_gsr']['Force Index EMA13'], "Senal": "Monitoreando"},
        {"Modelo": "4. Elliott Waves", "Metrica": "Impulso Corto Plazo", "Valor": "-", "Senal": results['mod6_elliott']}
    ])

    with pd.ExcelWriter(outfile, engine="openpyxl") as writer:
        df_models.to_excel(writer, sheet_name="Módulos Quant", index=False)
        df_diag.to_excel(writer, sheet_name="Ajuste Barbell Strategy", index=False)
        df_risk.to_excel(writer, sheet_name="Control de Riesgo", index=False)
        df_hold.to_excel(writer, sheet_name="Posiciones Ledger", index=False)
        df_perf.to_excel(writer, sheet_name="Rendimientos", index=False)
        
        for s in writer.sheets:
            for c in writer.sheets[s].columns:
                writer.sheets[s].column_dimensions[c[0].column_letter].width = 25