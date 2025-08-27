# ml_predictor.py
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split

def create_features(df):
    """주가 데이터로부터 머신러닝 모델이 사용할 Feature를 생성합니다."""
    df_new = df.copy()
    
    # ✅ 컬럼 이름을 모두 소문자로 변경하여 대소문자 문제를 원천 차단합니다.
    df_new.columns = [col.lower() for col in df_new.columns]
    
    # ✅ 'close' 컬럼이 있는지 다시 한번 확인합니다.
    if 'close' not in df_new.columns:
        print("Warning: ML Feature 생성을 위한 'close' 컬럼이 없습니다.")
        return pd.DataFrame() # 컬럼이 없으면 빈 데이터프레임 반환

    # 이제 모든 컬럼 접근을 소문자로 안전하게 통일합니다.
    df_new['ma5'] = df_new['close'].rolling(window=5).mean()
    df_new['ma20'] = df_new['close'].rolling(window=20).mean()
    
    delta = df_new['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df_new['rsi'] = 100 - (100 / (1 + rs))
    
    df_new['volatility'] = df_new['close'].rolling(window=20).std()
    
    df_new.dropna(inplace=True)
    return df_new

def train_and_predict(df, prediction_days=20):
    """
    주어진 데이터로 XGBoost 모델을 학습하고 미래 수익률을 예측합니다.
    prediction_days: 예측할 미래 기간 (거래일 기준, 약 1개월)
    """
    if df.empty:
        return 0.0

    # 1. Feature 생성
    df_featured = create_features(df)
    
    if df_featured.empty or 'close' not in df_featured.columns:
        return 0.0

    # 2. Target 변수 생성 (미래 수익률, 소문자 'close' 사용)
    df_featured['target'] = df_featured['close'].pct_change(prediction_days).shift(-prediction_days)
    df_featured.dropna(inplace=True)

    if df_featured.empty:
        return 0.0

    # 3. 데이터 준비
    features = ['ma5', 'ma20', 'rsi', 'volatility']
    X = df_featured[features]
    y = df_featured['target']
    
    X_predict = X.iloc[[-1]] 
    
    # 4. 모델 학습
    model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
    model.fit(X, y)
    
    # 5. 미래 수익률 예측
    prediction = model.predict(X_predict)
    
    return prediction[0]
