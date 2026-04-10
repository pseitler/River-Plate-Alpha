import pandas as pd
import numpy as np
import yfinance as yf
import os
from datetime import datetime
from config import HTML_REPORT_FILE, XLSX_REPORT_FILE, TRANSACTIONS_FILE
from core.portfolio import process_ledger

def run_week():
    print("-> Iniciando procesamiento de datos dinamicos v7.0...")

    L1_NAME, L2_NAME, L3_NAME = "Layer 1", "Layer 2", "Layer 3"

    # --------------------------------------------------------
    # BLOQUE 1: DESCARGA MACRO Y MERCADOS
    # --------------------------------------------------------
    print("   -> Descargando Macro (Metales, Divisas, VIX, Bonos)...")
    tickers_macro = {
        "GC=F": "Oro", "SI=F": "Plata", "DX-Y.NYB": "DXY", 
        "^VIX": "VIX", "^TNX": "TNX 10Y", "EURUSD=X": "EUR/USD",
        "GDX": "Miners ETF", "GLD": "Gold ETF", "CHF=X": "CHF/USD"
    }
    
    macro_data = {}
    for t in tickers_macro.keys():
        macro_data[t] = yf.download(t, period="3y", progress=False) # 3 años por seg.
        
    prices = pd.DataFrame()
    for t in ["GC=F", "SI=F", "DX-Y.NYB", "^VIX", "^TNX", "GDX", "GLD", "CHF=X"]:
        try:
            if 'Close' in macro_data[t] and not macro_data[t].empty:
                s = macro_data[t]['Close'].squeeze()
                s.name = t
                prices = pd.concat([prices, s], axis=1)
            else:
                prices[t] = pd.Series(dtype=float)
        except Exception:
            prices[t] = pd.Series(dtype=float)
            
    # Llenar faltantes o nulos temporalmente
    prices.ffill(inplace=True)
    prices.bfill(inplace=True)
    for col in prices.columns:
        if prices[col].isna().all():
            prices[col] = 0.0  # fallback si todo falla
    
    prices.dropna(inplace=True)
    
    try:
        current_eur_usd = float(macro_data["EURUSD=X"]['Close'].squeeze().iloc[-1])
    except:
        current_eur_usd = 1.05 # Fallback razonable

    # --------------------------------------------------------
    # BLOQUE 2: CARTERA: LEDGER TRANSACCIONAL
    # --------------------------------------------------------
    print("   -> Mapeo de Cartera desde Transactions Ledger...")
    holdings_df, port_stats = process_ledger(TRANSACTIONS_FILE)
    
    # Obtener precios actuales para el DataFrame de Holdings
    current_prices = {}
    for t in holdings_df['Ticker'].unique():
        try:
            p = float(yf.download(t, period="5d", progress=False)['Close'].squeeze().iloc[-1])
            current_prices[t] = p
        except:
            current_prices[t] = 0.0
            
    holdings_df['Current Price'] = holdings_df['Ticker'].map(current_prices)
    holdings_df['Current Market Value (Local)'] = holdings_df['Current Quantity'] * holdings_df['Current Price']
    
    hold = holdings_df.copy()
    
    # Diccionario de capas (Barbell mapping in diagnostics later)
    diccionario_capas = {
        "PHAG": L1_NAME, "PHAG.MI": L1_NAME, "PHAG.L": L1_NAME, 
        "SGLD": L1_NAME, "SGLD.MI": L1_NAME, "SGLD.L": L1_NAME,
        "SGLE": L1_NAME, "SGLE.MI": L1_NAME, "SGLE.L": L1_NAME, 
        "SSLN": L1_NAME, "SSLN.MI": L1_NAME, "SSLN.L": L1_NAME,
        "ISLN": L1_NAME, "ISLN.MI": L1_NAME, "ISLN.L": L1_NAME, 
        "4GLD": L1_NAME, "4GLD.DE": L1_NAME, 
        "GLDA": L1_NAME, "GLDA.MI": L1_NAME, "GLDA.DE": L1_NAME, "GLDA.L": L1_NAME,
        "WPM": L2_NAME, "FNV": L2_NAME, "PAAS": L2_NAME, "B": L2_NAME, "NEM": L2_NAME, "AEM": L2_NAME, "RGLD": L2_NAME,
        "HL": L3_NAME, "AG": L3_NAME, "CDE": L3_NAME, "EXK": L3_NAME,
        "SILV": L3_NAME, "SILV.MI": L3_NAME, "SILV.L": L3_NAME, 
        "GDXJ": L3_NAME, "GDXJ.MI": L3_NAME, "GDXJ.L": L3_NAME
    }
    hold['Layer'] = hold['Ticker'].str.strip().map(diccionario_capas).fillna("🚨 NO CLASIFICADO")

    # Normalización a USD / EUR / Local
    def get_market_values(row):
        local_val = row['Current Market Value (Local)']
        cur = str(row['Currency']).upper().strip()
        
        usd_val = local_val
        if cur == 'EUR':
            usd_val = local_val * current_eur_usd
            
        eur_val = usd_val / current_eur_usd if current_eur_usd > 0 else usd_val
        
        # Average Cost in other currencies
        avg_cost_usd = row.get('Average Cost USD', 0.0)
        avg_cost_eur = avg_cost_usd / current_eur_usd if current_eur_usd > 0 else avg_cost_usd
        
        # Local price in other currencies
        price_local = row['Current Price']
        price_usd = price_local * current_eur_usd if cur == 'EUR' else price_local
        price_eur = price_usd / current_eur_usd if current_eur_usd > 0 else price_usd
        
        row['Current Market Value'] = usd_val # Legacy total sum compatible
        row['Current Market Value (USD)'] = usd_val
        row['Current Market Value (EUR)'] = eur_val
        
        row['Current Price (USD)'] = price_usd
        row['Current Price (EUR)'] = price_eur
        
        row['Average Cost EUR'] = avg_cost_eur
        return row
        
    hold = hold.apply(get_market_values, axis=1)

    # --------------------------------------------------------
    # MODELO 1: ARBITRAJE ESTADÍSTICO (GLD vs GDX)
    # --------------------------------------------------------
    print("   -> Calculando Modelo 1: Arbitraje OLS...")
    gld_prices = prices['GLD']
    gdx_prices = prices['GDX']
    # Calcular covarianza para hedge ratio (~252 dias)
    cov_matrix = np.cov(gdx_prices[-252:], gld_prices[-252:])
    hedge_ratio = cov_matrix[0, 1] / cov_matrix[0, 0]
    
    spread = gld_prices - hedge_ratio * gdx_prices
    spread_mean = spread.rolling(252).mean()
    spread_std = spread.rolling(252).std()
    z_score_arb = (spread - spread_mean) / spread_std
    current_z_arb = z_score_arb.iloc[-1]
    
    if current_z_arb <= -2.0: arb_signal = "COMPRAR SPREAD (Largo GLD / Corto GDX)"
    elif current_z_arb >= 2.0: arb_signal = "VENDER SPREAD (Corto GLD / Largo GDX)"
    elif abs(current_z_arb) <= 1.0: arb_signal = "CERRAR ARBITRAJE (Media alcanzada)"
    else: arb_signal = "MANTENER"
    
    mod1_results = {"Hedge Ratio": round(hedge_ratio, 4), "Z-Score Spread": round(current_z_arb, 2), "Señal Arbitraje": arb_signal}

    # --------------------------------------------------------
    # MODELO 2: INTERMERCADOS (MARK BOUCHER)
    # --------------------------------------------------------
    print("   -> Calculando Modelo 2: Sistemas Intermercado...")
    gmi_16w = gdx_prices.rolling(16 * 5).mean()
    gold_68w = gld_prices.rolling(68 * 5).mean()
    silver_12w = prices['SI=F'].rolling(12*5).mean()

    m2a_buy = (gdx_prices.iloc[-1] > gmi_16w.iloc[-1]) and (gld_prices.iloc[-1] > gold_68w.iloc[-1]) and (prices['SI=F'].iloc[-1] > silver_12w.iloc[-1])
    
    chf = prices['CHF=X']
    chf_9w = chf.rolling(9 * 5).mean()
    gdx_w = gdx_prices.resample('W').last()
    gmi_w_min = gdx_w.rolling(52).min().iloc[-1]
    m2b_buy = (gdx_w.iloc[-1] > gmi_w_min * 1.08) and (chf.iloc[-1] > chf_9w.iloc[-1]) and (gld_prices.iloc[-1] > gld_prices.iloc[-130])

    if m2a_buy and m2b_buy: intermarket_signal = "STRONG BUY (Sincronía Total)"
    elif m2a_buy or m2b_buy: intermarket_signal = "LIGERAMENTE ALCISTA (Parcial)"
    else: intermarket_signal = "HOLD / CASH (Sin Tendencia)"
    
    mod2_results = {"Gold > SMA 68W": gld_prices.iloc[-1] > gold_68w.iloc[-1], "GMI > SMA 16W": gdx_prices.iloc[-1] > gmi_16w.iloc[-1], "Señal": intermarket_signal}

    # --------------------------------------------------------
    # MODELOS 3 & 4: RATIOS Y DIVERGENCIAS (FORCE INDEX)
    # --------------------------------------------------------
    print("   -> Calculando Modelos 3 & 4: Force Index y GSR...")
    gsr_series = prices['GC=F'] / prices['SI=F']
    gsr_sma20 = gsr_series.rolling(20).mean()
    z_score_series = (gsr_series - gsr_series.rolling(252).mean()) / gsr_series.rolling(252).std()
    
    try:
        vol = macro_data['GC=F']['Volume'].squeeze()
        vol.ffill(inplace=True)
        force_index = (prices['GC=F'] - prices['GC=F'].shift(1)) * vol
        fi_ema13 = force_index.ewm(span=13, adjust=False).mean()
        fi_trend = "Alcista" if fi_ema13.iloc[-1] > 0 else "Bajista"
    except:
        fi_trend = "N/D"

    mod3_results = {"GSR (Oro/Plata)": round(gsr_series.iloc[-1], 2), "GSR Z-Score": round(z_score_series.iloc[-1], 2), "Force Index EMA13": fi_trend}

    # --------------------------------------------------------
    # MODELO 6: ONDAS DE ELLIOTT (APROXIMACIÓN BÁSICA)
    # --------------------------------------------------------
    # Usamos una media movil corta (10t) para picos/valles basicos
    sma_10 = prices['GC=F'].rolling(10).mean()
    trend_valid = "Sí (Posible Onda de Impulso)" if prices['GC=F'].iloc[-1] > sma_10.iloc[-1] and sma_10.iloc[-1] > sma_10.iloc[-20] else "No Convencente / Correctivo"

    # --------------------------------------------------------
    # MACRO ANTIGUO Y FILTROS ESTÁNDAR
    # --------------------------------------------------------
    vix_actual = prices['^VIX'].iloc[-1]
    tnx_actual = prices['^TNX'].iloc[-1]
    sma50_tnx = prices['^TNX'].rolling(50).mean().iloc[-1]
    riesgo_sistemico = vix_actual > 30.0
    viento_contra_bonos = tnx_actual > sma50_tnx

    # --------------------------------------------------------
    # MODELO 5: RISK MANAGEMENT (BARBELL STRATEGY & 2% RULE)
    # --------------------------------------------------------
    print("   -> Calculando Modelo 5: Riesgo Institucional (Barbell y 2%)...")
    # Ponderaciones de Barbell Strategy: 85% Cash/L1 Seguro, 15% Layers 2/3 Agresivo
    t_l1, t_l2, t_l3 = 0.85, 0.10, 0.05 
    if riesgo_sistemico: t_l1, t_l2, t_l3 = 1.0, 0.0, 0.0
    
    total_val_real = hold['Current Market Value'].sum()
    nav_portafolio = total_val_real # Aproximación, idealmente habría cash
    risk_limit_2pct = nav_portafolio * 0.02
    
    risk_data = []
    total_risk_usd = 0.0

    def calc_risk_metrics(nombre, ticker_symbol, is_macro=False):
        try:
            df_h = yf.download(ticker_symbol, period="6mo", progress=False)
            if not df_h.empty:
                c_p = float(df_h['Close'].squeeze().iloc[-1])
                h, l = df_h['High'].squeeze(), df_h['Low'].squeeze()
                tr = pd.concat([h - l, (h - df_h['Close'].squeeze().shift(1)).abs(), (l - df_h['Close'].squeeze().shift(1)).abs()], axis=1).max(axis=1)
                atr = float(tr.rolling(14).mean().iloc[-1])
                max_high_3m = float(h.tail(63).max())
                trailing_stop = max_high_3m - (2.5 * atr)
                if trailing_stop > c_p: trailing_stop = c_p - (1.0 * atr)
                
                # Riesgo financiero por este activo
                qty_held = float(hold[hold['Ticker'] == nombre]['Current Quantity'].iloc[0]) if nombre in hold['Ticker'].values else 0
                risk_usd_item = qty_held * (c_p - trailing_stop) if trailing_stop < c_p else 0
                
                return {
                    "Activo": nombre, "Precio Actual": round(c_p, 2), "ATR 14d": round(atr, 2), 
                    "Trailing Stop": round(trailing_stop, 2), "Target Price": round(c_p + (3*atr), 2),
                    "Risk USD (VaR)": round(risk_usd_item, 2)
                }
        except: return None

    for ticker in hold['Ticker'].unique():
        rm = calc_risk_metrics(ticker, ticker)
        if rm: 
            risk_data.append(rm)
            total_risk_usd += rm["Risk USD (VaR)"]

    risk_check = "🟢 DENTRO DEL LÍMITE" if total_risk_usd <= risk_limit_2pct else "🔴 EXCESO DE RIESGO (>2% NAV)"

    # Diagnóstico Barbell
    hold_validos = hold[hold['Layer'] != "🚨 NO CLASIFICADO"]
    total_val_modelo = hold_validos['Current Market Value'].sum()
    actual_weights = hold_validos.groupby('Layer')['Current Market Value'].sum() / total_val_modelo if total_val_modelo > 0 else {}
    
    diagnostic = []
    targets_barbell = {"Layer 1": t_l1, "Layer 2": t_l2, "Layer 3": t_l3}
    for layer, target in targets_barbell.items():
        actual = actual_weights.get(layer, 0)
        diff_pct = actual - target
        diff_usd = (target - actual) * total_val_modelo 
        
        diagnostic.append({
            "Layer": layer, "Actual": f"{actual*100:.1f}%", "Target": f"{target*100:.1f}%", 
            "Diff_Pct": f"{diff_pct*100:+.1f}%", "Ajuste Barbell (USD)": diff_usd,
        })
        
    def calc_perf(serie):
        return {"Current": serie.iloc[-1], "1W": (serie.iloc[-1] / serie.iloc[-6] - 1), "1M": (serie.iloc[-1] / serie.iloc[-22] - 1)}
    
    perf_data = {"Gold ($)": calc_perf(prices['GC=F']), "Silver ($)": calc_perf(prices['SI=F'])}

    # --------------------------------------------------------
    # PLAN DE ACCION RECOMENDADO (PORTFOLIO ACTIONS)
    # --------------------------------------------------------
    print("   -> Generando Plan de Acción...")
    action_plan = []
    
    # 1. Limite de Riesgo Total
    if total_risk_usd > risk_limit_2pct:
        action_plan.append(f"🚨 URGENTE: Reducir riesgo total del portfolio. VaR Actual de {total_risk_usd:,.2f} USD supera el límite del 2% ({risk_limit_2pct:,.2f} USD).")
        
    # 2. Stops Loss
    for rm in risk_data:
        if rm['Precio Actual'] <= rm['Trailing Stop']:
            action_plan.append(f"🛑 STOP LOSS ALCANZADO: Liquidar {rm['Activo']}. Precio ({rm['Precio Actual']}) <= Stop ({rm['Trailing Stop']}).")
        elif rm['Precio Actual'] <= rm['Trailing Stop'] * 1.03:
            action_plan.append(f"⚠️ PELIGRO: {rm['Activo']} crítico. Precio ({rm['Precio Actual']}) a <3% del Stop ({rm['Trailing Stop']}).")

    # 3. Rebalanceo Asignación
    for d in diagnostic:
        ajuste = float(d['Ajuste Barbell (USD)'])
        layer = d['Layer']
        if abs(ajuste) > nav_portafolio * 0.01:  # Desvío mayor al 1% del NAV
            accion = "COMPRAR" if ajuste > 0 else "VENDER"
            asset_sug = ""
            if layer == L1_NAME: asset_sug = "Oro/Plata Físico (ETC UCITS e.g., SGLD, PHAG)"
            elif layer == L2_NAME: asset_sug = "Acciones/ETFs de mineras consolidadas (e.g., GDX, WPM)"
            elif layer == L3_NAME: asset_sug = "Mineras Junior / Especulativas (e.g., GDXJ, HL)"
            
            action_plan.append(f"⚖️ REBALANCEO {layer}: {accion} {abs(ajuste):,.2f} USD en <strong>{asset_sug}</strong> para alinear peso ({d['Actual']}) al target ({d['Target']}).")

    # 4. Señales Corto Plazo
    if "COMPRAR" in arb_signal or "VENDER SPREAD" in arb_signal or "CERRAR" in arb_signal:
        action_plan.append(f"📈 ARBITRAJE GLD/GDX: Ejecutar -> {arb_signal}. <em>(Subyacentes sugeridos: GLD o SGLD físico vs opciones/corto en ETF GDX)</em>")

    if "STRONG BUY" in intermarket_signal:
        action_plan.append("🚀 ESTRATEGICO: Viento a favor intenso. Priorizar compras activas en <strong>Acciones de Oro/Plata (Layer 2/3)</strong>.")
    elif "CASH" in intermarket_signal or "Sin Tendencia" in intermarket_signal:
        action_plan.append("🛡️ ESTRATEGICO: Régimen incierto. Mantener liquidez o rotar a <strong>Oro/Plata Físico puro (Layer 1)</strong>. Evitar mineras.")

    if not action_plan:
        action_plan.append("✅ PORTFOLIO ALINEADO: Ninguna acción correctiva estructural urgente requerida hoy.")

    # --------------------------------------------------------
    # PAQUETE DE RESULTADOS
    # --------------------------------------------------------
    print("   -> Generando paquetes de reporte de River Plate Alpha...")
    date_str = datetime.now().strftime("%Y-%m-%d")
    results = {
        "action_plan": action_plan,
        "date": date_str, "total_value": f"{total_val_real:,.2f}", "eur_usd_rate": current_eur_usd,
        "performance": perf_data,
        "portfolio_stats": port_stats, # Nuevo
        "mod1_arb": mod1_results,
        "mod2_intermarket": mod2_results,
        "mod3_force_gsr": mod3_results,
        "mod6_elliott": trend_valid,
        "vix_alert": "🔴 RIESGO SISTÉMICO" if riesgo_sistemico else "🟢 Mercado Ordenado",
        "risk_limit_2pct": risk_limit_2pct, "total_risk_usd": total_risk_usd, "risk_check": risk_check,
        "diagnostic": diagnostic, "risk_data": risk_data, "holdings": hold
    }

    from reporting.html_report import generate_dynamic_report
    from reporting.xlsx_report import generate_xlsx_report
    try:
        generate_dynamic_report(results, f"{os.path.splitext(HTML_REPORT_FILE)[0]}.html")
        generate_xlsx_report(results, f"{os.path.splitext(XLSX_REPORT_FILE)[0]}.xlsx")
    except Exception as e:
        print(f"Error generando reporte: {e}")
    
    return results