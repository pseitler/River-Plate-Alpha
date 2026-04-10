import pandas as pd
import numpy as np
import yfinance as yf

def process_ledger(csv_path):
    """
    Procesa el ledger de transacciones para reconstruir la cartera actual y calcular el P&L realizado.
    Implementa FIFO para el Realized P&L y autocompleta Exchange Rates faltantes.
    """
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(by='Date').reset_index(drop=True)
    
    # 1. Obtener Exchange Rates históricos automáticamente si hay otras divisas
    currencies = [str(c).strip().upper() for c in df['Currency'].unique() if pd.notna(c)]
    fx_rates = {}
    
    start_date = df['Date'].min()
    if pd.notna(start_date):
        end_date = pd.Timestamp.today() + pd.Timedelta(days=1)
        for cur in currencies:
            if cur == 'USD':
                continue
            ticker_fx = f"{cur}USD=X"
            try:
                data = yf.download(ticker_fx, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), progress=False)
                if not data.empty:
                    fx_rates[cur] = data['Close'].squeeze()
            except Exception as e:
                print(f"Error descargando FX para {cur}: {e}")

    def get_rate(row):
        cur = str(row['Currency']).strip().upper()
        if cur == 'USD':
            return 1.0
            
        if 'ExchangeRateToUSD' in row and pd.notna(row['ExchangeRateToUSD']) and str(row['ExchangeRateToUSD']).strip() != '':
            try:
                val = float(row['ExchangeRateToUSD'])
                if val > 0: return val
            except:
                pass
                
        date = pd.to_datetime(row['Date'])
        if cur in fx_rates:
            s_fx = fx_rates[cur]
            if type(s_fx) == pd.Series and not s_fx.empty:
                # Obtener el rate disponible más cercano hacia atrás
                idx = s_fx.index.get_indexer([date], method='pad')
                if idx[0] != -1:
                    return float(s_fx.iloc[idx[0]])
        return 1.0 # default si todo falla
        
    df['ExchangeRateToUSD_Calc'] = df.apply(get_rate, axis=1)
    df['Price_USD'] = df['Price'] * df['ExchangeRateToUSD_Calc']
    
    holdings = {}
    total_realized_pnl = 0.0
    realized_by_ticker = {}
    
    # 2. Reconstruir FIFO
    for idx, row in df.iterrows():
        ticker = str(row['Ticker']).strip()
        op_type = str(row['Type']).strip().upper()
        
        try:
            qty = float(row['Quantity'])
            price_usd = float(row['Price_USD'])
            price_local = float(row['Price'])
        except (ValueError, TypeError):
            continue
            
        if ticker not in holdings:
            holdings[ticker] = {'lots': [], 'currency': str(row['Currency']).strip()}
            realized_by_ticker[ticker] = 0.0
            
        if op_type == 'BUY':
            holdings[ticker]['lots'].append({
                'date': row['Date'].strftime('%Y-%m-%d') if pd.notna(row['Date']) else '',
                'qty': qty,
                'price_usd': price_usd,
                'price_local': price_local,
                'currency': row['Currency']
            })
            holdings[ticker]['currency'] = row['Currency']
            
        elif op_type == 'SELL':
            sell_qty = qty
            lots = holdings[ticker]['lots']
            
            # FIFO Consumo
            while sell_qty > 0 and len(lots) > 0:
                first_lot = lots[0]
                if first_lot['qty'] <= sell_qty:
                    # Consumir todo el lote
                    realized_pnl = first_lot['qty'] * (price_usd - first_lot['price_usd'])
                    total_realized_pnl += realized_pnl
                    realized_by_ticker[ticker] += realized_pnl
                    sell_qty -= first_lot['qty']
                    lots.pop(0)
                else:
                    # Consumir porción del lote
                    realized_pnl = sell_qty * (price_usd - first_lot['price_usd'])
                    total_realized_pnl += realized_pnl
                    realized_by_ticker[ticker] += realized_pnl
                    first_lot['qty'] -= sell_qty
                    sell_qty = 0

    # 3. Construir dataframe final y consolidar
    current_holdings = []
    for ticker, data in holdings.items():
        lots = data['lots']
        total_qty = sum(lot['qty'] for lot in lots)
        
        if total_qty > 0:
            total_cost_usd = sum(lot['qty'] * lot['price_usd'] for lot in lots)
            avg_cost_usd = total_cost_usd / total_qty if total_qty > 0 else 0.0
            
            formatted_lots = []
            for lot in lots:
                formatted_lots.append({
                    'Date': lot['date'],
                    'Quantity': lot['qty'],
                    'Price_USD': lot['price_usd'],
                    'Price_Local': lot['price_local']
                })
                
            current_holdings.append({
                'Ticker': ticker,
                'Current Quantity': total_qty,
                'Average Cost USD': avg_cost_usd,
                'Currency': data['currency'],
                'Lots': formatted_lots
            })
            
    df_holdings = pd.DataFrame(current_holdings)
    
    if df_holdings.empty:
        df_holdings = pd.DataFrame(columns=['Ticker', 'Current Quantity', 'Average Cost USD', 'Currency', 'Lots'])
        
    stats = {
        'total_realized_pnl': total_realized_pnl,
        'realized_by_ticker': realized_by_ticker
    }
    
    return df_holdings, stats
