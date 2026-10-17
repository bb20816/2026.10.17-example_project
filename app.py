"""
🌡️ 서울 연평균 기온 분석 Streamlit 앱
파일: seoul_temperature.csv (날짜, 지점, 평균기온(℃), 최저기온(℃), 최고기온(℃))

처리 규칙
- 주의 1: 날짜 값 앞에 탭 문자가 있어 코드에서 strip 처리
- 주의 2: 1950 ~ 1953년 결측치는 연평균·선택 구간 평균/최고/최저 계산에서
  제외하고, 화면 하단에 제외 사실을 명시
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(page_title="서울 연평균 기온", page_icon="🌡️", layout="wide")

# 1) 데이터 로드 및 전처리 ------------------------------------
@st.cache_data
def load_data(path: str = "seoul_temperature.csv") -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"지점": str})

    # 주의 1: 날짜 문자열 앞에 붙은 탭('\t') 제거 후 날짜로 변환
    df["날짜"] = df["날짜"].astype(str).str.replace('[\t"]', "", regex=True)
    df["날짜"] = pd.to_datetime(df["날짜"], format="%Y-%m-%d", errors="coerce")
    df = df.dropna(subset=["날짜"])

    # 수치 컬럼은 변환 불가값을 결측(NaN)으로 처리
    for col in ["평균기온(℃)", "최저기온(℃)", "최고기온(℃)"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 결측 기온이 있는 행은 평균 계산에서 제외
    df["연도"] = df["날짜"].dt.year
    df = df.dropna(subset=["연도", "평균기온(℃)", "최저기온(℃)", "최고기온(℃)"])
    return df


df = load_data()

# 2) 연도별 집계 + 5년 이동평균 ----------------------------------
yearly = (
    df.groupby("연도")
    .agg(
        연평균기온=("평균기온(℃)", "mean"),
        최저기온_연평균=("최저기온(℃)", "mean"),
        최고기온_연평균=("최고기온(℃)", "mean"),
        유효_관측일수=("평균기온(℃)", "count"),
    )
    .reset_index()
)

# 5년 이동평균(연평균기온 기준, 초기 4년은 부분 윈도우 사용)
yearly["이동평균5년"] = yearly["연평균기온"].rolling(window=5, min_periods=1).mean()

# 3) 사이드바: 연도 범위 슬라이더 ---------------------------------
min_year, max_year = int(yearly["연도"].min()), int(yearly["연도"].max())
year_range = st.sidebar.slider(
    "연도 범위 선택",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
)
st.sidebar.caption(f"전체 기간: {min_year}년 ~ {max_year}년 (총 {len(yearly)}개 연도)")

# 4) 선택 구간 통계 -------------------------------------------------
sel_daily = df[(df["연도"] >= year_range[0]) & (df["연도"] <= year_range[1])]
sel_yearly = yearly[(yearly["연도"] >= year_range[0]) & (yearly["연도"] <= year_range[1])]

if len(sel_daily) > 0:
    stat_mean = sel_daily["평균기온(℃)"].mean()
    stat_max = sel_daily["최고기온(℃)"].mean()
    stat_min = sel_daily["최저기온(℃)"].mean()
    st.subheader(f"선택 구간 ({year_range[0]}년 ~ {year_range[1]}년) 기온 통계")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("평균기온", f"{stat_mean:.2f} ℃")
    with c2:
        st.metric("최고기온(평균)", f"{stat_max:.2f} ℃")
    with c3:
        st.metric("최저기온(평균)", f"{stat_min:.2f} ℃")
    st.caption(f"선택 구간 관측 수: {len(sel_daily)}일 / 연평균 기준 {len(sel_yearly)}개 연도")
else:
    st.subheader("선택 구간 기온 통계")
    st.info("선택한 연도 범위에 데이터가 없습니다.")

# 5) 그래프 -------------------------------------------------------
fig = go.Figure()

# 연도별 평균기온
fig.add_trace(
    go.Scatter(
        x=yearly["연도"],
        y=yearly["연평균기온"],
        mode="lines+markers",
        name="연평균기온",
        line=dict(color="#2E86AB", width=2),
        marker=dict(size=4),
    )
)

# 5년 이동평균 (같은 그래프에 겹침)
fig.add_trace(
    go.Scatter(
        x=yearly["연도"],
        y=yearly["이동평균5년"],
        mode="lines",
        name="5년 이동평균",
        line=dict(color="#A23B72", width=2.5, dash="dash"),
    )
)

fig.update_layout(
    title="서울 연평균기온 및 5년 이동평균",
    xaxis_title="연도",
    yaxis_title="기온 (℃)",
    hovermode="x unified",
    margin=dict(l=40, r=20, t=50, b=30),
    font=dict(family="Malgun Gothic, AppleGothic, NanumGothic, sans-serif"),
)
st.plotly_chart(fig, use_container_width=True)

# 6) 하단 안내(결측치 제외 명시) -----------------------------------
st.divider()
st.info(
    "데이터 처리 안내: 1950 ~ 1953년 기간의 결측치는 연평균기온 및 "
    "선택 구간 평균·최고·최저 기온 산출에서 제외했습니다. "
    "제외 사실은 본 화면 하단에 명시되어 있습니다."
)
