import yfinance as yf
import pandas as pd

def GetLastValuePlacement(tickers: list,date = None) -> dict:
    result = {}

    # Télécharger les données groupées
    if date is None:
        data = yf.download(tickers, period="3d", interval="1d", progress=False, auto_adjust=True)
        index = -1
    else:
        data = yf.download(tickers, period="3d", interval="1d", start=date, progress=False, auto_adjust=True)
        index = 0
    if isinstance(tickers, str):
        tickers = [tickers]
    # Gestion MultiIndex si plusieurs tickers
    if isinstance(data.columns, pd.MultiIndex):
        close_data = data['Close']
    else:
        close_data = data

    # Supprimer les lignes totalement vides
    close_data = close_data.dropna(how='all')

    # Dernière date disponible (valide pour au moins un ticker)
    if close_data.empty:
        return result  # Aucun résultat dispo

    last_valid_date = close_data.index[index]
    last_row = close_data.loc[last_valid_date]

    # Conversion de la date en int AAAAMMJJ
    last_date_int = int(last_valid_date.strftime("%Y%m%d"))

    for ticker in tickers:
        try:
            if pd.notna(last_row[ticker]):
                result[ticker] = (last_date_int, round(float(last_row[ticker]), 4))
        except KeyError:
            continue  # Ticker non présent dans les données

    return result

print(GetLastValuePlacement("US0378331005","2025-06-22"))