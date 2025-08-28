# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy.signal import find_peaks
from config import ASSETS, BENCHMARK_CONFIG
from data_fetcher import fetch_data, fetch_benchmark_data, fetch_risk_free_rate 
from portfolio_analyzer import calculate_returns, get_portfolio_performance
from datetime import datetime

# --- 1. 페이지 기본 설정 ---
st.set_page_config(page_title="금융 포트폴리오 대시보드", layout="wide")
st.title("📈 나만의 금융 포트폴리오 대시보드")

# --- 2. Session State 초기화 ---
if 'saved_portfolios' not in st.session_state:
    st.session_state['saved_portfolios'] = []
if 'selected_assets' not in st.session_state:
    st.session_state['selected_assets'] = [asset for asset_class in ASSETS.values() for asset in asset_class]

# --- 3. 사이드바 UI ---
with st.sidebar:
    st.header("⚖️ 포트폴리오 구성")
    default_options = [f"{asset['name']} ({asset['ticker']})" for asset in st.session_state['selected_assets']]
    selected_options = st.multiselect("분석할 자산을 선택하세요", options=default_options, default=default_options)
    selected_tickers = [opt.split('(')[-1].replace(')','') for opt in selected_options]
    
    st.write("---")
    custom_ticker = st.text_input("추가할 종목 티커를 입력하세요 (예: 005930.KS 또는 AAPL)")
    if custom_ticker:
        custom_ticker = custom_ticker.upper()
        if not any(asset['ticker'] == custom_ticker for asset in st.session_state['selected_assets']):
            new_asset = {'name': custom_ticker, 'ticker': custom_ticker}
            st.session_state['selected_assets'].append(new_asset)
            st.rerun()
            
    st.header("⚖️ 포트폴리오 비중 설정")
    weights = {}
    current_portfolio_assets = [asset for asset in st.session_state['selected_assets'] if asset['ticker'] in selected_tickers]

    if not current_portfolio_assets:
        st.warning("분석할 자산을 1개 이상 선택해주세요.")
    else:
        grouped_assets = {}
        for asset in current_portfolio_assets:
            asset_class_name = "기타"
            for class_name, assets_list in ASSETS.items():
                if any(a['ticker'] == asset['ticker'] for a in assets_list):
                    asset_class_name = class_name
                    break
            if asset_class_name not in grouped_assets: grouped_assets[asset_class_name] = []
            grouped_assets[asset_class_name].append(asset)
        
        for asset_class, assets_list in grouped_assets.items():
            with st.expander(f"**{asset_class}**"):
                for asset in assets_list:
                    weights[asset['name']] = st.slider(f"{asset['name']} (%)", 0, 100, int(100/len(current_portfolio_assets)), 5, key=f"slider_{asset['ticker']}")
        
        total_weight = sum(weights.values())
        if total_weight != 100: st.warning(f"비중의 총합이 100%가 되어야 합니다. (현재: {total_weight}%)")

        st.write("---")
        portfolio_name = st.text_input("저장할 포트폴리오 이름을 입력하세요", "나의 첫 포트폴리오")
        if st.button("💾 현재 포트폴리오 저장"):
            if total_weight == 100:
                saved_port = {'name': portfolio_name, 'weights': weights, 'assets': current_portfolio_assets}
                st.session_state['saved_portfolios'].append(saved_port)
                st.success(f"'{portfolio_name}'이(가) 저장되었습니다!")
            else:
                st.error("비중의 총합이 100%일 때만 저장할 수 있습니다.")

# --- 4. 메인 페이지 (탭으로 구분) ---
tab1, tab2 = st.tabs(["📊 내 포트폴리오 분석", "🗂️ 저장된 포트폴리오 비교"])

