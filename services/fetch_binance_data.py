"""
Script de récupération des bougies BTC/USDT depuis l'API Binance.
Récupère les intervalles 1h, 4h, 1d, 1w sur 5 ans et les sauvegarde en CSV.
"""

import os
import time
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone

# === CONFIGURATION ===
SYMBOL = "BTCUSDT"
INTERVALS = {
    "1h": "1h",
    "4h": "4h",
    "1d": "1d",
    "1w": "1w",
}
YEARS_BACK = 5
LIMIT = 1000  # Max candles par requête Binance
OUTPUT_DIR = "data"
BASE_URL = "https://api.binance.com/api/v3/klines"

# Colonnes retournées par l'API Binance
COLUMNS = [
    "Timestamp",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
    "Close_time",
    "Quote_asset_volume",
    "Number_of_trades",
    "Taker_buy_base_asset_volume",
    "Taker_buy_quote_asset_volume",
    "Ignore",
]


def fetch_klines(symbol: str, interval: str, start_time: int, limit: int = 1000) -> list:
    """
    Récupère les klines depuis l'API Binance.
    Retourne une liste de klines (listes).
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "limit": limit,
    }
    try:
        resp = requests.get(BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"  [ERREUR] Requête échouée : {e}")
        # Retry après une pause
        time.sleep(2)
        try:
            resp = requests.get(BASE_URL, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e2:
            print(f"  [ERREUR] Second essai échoué : {e2}")
            return []


def calc_interval_ms(interval: str) -> int:
    """Convertit un intervalle Binance en millisecondes."""
    unit = interval[-1]
    value = int(interval[:-1])
    if unit == "m":
        return value * 60 * 1000
    elif unit == "h":
        return value * 60 * 60 * 1000
    elif unit == "d":
        return value * 24 * 60 * 60 * 1000
    elif unit == "w":
        return value * 7 * 24 * 60 * 60 * 1000
    else:
        raise ValueError(f"Intervalle inconnu : {interval}")


def download_all_klines(symbol: str, interval: str, years: int) -> pd.DataFrame:
    """
    Télécharge toutes les klines pour un intervalle donné sur N années.
    Retourne un DataFrame avec les colonnes : Timestamp, Open, High, Low, Close, Volume.
    """
    interval_ms = calc_interval_ms(interval)
    end_time = int(datetime.now(timezone.utc).timestamp() * 1000)
    start_time = int((datetime.now(timezone.utc) - timedelta(days=years * 365)).timestamp() * 1000)

    all_klines = []
    current_start = start_time
    nb_requests = 0

    print(f"  Début téléchargement {interval}...")
    print(f"    De {datetime.fromtimestamp(start_time/1000, tz=timezone.utc).strftime('%Y-%m-%d')} "
          f"à {datetime.fromtimestamp(end_time/1000, tz=timezone.utc).strftime('%Y-%m-%d')}")

    while current_start < end_time:
        klines = fetch_klines(symbol, interval, current_start, LIMIT)
        nb_requests += 1

        if not klines:
            print(f"  [AVERTISSEMENT] Aucune donnée reçue, arrêt de la boucle.")
            break

        all_klines.extend(klines)

        # Mise à jour du curseur : dernière bougie + 1ms
        last_open_time = klines[-1][0]
        if last_open_time <= current_start:
            # Évite boucle infinie si Binance retourne les mêmes données
            last_open_time = current_start + interval_ms
        current_start = last_open_time + 1

        # Progression
        if nb_requests % 10 == 0:
            progress = (current_start - start_time) / (end_time - start_time) * 100
            print(f"    Progression : {min(progress, 100):.0f}% ({nb_requests} requêtes, {len(all_klines)} bougies)")

        # Rate limiting : max 1200 requêtes/min, on reste large (~600/min)
        time.sleep(0.1)

    print(f"    Terminé : {len(all_klines)} bougies récupérées en {nb_requests} requêtes.")

    if not all_klines:
        print(f"  [ERREUR] Aucune donnée récupérée pour {interval}.")
        return pd.DataFrame()

    # Conversion en DataFrame
    df = pd.DataFrame(all_klines, columns=COLUMNS)
    df = df[["Timestamp", "Open", "High", "Low", "Close", "Volume"]].copy()

    # Conversion des types
    df["Timestamp"] = pd.to_datetime(df["Timestamp"].astype(float), unit="ms", utc=True)
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col])

    # Suppression des doublons éventuels
    df = df.drop_duplicates(subset="Timestamp").sort_values("Timestamp").reset_index(drop=True)

    print(f"    DataFrame final : {len(df)} lignes.")
    return df


def main():
    """Point d'entrée principal."""
    print("=" * 60)
    print("Téléchargement des bougies BTC/USDT - Binance")
    print(f"Période : {YEARS_BACK} ans | Intervalles : {', '.join(INTERVALS.keys())}")
    print("=" * 60)

    # Création du dossier data si nécessaire
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for label, interval in INTERVALS.items():
        print(f"\n>>> Traitement de l'intervalle {label} <<<")
        df = download_all_klines(SYMBOL, interval, YEARS_BACK)

        if df.empty:
            print(f"  [ERREUR] Échec du téléchargement pour {label}, intervalle ignoré.")
            continue

        # Sauvegarde en CSV
        filename = os.path.join(OUTPUT_DIR, f"BTC_USDT_{label}_5y.csv")
        df.to_csv(filename, index=False)
        print(f"  Sauvegardé dans : {filename}")

        # Petit résumé
        print(f"  Première bougie : {df['Timestamp'].iloc[0]}")
        print(f"  Dernière bougie  : {df['Timestamp'].iloc[-1]}")
        print(f"  Nb lignes        : {len(df)}")

    print("\n" + "=" * 60)
    print("Téléchargement terminé !")
    print("=" * 60)


if __name__ == "__main__":
    main()