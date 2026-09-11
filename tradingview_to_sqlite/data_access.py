# pyrefly: ignore [missing-import]
from datetime import timedelta
from tradingview_to_sqlite import contracts
from sqlite3 import dbapi2
from .database_setup import db_connection
import pandas as pd

def load_prices(ticker, start_date, end_date):
    """
    Load price data from the database for a specific ticker and date range.

    Parameters
    ----------
    ticker : str
        The ticker symbol of the asset as "[exchange]:[underlying_asset][expiry_month][expiry_year].
    start_date : str
        The start date in 'YYYY-MM-DD' format.
    end_date : str
        The end date in 'YYYY-MM-DD' format.
    
    Returns
    -------
    pd.DataFrame
        A DataFrame containing the price data.
    """
    return pd.read_sql_query("SELECT * FROM futures WHERE ticker = ? AND date BETWEEN ? AND ?", db_connection(), params=(ticker, start_date, end_date), parse_dates=["date"])


def load_continuous_contract(asset, start_date, end_date, roll_rule="1st"):
    """
    Load continuous contract data from the database for a specific asset.
    
    Parameters
    ----------
    asset : str
        The underlying asset.
    start_date : str
        The start date in 'YYYY-MM-DD' format.
    end_date : str
        The end date in 'YYYY-MM-DD' format.
    roll_rule : str
        The roll rule to use for continuous contracts. Valid options are '1st', '2nd' or '3rd'.
    
    Returns
    -------
    pd.DataFrame
        A DataFrame containing the continuous contract data.
    """
    if roll_rule not in ["1st", "2nd", "3rd"]:
        raise ValueError("Invalid roll rule. Valid options are '1st', '2nd' or '3rd'.")

    contracts_meta_data = pd.read_sql_query("""
        SELECT ticker, exchange, expiry_month, expiry_year, expiration_date FROM
        contracts_meta_data WHERE expiration_date > ? AND symbol = ?""", db_connection(), params=(start_date, asset)
    )

    contracts_meta_data.sort_values(by = ["expiry_year", "expiry_month"], ascending=[True, True], inplace=True)
    contracts_meta_data.reset_index(drop=True, inplace=True)

    if roll_rule == "1st":
        continuos_series = []

        loop_counter = 0

        while True:
            contract_ticker = contracts_meta_data['ticker'].iloc[loop_counter]
            contract_data = load_prices(contract_ticker, start_date, end_date)
            contract_max_date = contract_data['date'].max()

            if contract_max_date >= end_date:
                continuos_series.append(contract_data[contract_data['date'] <= end_date])
                break
            
            continuos_series.append(contract_data)
            start_date = str(contract_data['date'].max() + timedelta(days=1))
            loop_counter += 1

        continuos_contract = pd.concat(continuos_series)
        continuos_contract.sort_values(by = ["date"], ascending=[True], inplace=True)
        continuos_contract.reset_index(drop=True, inplace=True)

        return continuos_contract

    elif roll_rule == "2nd":
        continuos_series = []
        
        loop_counter = 1

        while True:
            contract_ticker = contracts_meta_data['ticker'].iloc[loop_counter]
            contract_data = load_prices(contract_ticker, start_date, end_date)
            contract_max_date = contract_data['date'].max()

            if contract_max_date >= end_date:
                continuos_series.append(contract_data[contract_data['date'] <= end_date])
                break
            
            continuos_series.append(contract_data)
            start_date = str(contract_data['date'].max() + timedelta(days=1))
            loop_counter += 1

        continuos_contract = pd.concat(continuos_series)
        continuos_contract.sort_values(by = ["date"], ascending=[True], inplace=True)
        continuos_contract.reset_index(drop=True, inplace=True)

        return continuos_contract
    
    elif roll_rule == "3rd":
        continuos_series = []
        
        loop_counter = 2

        while True:
            contract_ticker = contracts_meta_data['ticker'].iloc[loop_counter]
            contract_data = load_prices(contract_ticker, start_date, end_date)
            contract_max_date = contract_data['date'].max()

            if contract_max_date >= end_date:
                continuos_series.append(contract_data[contract_data['date'] <= end_date])
                break
            
            continuos_series.append(contract_data)
            start_date = str(contract_data['date'].max() + timedelta(days=1))
            loop_counter += 1

        continuos_contract = pd.concat(continuos_series)
        continuos_contract.sort_values(by = ["date"], ascending=[True], inplace=True)
        continuos_contract.reset_index(drop=True, inplace=True)

        return continuos_contract
    


    
    


    