import pandas as pd
import numpy as np

def process_ledger(csv_path):
    """
    Procesa el ledger de transacciones para reconstruir la cartera actual y calcular el P&L realizado.
    """
    df = pd.read_csv(csv_path)
    # Asegurar que los nombres de columnas estén limpios
    df.columns = df.columns.str.strip()
    
    # Calcular precio en USD al momento de la operación
    if 'ExchangeRateToUSD' not in df.columns:
        df['ExchangeRateToUSD'] = 1.0 # default if missing
    
    df['Price_USD'] = df['Price'] * df['ExchangeRateToUSD']
    df = df.sort_values(by='Date').reset_index(drop=True)
    
    holdings = {}
    total_realized_pnl = 0.0
    realized_by_ticker = {}
    
    # Iterar cronológicamente para calcular el Costo Promedio (Average Cost) y P&L
    for idx, row in df.iterrows():
        ticker = row['Ticker'].strip()
        op_type = row['Type'].strip().upper()
        qty = float(row['Quantity'])
        price_usd = float(row['Price_USD'])
        
        if ticker not in holdings:
            holdings[ticker] = {'qty': 0, 'avg_cost_usd': 0.0, 'currency': row['Currency']}
            realized_by_ticker[ticker] = 0.0
            
        current_qty = holdings[ticker]['qty']
        current_avg_cost = holdings[ticker]['avg_cost_usd']
        
        if op_type == 'BUY':
            new_qty = current_qty + qty
            # Actualizar Average Cost Ponderado
            if new_qty > 0:
                new_avg_cost = ((current_qty * current_avg_cost) + (qty * price_usd)) / new_qty
            else:
                new_avg_cost = 0.0
            
            holdings[ticker]['qty'] = new_qty
            holdings[ticker]['avg_cost_usd'] = new_avg_cost
            holdings[ticker]['currency'] = row['Currency'] # Actualizar la info de divisa
            
        elif op_type == 'SELL':
            # Venta: Calcular Realized P&L
            realized_pnl = qty * (price_usd - current_avg_cost)
            total_realized_pnl += realized_pnl
            realized_by_ticker[ticker] += realized_pnl
            
            holdings[ticker]['qty'] = max(0, current_qty - qty)
            if holdings[ticker]['qty'] == 0:
                holdings[ticker]['avg_cost_usd'] = 0.0
                
    # Construir dataframe final de holdings actuales
    current_holdings = []
    for ticker, data in holdings.items():
        if data['qty'] > 0:
            current_holdings.append({
                'Ticker': ticker,
                'Current Quantity': data['qty'],
                'Average Cost USD': data['avg_cost_usd'],
                'Currency': data['currency']
            })
            
    df_holdings = pd.DataFrame(current_holdings)
    
    # Si no hay tenencias activas
    if df_holdings.empty:
        df_holdings = pd.DataFrame(columns=['Ticker', 'Current Quantity', 'Average Cost USD', 'Currency'])
        
    stats = {
        'total_realized_pnl': total_realized_pnl,
        'realized_by_ticker': realized_by_ticker
    }
    
    return df_holdings, stats
