# portfolio_analyzer.py
import pandas as pd
import numpy as np

def calculate_returns(data: pd.DataFrame):
    """자산별 일일 수익률과 누적 수익률을 계산합니다."""
    daily_returns = data.pct_change().dropna()
    cumulative_returns = (1 + daily_returns).cumprod()
    return daily_returns, cumulative_returns

def get_portfolio_performance(weights: list, daily_returns: pd.DataFrame, risk_free_rate: float = 0.0):
    """가중치에 따른 포트폴리오의 연간 수익률, 변동성, 샤프 지수를 계산합니다."""
    # 포트폴리오의 일일 수익률 계산
    portfolio_returns = np.dot(daily_returns, weights)
    
    # 연간 수익률 (기하 평균)
    # 연간 거래일은 약 252일
    annual_return = (1 + np.mean(portfolio_returns))**252 - 1
    
    # 연간 변동성
    annual_volatility = np.std(portfolio_returns) * np.sqrt(252)
    
    # 샤프 지수 (무위험 수익률은 0으로 가정)
    # 샤프 지수는 우리가 감수한 위험 한 단위당, 얼마나 높은 수익을 얻었는지를 보여주는 '가성비' 지표
    sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility if annual_volatility != 0 else 0
    
    return annual_return, annual_volatility, sharpe_ratio