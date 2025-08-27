# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from config import ASSETS, BENCHMARK_CONFIG
from data_fetcher import fetch_data, fetch_benchmark_data, fetch_ohlcv # fetch_ohlcv 추가
from portfolio_analyzer import calculate_returns, get_portfolio_performance
from ml_predictor import train_and_predict # 새로 만든 ml_predictor 임포트

# --- 웹 페이지 기본 설정 ---
st.set_page_config(page_title="금융 포트폴리오 대시보드", layout="wide")
st.title("📈 나만의 금융 포트폴리오 대시보드")
st.write("다양한 자산으로 포트폴리오를 구성하고 성과를 분석합니다.")

# --- 데이터 로딩 ---
asset_data = fetch_data(ASSETS)

if not asset_data.empty:
    daily_returns, cumulative_returns = calculate_returns(asset_data)

    # --- 사이드바 ---
    st.sidebar.header("⚖️ 포트폴리오 비중 설정")
    weights = {}
    
    valid_assets_in_config = [asset for asset_class in ASSETS.values() for asset in asset_class if asset['name'] in asset_data.columns]
    
    grouped_assets = {}
    for asset in valid_assets_in_config:
        for class_name, assets_list in ASSETS.items():
            if asset in assets_list:
                if class_name not in grouped_assets: grouped_assets[class_name] = []
                grouped_assets[class_name].append(asset)
                break

    for asset_class, assets_list in grouped_assets.items():
        st.sidebar.subheader(asset_class)
        for asset in assets_list:
            asset_name = asset['name']
            initial_weight = int(100 / len(asset_data.columns))
            weights[asset_name] = st.sidebar.slider(f"{asset_name} (%)", 0, 100, initial_weight, 5, key=asset_name)

    total_weight = sum(weights.values())
    if total_weight != 100: st.sidebar.warning(f"비중의 총합이 100%가 되어야 합니다. (현재: {total_weight}%)")
    
    weight_list = [weights.get(col, 0) / 100 for col in asset_data.columns]
    
    # --- 메인 페이지 ---
    st.header("📊 포트폴리오 구성")
    valid_weights = {name: w for name, w in weights.items() if w > 0}
    if total_weight == 100 and valid_weights:
        pie_df = pd.DataFrame({'자산': valid_weights.keys(), '비중 (%)': valid_weights.values()})
        fig = px.pie(pie_df, values='비중 (%)', names='자산', title='내 포트폴리오 비중')
        st.plotly_chart(fig, use_container_width=True)
    elif total_weight != 100: st.info("사이드바에서 비중의 총합을 100%로 맞춰주세요.")
    else: st.warning("포트폴리오에 포함된 자산이 없습니다.")

    st.header("📈 포트폴리오 주요 성과")
    if total_weight == 100:
        annual_return, annual_volatility, sharpe_ratio = get_portfolio_performance(weight_list, daily_returns)
        
        # 💡💡💡 머신러닝 예측 기능 추가 💡💡💡
        with st.spinner('🤖 머신러닝 모델이 미래 수익률을 예측하고 있습니다...'):
            weighted_prediction = 0
            for asset in valid_assets_in_config:
                asset_weight = weights.get(asset['name'], 0) / 100
                if asset_weight > 0:
                    ohlcv_data = fetch_ohlcv(asset['ticker'])
                    if not ohlcv_data.empty:
                        prediction = train_and_predict(ohlcv_data)
                        weighted_prediction += prediction * asset_weight
        
        col1, col2, col3, col4 = st.columns(4) # 4개 컬럼으로 변경
        col1.metric("연평균 수익률", f"{annual_return*100:.2f}%")
        col2.metric("연간 변동성", f"{annual_volatility*100:.2f}%")
        col3.metric("샤프 지수", f"{sharpe_ratio:.2f}")
        # 예측 결과 표시
        col4.metric("예상 월간 수익률 (ML)", f"{weighted_prediction*100:.2f}%", help="XGBoost 모델이 예측한 향후 20 거래일의 포트폴리오 수익률입니다.")

        st.header("💹 포트폴리오 누적 수익률")
        portfolio_cumulative_returns = (1 + daily_returns.dot(weight_list)).cumprod()
        st.line_chart(portfolio_cumulative_returns)
    else:
        st.info("사이드바에서 비중의 총합을 100%로 맞춰주세요.")

    # --- 포트폴리오 백테스팅 ---
    st.header("🆚 포트폴리오 vs. 벤치마크")
    benchmark_data = fetch_benchmark_data(BENCHMARK_CONFIG['ticker'])
    if not benchmark_data.empty and 'daily_returns' in locals() and total_weight == 100:
        portfolio_cum_returns_np = (1 + daily_returns.dot(weight_list)).cumprod().values
        portfolio_series = pd.Series(portfolio_cum_returns_np.flatten(), index=daily_returns.index)
        benchmark_daily_returns = benchmark_data.pct_change().dropna()
        benchmark_cum_returns_np = (1 + benchmark_daily_returns).cumprod().values
        benchmark_series = pd.Series(benchmark_cum_returns_np.flatten(), index=benchmark_daily_returns.index)
        comparison_df = pd.DataFrame({'My Portfolio': portfolio_series, 'Benchmark': benchmark_series}).dropna()
        normalized_df = comparison_df / comparison_df.iloc[0]
        st.write(f"내 포트폴리오와 **{BENCHMARK_CONFIG['name']}** 지수의 성과를 비교합니다.")
        st.line_chart(normalized_df)
        portfolio_final_return = normalized_df['My Portfolio'].iloc[-1]
        benchmark_final_return = normalized_df['Benchmark'].iloc[-1]
        st.write(f"- **내 포트폴리오 최종 성과:** `{portfolio_final_return:.2f}`")
        st.write(f"- **벤치마크 최종 성과:** `{benchmark_final_return:.2f}`")
        if portfolio_final_return > benchmark_final_return: st.success("축하합니다! 내 포트폴리오가 시장 평균보다 높은 성과를 거두었습니다. 🎉")
        else: st.warning("아쉽지만 내 포트폴리오가 시장 평균보다 낮은 성과를 기록했습니다. 😢")
