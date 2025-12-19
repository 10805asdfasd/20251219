import streamlit as st
import pandas as pd

# 앱 타이틀 및 설명
st.set_page_config(page_title="서울 기온 분석기", layout="wide")
st.title("🌡️ 서울 기온 110년 변화 분석기")
st.write("외부 라이브러리(matplotlib) 없이 스트림릿 내장 기능만으로 구현되었습니다.")

@st.cache_data
def load_data():
    # 데이터 파일 읽기 (상단 7행은 설명이므로 건너뜀)
    df = pd.read_csv('test.csv', skiprows=7, encoding='cp949')
    
    # 컬럼명 정리 (공백 제거)
    df.columns = [col.strip() for col in df.columns]
    
    # 날짜 데이터 변환 (앞의 탭 문자 제거 및 날짜형 변환)
    df['날짜'] = df['날짜'].str.strip()
    df['날짜'] = pd.to_datetime(df['날짜'])
    
    # 연도 컬럼 생성 및 결측치 제거
    df['연도'] = df['날짜'].dt.year
    df = df.dropna(subset=['평균기온(℃)'])
    return df

try:
    data = load_data()

    # 1. 연도별 평균 기온 계산
    annual_temp = data.groupby('연도')['평균기온(℃)'].mean().reset_index()
    annual_temp.set_index('연도', inplace=True) # 차트 축 설정을 위해 인덱스 지정

    # 2. 사이드바 - 분석 범위 설정
    st.sidebar.header("분석 설정")
    min_year = int(annual_temp.index.min())
    max_year = int(annual_temp.index.max())
    
    year_range = st.sidebar.slider(
        "분석 기간 선택",
        min_year,
        max_year,
        (min_year, max_year)
    )

    # 데이터 필터링
    filtered_df = annual_temp.loc[year_range[0]:year_range[1]]

    # 3. 주요 지표 계산
    col1, col2, col3 = st.columns(3)
    start_temp = filtered_df.iloc[0]['평균기온(℃)']
    end_temp = filtered_df.iloc[-1]['평균기온(℃)']
    diff = end_temp - start_temp

    col1.metric("시작 연도 평균", f"{start_temp:.2f} ℃")
    col2.metric("종료 연도 평균", f"{end_temp:.2f} ℃")
    col3.metric("기온 변화량", f"{diff:+.2f} ℃", delta_color="inverse")

    # 4. 스트림릿 내장 라인 차트 (matplotlib 불필요)
    st.subheader(f"📈 {year_range[0]}년 ~ {year_range[1]}년 평균 기온 추이")
    st.line_chart(filtered_df['평균기온(℃)'])

    # 5. 인사이트 요약
    st.info(f"분석 결과: {year_range[0]}년부터 {year_range[1]}년 사이 평균 기온은 약 {abs(diff):.2f}도 {'상승' if diff > 0 else '하락'}했습니다.")

    # 6. 데이터 테이블
    with st.expander("상세 데이터 보기"):
        st.write(filtered_df)

except Exception as e:
    st.error(f"오류 발생: {e}")
    st.info("파일 이름이 'test.csv'이며 스크립트와 동일한 경로에 있는지 확인해 주세요.")
