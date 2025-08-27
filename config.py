# config.py
from datetime import datetime

# 데이터 조회 기간
START_DATE = "2022-01-01"
END_DATE = datetime.today().strftime('%Y-%m-%d')


# 💡 분석할 자산 목록 (자유롭게 추가/수정/삭제 가능)
ASSETS = {
    '국내주식': [
        {'name': '삼성전자', 'ticker': '005930.KS'},
        {'name': 'SK하이닉스', 'ticker': '000660.KS'},
        {'name': 'NAVER', 'ticker': '035420.KS'}
    ],
    '해외주식': [
        {'name': 'Apple', 'ticker': 'AAPL'},
        {'name': 'NVIDIA', 'ticker': 'NVDA'},
        {'name': 'Tesla', 'ticker': 'TSLA'}
    ],
    '채권': [
        # 국채 (만기 20년 이상 미국채)
        {'name': '미국 장기채', 'ticker': 'TLT'},
        # 회사채 (투자등급 미국 회사채)
        {'name': '미국 회사채', 'ticker': 'LQD'}
    ],
    '원자재/암호화폐': [
        {'name': '금', 'ticker': 'GLD'},
        {'name': '비트코인', 'ticker': 'BTC-USD'}
    ]
}

# 백테스팅 비교 기준 지수 (코스피: ^KS11, S&P 500: ^GSPC, 나스닥: ^IXIC)
BENCHMARK_CONFIG = {
    'name': 'S&P 500',    # 화면에 표시될 이름
    'ticker': '^GSPC'      # 데이터 조회용 티커
}