else:
    st.error("초기 데이터를 불러오는 데 실패했습니다. config.py의 티커를 확인하거나 인터넷 연결을 확인해주세요.")


st.header("🗺️ 프로젝트 전체 흐름도")
with st.expander("플로우차트로 전체 과정 보기"):
    flowchart = """
    digraph G {
        rankdir="TB";
        node [shape=box, style="rounded,filled", fillcolor="#f8f9fa", fontname="sans-serif"];
        edge [fontname="sans-serif"];

        subgraph cluster_ui {
            label = "1. 사용자 인터페이스 (app.py)";
            bgcolor="#e9ecef";
            UI [label="사용자 입력 (비중 조절 슬라이더)"];
        }

        subgraph cluster_data {
            label = "2. 데이터 계층";
            bgcolor="#dee2e6";
            Config [label="설정값 로드 (config.py)"];
            Fetcher [label="데이터 수집 (data_fetcher.py)"];
        }

        subgraph cluster_logic {
            label = "3. 분석 계층";
            bgcolor="#ced4da";
            Analyzer [label="성과 분석 (portfolio_analyzer.py)"];
        }

        subgraph cluster_view {
            label = "4. 시각화 계층 (app.py)";
            bgcolor="#adb5bd";
            PieChart [label="파이 차트 (비중)"];
            Metrics [label="성과 지표 (수익률, 변동성 등)"];
            LineChart1 [label="누적 수익률 그래프"];
            LineChart2 [label="벤치마크 비교 그래프"];
        }

        UI -> Config [label="  1. 설정 요청"];
        Config -> Fetcher [label="  2. 자산 목록 전달"];
        Fetcher -> Analyzer [label="  3. 가격 데이터 전달"];
        UI -> Analyzer [label="  4. 포트폴리오 비중 전달"];
        Analyzer -> Metrics [label="  5. 분석 결과 전달"];
        Analyzer -> LineChart1 [label="  5. 분석 결과 전달"];
        Analyzer -> LineChart2 [label="  5. 분석 결과 전달"];
        UI -> PieChart [label="  비중 직접 전달"];
    }
    """
    st.graphviz_chart(flowchart)
