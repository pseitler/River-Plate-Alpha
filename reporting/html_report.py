import pandas as pd

def generate_dynamic_report(results, outfile):
    # Formatting helper
    def fmt_val(usd, eur, local, local_cur):
        return f"<span class='cur-usd' style='display:inline;'>${usd:,.2f}</span><span class='cur-eur' style='display:none;'>€{eur:,.2f}</span><span class='cur-local' style='display:none;'>{local:,.2f} {local_cur}</span>"

    def fmt_usd(val):
        return f"${val:,.2f}"
        
    eur_rate = results.get('eur_usd_rate', 1.05) if results.get('eur_usd_rate') and results.get('eur_usd_rate') > 0 else 1.05
    
    # 1. Macro Perf
    perf_rows = "".join([
        f"<tr><td><strong>{a}</strong></td><td>{m['Current']:.2f}</td>"
        f"<td style='color:{'green' if m['1W']>=0 else 'red'}; font-weight:bold;'>{m['1W']*100:+.2f}%</td>"
        f"<td style='color:{'green' if m['1M']>=0 else 'red'}; font-weight:bold;'>{m['1M']*100:+.2f}%</td></tr>"
        for a, m in results['performance'].items()
    ])
    
    # 2. Holdings Ledger Status
    hold_rows = ""
    for idx, r in results['holdings'].iterrows():
        bg_color = '#f9ebea' if r['Layer'] == '🚨 NO CLASIFICADO' else 'white'
        row_id = f"lots_row_{idx}"
        cur_code = r.get('Currency', 'USD')
        
        # Helper for lot cost which could default back if local isn't perfectly registered
        avg_usd = r.get('Average Cost USD', 0)
        avg_eur = r.get('Average Cost EUR', avg_usd / eur_rate)
        # For local, avg cost in local is not directly saved in holdings, but we can assume it via Current Price proportion
        avg_local = avg_usd if cur_code == 'USD' else avg_usd / eur_rate if cur_code == 'EUR' else avg_usd
        
        hold_rows += f"<tr style='background-color:{bg_color}; cursor:pointer;' onclick='toggleLots(\"{row_id}\")'>"
        hold_rows += f"<td>{r['Layer']} - <strong>{r['Ticker']}</strong> <span style='font-size:10px;color:#3498db;'>▼ Lotes</span></td>"
        hold_rows += f"<td>{r['Current Quantity']}</td>"
        hold_rows += f"<td>{fmt_val(avg_usd, avg_eur, avg_local, cur_code)}</td>"
        hold_rows += f"<td>{fmt_val(r.get('Current Price (USD)', r.get('Current Price', 0)), r.get('Current Price (EUR)', r.get('Current Price', 0)/eur_rate), r.get('Current Price', 0), cur_code)}</td>"
        hold_rows += f"<td>{fmt_val(r.get('Current Market Value (USD)', r.get('Current Market Value', 0)), r.get('Current Market Value (EUR)', r.get('Current Market Value',0)/eur_rate), r.get('Current Market Value (Local)', 0), cur_code)}</td>"
        hold_rows += f"<td><span style='color:#7f8c8d; font-size:12px;'>{cur_code}</span></td></tr>"
        
        # Construir tabla de lotes (desplegable anidado)
        lots = r.get('Lots', [])
        if isinstance(lots, list) and len(lots) > 0:
            lots_html = "<table style='margin: 10px 0; background-color:#fdfefe; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-radius: 5px; font-size:12px;'><tr><th style='background-color:#bdc3c7;'>Fecha Compra</th><th style='background-color:#bdc3c7;'>Cant.</th><th style='background-color:#bdc3c7;'>Costo Equivalente</th></tr>"
            for lot in lots:
                # Lot representation
                l_usd = lot.get('Price_USD', 0)
                l_eur = l_usd / eur_rate
                l_loc = lot.get('Price_Local', 0)
                lots_html += f"<tr><td>{lot['Date']}</td><td>{lot['Quantity']}</td><td>{fmt_val(l_usd, l_eur, l_loc, cur_code)}</td></tr>"
            lots_html += "</table>"
            hold_rows += f"<tr id='{row_id}' style='display:none; background-color:#f8f9f9;'><td colspan='6' style='padding: 5px 20px;'>{lots_html}</td></tr>"
    
    # 3. Barbell Diagnostic
    diag_rows = ""
    for d in results['diagnostic']:
        ajuste_usd = d.get('Ajuste Barbell (USD)', 0)
        c_stat = '#e74c3c' if "-" in str(d['Diff_Pct']) else '#27ae60'
        
        if abs(ajuste_usd) < 100: 
            ajust_txt = "Alineado"
        else:
            accion = "COMPRAR" if ajuste_usd > 0 else "VENDER"
            ajust_txt = f"{accion} {fmt_val(abs(ajuste_usd), abs(ajuste_usd)/eur_rate, abs(ajuste_usd), 'USD')}"
            
        diag_rows += f"<tr><td>{d['Layer']}</td><td>{d['Target']}</td><td>{d['Actual']}</td><td style='color:{c_stat}; font-weight:bold;'>{d['Diff_Pct']}</td><td style='background-color:#fcf3cf; font-weight:bold;'>{ajust_txt}</td></tr>"

    # 4. Risk Data
    risk_rows = "".join([f"<tr><td><strong>{r['Activo']}</strong></td><td>{fmt_val(r['Precio Actual'], r['Precio Actual']/eur_rate, r['Precio Actual'], 'USD')}</td><td>{r['ATR 14d']}</td><td style='color:#e74c3c; font-weight:bold;'>{r['Trailing Stop']}</td><td style='color:#e67e22; font-weight:bold;'>{fmt_val(r['Risk USD (VaR)'], r['Risk USD (VaR)']/eur_rate, r['Risk USD (VaR)'], 'USD')}</td></tr>" for r in results['risk_data']])

    # 5. Action Plan Rows
    action_rows = "".join([f"<li style='margin-bottom: 10px;'>{act}</li>" for act in results.get('action_plan', [])])
    
    try:
        tot_val_usd = float(str(results['total_value']).replace(',', ''))
    except:
        tot_val_usd = 0.0
    tot_val_eur = tot_val_usd / eur_rate
    
    tot_pnl_usd = results['portfolio_stats']['total_realized_pnl']
    tot_pnl_eur = tot_pnl_usd / eur_rate

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
        .action-card {{ border-left: 6px solid #e74c3c; background-color: #fdfefe; }}
        .btn-currency {{ background-color: #34495e; color: white; border: 1px solid #2c3e50; padding: 8px 15px; border-radius: 5px; cursor: pointer; transition: 0.3s; }}
        .btn-currency:hover {{ background-color: #2c3e50; }}
        .btn-active {{ background-color: #3498db; border-color: #2980b9; }}
    </style>
    <script>
        function toggleLots(rowId) {{
            var el = document.getElementById(rowId);
            if (el) {{
                if (el.style.display === 'none') {{
                    el.style.display = 'table-row';
                }} else {{
                    el.style.display = 'none';
                }}
            }}
        }}

        function setCurrency(cur) {{
            const usdEls = document.querySelectorAll('.cur-usd');
            const eurEls = document.querySelectorAll('.cur-eur');
            const localEls = document.querySelectorAll('.cur-local');
            
            usdEls.forEach(el => el.style.display = 'none');
            eurEls.forEach(el => el.style.display = 'none');
            localEls.forEach(el => el.style.display = 'none');
            
            if(cur === 'USD') usdEls.forEach(el => el.style.display = 'inline');
            if(cur === 'EUR') eurEls.forEach(el => el.style.display = 'inline');
            if(cur === 'LOCAL') localEls.forEach(el => el.style.display = 'inline');
            
            document.getElementById('btn-usd').classList.remove('btn-active');
            document.getElementById('btn-eur').classList.remove('btn-active');
            document.getElementById('btn-local').classList.remove('btn-active');
            
            if(cur === 'USD') document.getElementById('btn-usd').classList.add('btn-active');
            if(cur === 'EUR') document.getElementById('btn-eur').classList.add('btn-active');
            if(cur === 'LOCAL') document.getElementById('btn-local').classList.add('btn-active');
        }}
    </script>
    </head>
    <body>
        <div class="header">
            <div class="header-row" style="align-items: center;">
                <div style="display: flex; align-items: center; gap: 15px;">
                    <img src="RPA.png" alt="RPA Logo" height="50">
                    <span style="font-size: 22px;"><strong>River Plate Alpha</strong></span>
                </div>
                <div>
                    <button id="btn-usd" class="btn-currency btn-active" onclick="setCurrency('USD')">Ver USD</button>
                    <button id="btn-eur" class="btn-currency" onclick="setCurrency('EUR')">Ver EUR</button>
                    <button id="btn-local" class="btn-currency" onclick="setCurrency('LOCAL')">Ver Local</button>
                </div>
                <span>📅 Fecha: {results['date']}</span>
            </div>
            <div class="metrics-grid">
                <div class="metric-box"><span>NAV Total</span><strong>{fmt_val(tot_val_usd, tot_val_eur, tot_val_usd, 'MIX')}</strong></div>
                <div class="metric-box"><span>P&L Realizado Histórico</span><strong style="color:#2ecc71;">{fmt_val(tot_pnl_usd, tot_pnl_eur, tot_pnl_usd, 'MIX')}</strong></div>
                <div class="metric-box"><span>Condición Mercado (VIX)</span><strong>{results['vix_alert']}</strong></div>
                <div class="metric-box" style="background: {'rgba(231, 76, 60, 0.4)' if 'EXCESO' in results['risk_check'] else 'rgba(46, 204, 113, 0.2)'};"><span>Regla 2% Riesgo</span><strong>{results['risk_check']}</strong></div>
            </div>
        </div>

        <div class="card action-card">
            <h2 style="border-bottom: 2px solid #e74c3c; color: #c0392b;">🚀 ACCIONES RECOMENDADAS (HOY)</h2>
            <ul style="font-size: 16px; line-height: 1.6; color: #34495e; padding-left: 20px;">
                {action_rows}
            </ul>
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
            <table><tr><th>Capa</th><th>Objetivo Target</th><th>Peso Actual</th><th>Desviación</th><th>Ajuste a Ejecutar</th></tr>{diag_rows}</table>
        </div>

        <div class="card">
            <h2>3. Control Geométrico (Stops Anclados y VaR < 2%)</h2>
            <p style="font-size: 13px; color: #555;">Presupuesto máximo de riesgo (2% NAV): <strong>{fmt_usd(results['risk_limit_2pct'])}</strong> | Riesgo Total Asignado Actual: <strong>{fmt_usd(results['total_risk_usd'])}</strong></p>
            <table><tr><th>Activo</th><th>Precio Actual</th><th>ATR 14d</th><th>Trailing Stop (Protección)</th><th>Riesgo (VaR)</th></tr>{risk_rows}</table>
        </div>

        <div class="card">
            <h2>4. Posiciones Activas del Ledger Transaccional</h2>
            <table><tr><th>Capa / Activo</th><th>Cantidad</th><th>Costo Promedio</th><th>Precio Actual</th><th>Valor Mercado</th><th>Divisa</th></tr>{hold_rows}</table>
        </div>
        
        <div class="card">
            <h2>5. Desempeño Corto Plazo</h2>
            <table><tr><th>Activo</th><th>Actual</th><th>1W</th><th>1M</th></tr>{perf_rows}</table>
        </div>
    </body></html>
    """
    with open(outfile, "w", encoding="utf-8") as f: f.write(html_content)