with tab1:
    current_assets_config = {'Current': current_portfolio_assets}
    asset_data = fetch_data(current_assets_config)

    if not asset_data.empty and total_weight == 100:
        daily_returns, _ = calculate_returns(asset_data)
        weight_list = [weights.get(col, 0) / 100 for col in asset_data.columns]
        
        st.header("📊 포트폴리오 구성")
        asset_to_class = {asset['name']: class_name for class_name, assets_list in ASSETS.items() for asset in assets_list}
        pie_df = pd.DataFrame({'자산': weights.keys(), '비중 (%)': weights.values()})
        pie_df['자산군'] = pie_df['자산'].map(asset_to_class).fillna('기타')
        
        fig_sunburst = px.sunburst(pie_df, path=['자산군', '자산'], values='비중 (%)',
                                   title='내 포트폴리오 비중 (자산군별)',
                                   color='자산군',
                                   color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_sunburst.update_traces(textinfo="label+percent parent")
        st.plotly_chart(fig_sunburst, use_container_width=True)
        
        st.header("📈 포트폴리오 주요 성과")
        risk_free_rate = fetch_risk_free_rate()
        annual_return, volatility, sharpe = get_portfolio_performance(weight_list, daily_returns, risk_free_rate)
        col1, col2, col3 = st.columns(3)
        col1.metric("연평균 수익률", f"{annual_return*100:.2f}%")
        col2.metric("연간 변동성", f"{volatility*100:.2f}%")
        col3.metric("샤프 지수", f"{sharpe:.2f}", help=f"무위험 수익률 {risk_free_rate*100:.2f}% 기준")
        
        st.header("🆚 포트폴리오 vs. 벤치마크")
        benchmark_data = fetch_benchmark_data(BENCHMARK_CONFIG['ticker'])
        if not benchmark_data.empty:
            
            # 💡💡💡 ValueError 오류 해결: 두 변수 모두 1차원으로 변환 💡💡💡
            portfolio_cum_returns_np = (1 + daily_returns.dot(weight_list)).cumprod().values
            portfolio_series = pd.Series(portfolio_cum_returns_np.flatten(), index=daily_returns.index)

            benchmark_daily_returns = benchmark_data.pct_change().dropna()
            benchmark_cum_returns_np = (1 + benchmark_daily_returns).cumprod().values
            benchmark_series = pd.Series(benchmark_cum_returns_np.flatten(), index=benchmark_daily_returns.index)
            
            comparison_df = pd.DataFrame({'My Portfolio': portfolio_series, 'Benchmark': benchmark_series}).dropna()
            normalized_df = comparison_df / comparison_df.iloc[0]

            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(x=normalized_df.index, y=normalized_df['My Portfolio'], mode='lines', name='My Portfolio'))
            fig_line.add_trace(go.Scatter(x=normalized_df.index, y=normalized_df['Benchmark'], mode='lines', name='Benchmark', line=dict(dash='dot')))
            
            peaks, _ = find_peaks(normalized_df['My Portfolio'], distance=100)
            fig_line.add_trace(go.Scatter(x=normalized_df.index[peaks], y=normalized_df['My Portfolio'].iloc[peaks], mode='markers', name='고점', marker=dict(color='red', size=8, symbol='triangle-down')))
            troughs, _ = find_peaks(-normalized_df['My Portfolio'], distance=100)
            fig_line.add_trace(go.Scatter(x=normalized_df.index[troughs], y=normalized_df['My Portfolio'].iloc[troughs], mode='markers', name='저점', marker=dict(color='blue', size=8, symbol='triangle-up')))
            
            st.write(f"내 포트폴리오와 **{BENCHMARK_CONFIG['name']}** 지수의 성과를 비교합니다.")
            st.plotly_chart(fig_line, use_container_width=True)

    elif not current_portfolio_assets: st.info("사이드바에서 분석할 자산을 선택해주세요.")
    else: st.info("사이드바에서 비중의 총합을 100%로 맞춰주세요.")

with tab2:
    st.header("🗂️ 저장된 포트폴리오 비교")
    if not st.session_state['saved_portfolios']:
        st.info("저장된 포트폴리오가 없습니다.")
    else:
        col1, col2 = st.columns(2)
        start_date = col1.date_input("시작일", value=pd.to_datetime("2018-01-01"), min_value=pd.to_datetime("2010-01-01"), max_value=datetime.today())
        end_date = col2.date_input("종료일", value=datetime.today(), min_value=pd.to_datetime("2010-01-01"), max_value=datetime.today())
        
        results = []
        all_comparison_returns = pd.DataFrame()
        
        for port in st.session_state['saved_portfolios']:
            port_assets_config = {'Portfolio': port['assets']}
            port_asset_data = fetch_data(port_assets_config)
            
            if not port_asset_data.empty:
                filtered_data = port_asset_data.loc[start_date:end_date]
                if not filtered_data.empty:
                    port_daily_returns, _ = calculate_returns(filtered_data)
                    port_weight_list = [port['weights'].get(col, 0) / 100 for col in filtered_data.columns]
                    
                    ann_ret, vol, shp = get_portfolio_performance(port_weight_list, port_daily_returns)
                    results.append({'포트폴리오 이름': port['name'], '연평균 수익률 (%)': ann_ret*100, '연간 변동성 (%)': vol*100, '샤프 지수': shp})
                    
                    cum_returns = (1 + port_daily_returns.dot(port_weight_list)).cumprod()
                    all_comparison_returns[port['name']] = cum_returns
        
        st.subheader("성과 지표 비교")
        st.dataframe(pd.DataFrame(results).set_index('포트폴리오 이름').style.format("{:.2f}"))
        
        st.subheader("누적 수익률 비교")
        if not all_comparison_returns.empty:
            normalized_returns = all_comparison_returns / all_comparison_returns.iloc[0]
            st.line_chart(normalized_returns)