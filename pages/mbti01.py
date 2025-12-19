import streamlit as st
import pandas as pd
import altair as alt

# --- 페이지 설정 ---
st.set_page_config(
    page_title="Global MBTI Analyzer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 타이틀 ---
st.title("🌏 국가별 MBTI 성향 분석 (Interactive)")
st.markdown("Matplotlib 없이 스트림릿 내장 차트 기능을 활용하여 분석합니다.")

# --- 데이터 로드 함수 ---
@st.cache_data
def load_data():
    try:
        # 같은 폴더에 있는 파일 읽기
        df = pd.read_csv('mbti_data.csv')
        return df
    except FileNotFoundError:
        return None

df = load_data()

# --- 데이터 로드 실패 시 안내 ---
if df is None:
    st.error("❌ 'mbti_data.csv' 파일을 찾을 수 없습니다.")
    st.info("같은 폴더에 데이터 파일이 있는지 확인해주세요.")
    st.stop()

# --- 사이드바: 옵션 설정 ---
with st.sidebar:
    st.header("⚙️ 설정")
    
    # 한국의 영문 표기 찾기 (자동 감지 시도)
    country_list = df['Country'].unique().tolist()
    default_korea = next((c for c in country_list if "Korea" in c), country_list[0])
    
    korea_name = st.selectbox(
        "한국(비교 대상) 국가명 선택", 
        country_list, 
        index=country_list.index(default_korea)
    )
    
    if st.checkbox("전체 데이터 표 보이기"):
        st.dataframe(df)

# --- 탭 구성 ---
tab1, tab2 = st.tabs(["🏳️ 국가별 상세 분석", "🏆 유형별 TOP 10 & 비교"])

# === Tab 1: 국가별 상세 분석 ===
with tab1:
    st.subheader("국가별 MBTI 분포")
    selected_country = st.selectbox("분석할 국가를 선택하세요", country_list)
    
    # 데이터 전처리: 선택된 국가의 데이터를 'MBTI 유형'과 '수치'로 변환
    country_data = df[df['Country'] == selected_country].iloc[0]
    mbti_cols = [col for col in df.columns if col != 'Country']
    
    # 차트용 데이터프레임 생성
    chart_data = pd.DataFrame({
        'MBTI': mbti_cols,
        'Score': country_data[mbti_cols].values
    })
    
    # Altair를 이용한 막대 차트 (마우스 오버 시 수치 표시)
    c = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X('MBTI', sort=None),
        y='Score',
        color=alt.value('#4c78a8'), # 파란색 계열
        tooltip=['MBTI', 'Score']   # 마우스 오버 시 정보 표시
    ).properties(
        height=400
    )
    
    st.altair_chart(c, use_container_width=True)


# === Tab 2: 유형별 TOP 10 & 한국 비교 ===
with tab2:
    st.subheader(f"MBTI 유형별 상위 국가 & {korea_name} 위치")
    
    target_mbti = st.selectbox("순위를 확인할 MBTI 유형", mbti_cols)
    
    # 데이터 정렬 및 추출
    sorted_df = df[['Country', target_mbti]].sort_values(by=target_mbti, ascending=False)
    top_10 = sorted_df.head(10)
    
    # 한국 데이터 확보
    korea_row = sorted_df[sorted_df['Country'] == korea_name]
    
    # 시각화용 데이터 합치기 (한국이 Top 10에 없으면 추가)
    if not korea_row.empty and korea_name not in top_10['Country'].values:
        plot_df = pd.concat([top_10, korea_row])
    else:
        plot_df = top_10
        
    # 순위 표시를 위해 Rank 컬럼 추가 (전체 데이터 기준)
    sorted_df['Rank'] = range(1, len(sorted_df) + 1)
    plot_df = plot_df.merge(sorted_df[['Country', 'Rank']], on='Country')
    
    # --- Altair 차트 생성 (Highlighting) ---
    # 기본 막대
    bars = alt.Chart(plot_df).mark_bar().encode(
        x=alt.X(target_mbti, title='Score'),
        y=alt.Y('Country', sort='-x', title='Country'), # 점수 높은 순 정렬
        # 한국이면 빨간색, 아니면 회색으로 색상 지정
        color=alt.condition(
            alt.datum.Country == korea_name,
            alt.value('red'),
            alt.value('lightgray')
        ),
        tooltip=['Country', target_mbti, 'Rank']
    )
    
    # 막대 끝에 수치 텍스트 표시
    text = bars.mark_text(
        align='left',
        baseline='middle',
        dx=3  # 막대에서 3픽셀 떨어뜨림
    ).encode(
        text=target_mbti
    )
    
    # 차트 결합 및 표시
    final_chart = (bars + text).properties(height=500)
    st.altair_chart(final_chart, use_container_width=True)
    
    # 텍스트 요약
    if not korea_row.empty:
        real_rank = sorted_df.loc[sorted_df['Country'] == korea_name, 'Rank'].values[0]
        st.info(f"📌 **{korea_name}**의 **{target_mbti}** 지수는 **{sorted_df.loc[sorted_df['Country'] == korea_name, target_mbti].values[0]}**이며, 전체 **{real_rank}위**입니다.")
