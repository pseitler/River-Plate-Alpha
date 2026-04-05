import pandas as pd

def generate_dynamic_report(results, outfile):
    # Formatting helper
    def fmt_usd(val):
        return f"${val:,.2f}"
    
    # 1. Macro Perf
    perf_rows = "".join([
        f"<tr><td><strong>{a}</strong></td><td>{m['Current']:.2f}</td>"
        f"<td style='color:{'green' if m['1W']>=0 else 'red'}; font-weight:bold;'>{m['1W']*100:+.2f}%</td>"
        f"<td style='color:{'green' if m['1M']>=0 else 'red'}; font-weight:bold;'>{m['1M']*100:+.2f}%</td></tr>"
        for a, m in results['performance'].items()
    ])
    
    # 2. Holdings Ledger Status
    hold_rows = "".join([
        f"<tr style='background-color:{'#f9ebea' if r['Layer'] == '🚨 NO CLASIFICADO' else 'white'};'>"
        f"<td>{r['Layer']} - <strong>{r['Ticker']}</strong></td>"
        f"<td>{r['Current Quantity']}</td>"
        f"<td>{fmt_usd(r.get('Average Cost USD', 0))}</td>"
        f"<td>{fmt_usd(r['Current Price'])}</td>"
        f"<td>{fmt_usd(r['Current Market Value'])}</td>"
        f"<td><span style='color:#7f8c8d; font-size:12px;'>{r.get('Currency','USD')}</span></td></tr>"
        for _, r in results['holdings'].iterrows()
    ])
    
    # 3. Barbell Diagnostic
    diag_rows = ""
    for d in results['diagnostic']:
        ajuste_usd = d.get('Ajuste Barbell (USD)', 0)
        c_stat = '#e74c3c' if "-" in str(d['Diff_Pct']) else '#27ae60'
        ajust_txt = f"COMPRAR {fmt_usd(ajuste_usd)}" if ajuste_usd > 0 else f"VENDER {fmt_usd(abs(ajuste_usd))}"
        if abs(ajuste_usd) < 100: ajust_txt = "Alineado"
        diag_rows += f"<tr><td>{d['Layer']}</td><td>{d['Target']}</td><td>{d['Actual']}</td><td style='color:{c_stat}; font-weight:bold;'>{d['Diff_Pct']}</td><td style='background-color:#fcf3cf; font-weight:bold;'>{ajust_txt}</td></tr>"

    # 4. Risk Data
    risk_rows = "".join([f"<tr><td><strong>{r['Activo']}</strong></td><td>{r['Precio Actual']}</td><td>{r['ATR 14d']}</td><td style='color:#e74c3c; font-weight:bold;'>{r['Trailing Stop']}</td><td style='color:#e67e22; font-weight:bold;'>{fmt_usd(r['Risk USD (VaR)'])}</td></tr>" for r in results['risk_data']])

    html_content = f"""
    <html><head><style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; padding: 25px; background: #f0f2f5; color: #1c1e21; }}
        .card {{ background: white; padding: 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
        .header {{ background: #1a2a3a; color: white; padding: 20px; border-radius: 12px; display: flex; flex-direction: column; gap: 15px; margin-bottom: 25px; }}
        .header-row {{ display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px; font-size: 14px;}}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-top: 15px; }}
        .metric-box {{ background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.2); text-align: center; }}
        .metric-box span {{ display: block; font-size: 12px; text-transform: uppercase; opacity: 0.8; margin-bottom: 5px; }}
        .metric-box strong {{ font-size: 18px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ padding: 12px; border-bottom: 1px solid #e1e4e8; text-align: left; font-size: 14px; }}
        th {{ background: #2c3e50; color: white; text-transform: uppercase; font-size: 12px; }}
        tr:hover {{ background-color: #f8f9f9; }}
        h2 {{ color: #2c3e50; font-size: 18px; margin-bottom: 15px; border-bottom: 2px solid #3498db; padding-bottom: 5px; display: inline-block; }}
    </style></head>
    <body>
        <div class="header">
            <div class="header-row" style="align-items: center;">
                <div style="display: flex; align-items: center; gap: 15px;">
                    <img src="RPA.png" alt="RPA Logo" height="50">
                    <span style="font-size: 22px;"><strong>River Plate Alpha</strong></span>
                </div>
                <span>📅 Fecha: {results['date']}</span>
            </div>
            <div class="metrics-grid">
                <div class="metric-box"><span>NAV Total (USD)</span><strong>${results['total_value']}</strong></div>
                <div class="metric-box"><span>P&L Realizado Histórico</span><strong style="color:#2ecc71;">${results['portfolio_stats']['total_realized_pnl']:,.2f}</strong></div>
                <div class="metric-box"><span>Condición Mercado (VIX)</span><strong>{results['vix_alert']}</strong></div>
                <div class="metric-box" style="background: {'rgba(231, 76, 60, 0.4)' if 'EXCESO' in results['risk_check'] else 'rgba(46, 204, 113, 0.2)'};"><span>Regla 2% Riesgo</span><strong>{results['risk_check']}</strong></div>
            </div>
        </div>

        <div class="card">
            <h2>1. Módulos Cuantitativos (Inteligencia Algorítmica)</h2>
            <table>
                <tr><th>Modelo</th><th>Métricas</th><th>Señal / Estado</th></tr>
                <tr><td>1. Arbitraje GLD/GDX (Cointegración)</td><td>Hedge Ratio: {results['mod1_arb']['Hedge Ratio']} | Z-Score Spread: {results['mod1_arb']['Z-Score Spread']}</td><td><strong>{results['mod1_arb']['Señal Arbitraje']}</strong></td></tr>
                <tr><td>2. Intermercados (M. Boucher)</td><td>GMI > SMA16: {results['mod2_intermarket']['GMI > SMA 16W']} | Gold > SMA 68: {results['mod2_intermarket']['Gold > SMA 68W']}</td><td><strong>{results['mod2_intermarket']['Señal']}</strong></td></tr>
                <tr><td>3. Ratios & Momentum (C. Goslin)</td><td>Ratio Oro/Plata: {results['mod3_force_gsr']['GSR (Oro/Plata)']} | Force Index: {results['mod3_force_gsr']['Force Index EMA13']}</td><td><strong>Monitoreando Flujos</strong></td></tr>
                <tr><td>4. Ondas de Elliott (Impluso)</td><td>Estructura de retroceso de corto plazo</td><td><strong>{results['mod6_elliott']}</strong></td></tr>
            </table>
        </div>

        <div class="card" style="border-left: 5px solid #f1c40f;">
            <h2>2. Asignación Estratégica (The Barbell Strategy - 85/15)</h2>
            <table><tr><th>Capa</th><th>Objetivo Target</th><th>Peso Actual</th><th>Desviación</th><th>Ajuste a Ejecutar (USD)</th></tr>{diag_rows}</table>
        </div>

        <div class="card">
            <h2>3. Control Geométrico (Stops Anclados y VaR < 2%)</h2>
            <p style="font-size: 13px; color: #555;">Presupuesto máximo de riesgo (2% NAV): <strong>{fmt_usd(results['risk_limit_2pct'])}</strong> | Riesgo Total Asignado Actual: <strong>{fmt_usd(results['total_risk_usd'])}</strong></p>
            <table><tr><th>Activo</th><th>Precio Actual</th><th>ATR 14d</th><th>Trailing Stop (Protección)</th><th>Riesgo Dólares (VaR)</th></tr>{risk_rows}</table>
        </div>

        <div class="card">
            <h2>4. Posiciones Activas del Ledger Transaccional</h2>
            <table><tr><th>Capa / Activo</th><th>Cantidad</th><th>Costo Prom. (USD)</th><th>Precio Act. (USD)</th><th>Valor Mercado (USD)</th><th>Divisa</th></tr>{hold_rows}</table>
        </div>
        
        <div class="card">
            <h2>5. Desempeño Corto Plazo</h2>
            <table><tr><th>Activo</th><th>Actual</th><th>1W</th><th>1M</th></tr>{perf_rows}</table>
        </div>
    </body></html>
    """
    with open(outfile, "w", encoding="utf-8") as f: f.write(html_content)