import yfinance as yf
import pandas as pd

def GetLastValuePlacement(tickers: list, date=None) -> dict:
    result = {}

    if isinstance(tickers, str):
        tickers = [tickers]

    # Télécharger les données de prix
    data = yf.download(
        tickers, 
        period="3d", 
        interval="1d", 
        start=date if date else None, 
        progress=False, 
        auto_adjust=True
    )

    index = 0 if date else -1

    # Extraire les prix de clôture
    close_data = data['Close'] if isinstance(data.columns, pd.MultiIndex) else data
    close_data = close_data.dropna(how='all')
    if close_data.empty:
        return result

    last_valid_date = close_data.index[index]
    last_row = close_data.loc[last_valid_date]
    last_date_int = int(last_valid_date.strftime("%Y%m%d"))

    # Récupérer toutes les devises des tickers en une passe
    currencies = {}
    for ticker in tickers:
        try:
            currencies[ticker] = yf.Ticker(ticker).info.get("currency", "EUR")
        except Exception:
            currencies[ticker] = "EUR"  # Valeur par défaut en cas d'erreur

    # Identifier les devises à convertir
    foreign_currencies = set(currencies.values()) - {"EUR"}

    # Télécharger les taux de change nécessaires
    fx_rates = {}
    if foreign_currencies:
        fx_tickers = [f"{cur}EUR=X" for cur in foreign_currencies]
        fx_data = yf.download(fx_tickers, period="3d", interval="1d", progress=False,start=date if date else None)['Close']
        fx_data = fx_data.dropna(how='all')
        for cur in foreign_currencies:
            fx_ticker = f"{cur}EUR=X"
            try:
                rate = fx_data[fx_ticker].dropna().iloc[index]
                fx_rates[cur] = rate
            except Exception:
                fx_rates[cur] = None  # Impossible d'obtenir le taux

    # Construction du résultat
    for ticker in tickers:
        try:
            price = last_row[ticker]
            if pd.notna(price):
                currency = currencies.get(ticker, "EUR")
                if currency != "EUR":
                    rate = fx_rates.get(currency)
                    if rate:
                        price *= rate  # conversion vers EUR
                    else:
                        continue  # ignorer si taux manquant
                result[ticker] = (last_date_int, round(float(price), 4))
        except Exception:
            continue  # Ignorer les erreurs individuelles

    return result

if __name__ == "__main__":
    print(GetLastValuePlacement(["US0378331005", "AIR.PA"],"2025-08-21"))
