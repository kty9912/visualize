# data_fetcher.py
import yfinance as yf
import pandas as pd
import streamlit as st
from config import START_DATE, END_DATE

@st.cache_data
def fetch_data(assets_config: dict):
    # 이 함수는 수정할 필요 없습니다. (이전과 동일)
    all_tickers = [asset['ticker'] for asset_class in assets_config.values() for asset in asset_class]
    raw_data = yf.download(all_tickers, start=START_DATE, end=END_DATE)

    if raw_data.empty:
        st.error("데이터를 가져오는 데 실패했습니다. 티커가 올바른지 확인해주세요.")
        return pd.DataFrame()

    if isinstance(raw_data.columns, pd.MultiIndex):
        if "Adj Close" in raw_data.columns.get_level_values(0):
            price_data = raw_data["Adj Close"].copy()
        elif "Close" in raw_data.columns.get_level_values(0):
            price_data = raw_data["Close"].copy()
        else:
            st.error("다운로드한 데이터에 'Adj Close' 또는 'Close' 컬럼이 없습니다.")
            return pd.DataFrame()
    else:
        if "Adj Close" in raw_data.columns:
            price_data = raw_data[["Adj Close"]].copy()
            price_data.columns = [all_tickers[0]]
        elif "Close" in raw_data.columns:
            price_data = raw_data[["Close"]].copy()
            price_data.columns = [all_tickers[0]]
        else:
            st.error("다운로드한 데이터에 'Adj Close' 또는 'Close' 컬럼이 없습니다.")
            return pd.DataFrame()
            
    ticker_to_name = {asset['ticker']: asset['name'] for asset_class in assets_config.values() for asset in asset_class}
    price_data.rename(columns=ticker_to_name, inplace=True)
    price_data.dropna(axis=0, how='all', inplace=True)
    price_data.dropna(axis=1, how='all', inplace=True)
    return price_data



@st.cache_data
def fetch_ohlcv(ticker: str):
    """
    지정된 티커의 OHLCV 데이터를 가져와서 어떤 데이터 구조에도 대응할 수 있도록 완벽하게 정제합니다.
    """
    df = yf.download(ticker, start=START_DATE, end=END_DATE)

    if df.empty:
        return pd.DataFrame()

    # ✅ yfinance가 예기치 않게 다중 컬럼을 반환할 경우, 단일 컬럼으로 변경
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(0)

    cols_to_process = ["Open", "High", "Low", "Close", "Volume"]
    
    # ✅ 실제 존재하는 컬럼에 대해서만 숫자 변환을 적용 (더 안전한 방법)
    existing_cols = [col for col in cols_to_process if col in df.columns]
    df[existing_cols] = df[existing_cols].apply(pd.to_numeric, errors='coerce')

    # ✅ NaN 값을 포함한 행을 완전히 제거
    df.dropna(subset=existing_cols, inplace=True)

    return df


@st.cache_data
def fetch_benchmark_data(ticker: str):
    """지정된 벤치마크 지수의 종가 데이터를 가져옵니다."""
    df = yf.download(ticker, start=START_DATE, end=END_DATE)
    if df.empty:
        return pd.Series(dtype='float64')
    
    # 'Adj Close'가 있으면 우선 사용, 없으면 'Close' 사용
    if 'Adj Close' in df.columns:
        return df['Adj Close']
    else:
        return df['Close']