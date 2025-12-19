import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 한글 폰트 설정 (스트림릿 클라우드 환경 고려)
plt.rcParams['axes.unicode_minus'] = False
# 스트림릿 클라우드는 리눅스 기반이므로 기본 폰트 설정이 필요할 수 있습니다.

def load_data():
    # 데이터 파일 읽기 (상단 7행은 설명이므로 건너뜀)
    df = pd.read_csv('test.csv', skiprows=7, encoding='cp949')
    
    # 컬럼명 정리 (공백 제거)
    df.columns = [col.strip() for col in df.columns]
    
    # 날짜 데이터 변환 (앞의 탭 문자 제거 및 날짜형 변환)
    df['날짜'] = df['날짜'].str.strip()
    df['날짜'] = pd.to_datetime(df['날짜'])
    
    # 연도 컬럼 생성
    df['연도'] = df['날짜'].dt.year
    return df

# 앱 타이틀
st.title("🌡️ 서울 기온 110년 변화 분석기")
st.write("1907년부터 최근까지의 데이터를 바탕으로 기온 상승 추이를 확인합니다.")

try:
    data = load_data()

    # 1. 연도별 평균 기온 계산
    annual_temp = data.groupby('연도')['평균기온(℃)'].mean().reset_index()

    # 2. 사이드바 - 분석 범위 설정
    st.sidebar.header("분석 설정")
    year_range = st.sidebar.slider(
        "분석 기간 선택",
        int(annual_temp['연도'].min()),
        int(annual_temp['연도'].max()),
        (1907, 2024)
    )

    # 필터링
    filtered_df = annual_temp[(annual_temp['연도'] >= year_range[0]) & (annual_temp['연도'] <= year_range[1])]

    # 3. 메인 화면 - 통계 요약
    col1, col2 = st.columns(2)
    with col1:
        st.metric("시작 연도 평균 기온", f"{filtered_df.iloc[0]['평균기온(℃) Marc']:.2f} ℃")
    with col2:
        st.metric("종료 연도 평균 기온", f"{filtered_df.iloc[-1]['평균기온(℃)']:.2f} ℃")

    # 4. 차트 시각화
    st.subheader(f"{year_range[0]}년 ~ {year_range[1]}년 연평균 기온 변화")
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(filtered_df['연도'], filtered_df['평균기온(℃)'], marker='o', linestyle='-', color='orangered', markersize=3)
    
    # 추세선 추가 (간단한 회귀선)
    import numpy as np
    z = np.polyfit(filtered_df['연도'], filtered_df['평균기온(℃)'], 1)
    p = np.poly1d(z)
    ax.plot(filtered_df['연도'], p(filtered_df['연도']), "b--", alpha=0.5, label="추세선")

    ax.set_xlabel("Year")
    ax.set_ylabel("Avg Temperature (℃)")
    ax.grid(True, alpha=0.3)
    
    st.pyplot(fig)

    # 5. 데이터 테이블 보기
    if st.checkbox("상세 데이터 보기"):
        st.dataframe(filtered_df)

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.info("test.csv 파일이 스크립트와 같은 폴더에 있는지 확인해주세요.")
