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
st.title("🌏 국가별 MBTI 성향 분석")
st.markdown("데이터 파일(`mbti.csv`)을 기반으로 국가별 성향 순위와 비교 분석을 제공합니다.")

# --- 데이터 로드 함수 ---
@st.cache_data
def load_data():
    try:
        # 파일 이름: mbti.csv
        df = pd.read_csv('mbti.csv')
        return df
    except FileNotFoundError:
        return None

df = load_data()

# --- 데이터 로드 실패 시 안내 ---
if df is None:
    st.error("❌ 'mbti.csv' 파일을 찾을 수 없습니다.")
    st.info("같은 폴더에 'mbti.csv' 이름의 파일이 있는지 확인해주세요.")
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
tab1, tab2 = st.tabs(["🏳️ 국가별 순위 분석", "🏆 유형별 TOP 10 & 비교"])

# === Tab 1: 국가별 상세 순위 분석 (기능 추가됨) ===
with tab1:
    st.subheader("국가별 MBTI 성향 순위")
    selected_country = st.selectbox("분석할 국가를 선택하세요", country_list)
    
    # 데이터 전처리
    country_data = df[df['Country'] == selected_country].iloc[0]
    mbti_cols = [col for col in df.columns if col != 'Country']
    
    # 데이터프레임 생성
    chart_data = pd.DataFrame({
        'MBTI': mbti_cols,
        'Score': country_data[mbti_cols].values
    })
    
    # [핵심 변경] 점수 기준 내림차순 정렬 (높은 점수가 1위)
    chart_data = chart_data.sort_values(by='Score', ascending=False).reset_index(drop=True)
    
    # 순위 컬럼 추가 (1위부터 시작)
    chart_data.index = chart_data.index + 1
    chart_data.index.name = 'Rank'
    chart_data = chart_data.reset_index() # Rank를 컬럼으로 변환
    
    # 화면 레이아웃 분할 (왼쪽: 차트, 오른쪽: 순위표)
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"**📊 {selected_country}의 MBTI 분포 (높은 순)**")
        # Altair 차트: X축을 점수 기준으로 정렬하여 표시
        c = alt.Chart(chart_data).mark_bar().encode(
            x=alt.X('MBTI', sort='-y'), # y축 값(Score) 기준으로 내림차순 정렬
            y='Score',
            color=alt.value('#4c78a8'), 
            tooltip=['Rank', 'MBTI', 'Score']
        ).properties(
            height=500
        )
        # 막대 위에 텍스트 표시
        text = c.mark_text(dy=-10).encode(text='Score')
        st.altair_chart(c + text, use_container_width=True)
        
    with col2:
        st.markdown(f"**📋 {selected_country} 상세 순위표**")
        # 순위표 표시 (인덱스를 숨기고 깔끔하게)
        st.dataframe(
            chart_data[['Rank', 'MBTI', 'Score']],
            hide_index=True,
            use_container_width=True
        )


# === Tab 2: 유형별 TOP 10 & 한국 비교 ===
with tab2:
    st.subheader(f"MBTI 유형별 상위 국가 & {korea_name} 위치")
    
    target_mbti = st.selectbox("순위를 확인할 MBTI 유형", mbti_cols)
    
    # 데이터 정렬 및 추출
    sorted_df = df[['Country', target_mbti]].sort_values(by=target_mbti, ascending=False)
    top_10 = sorted_df.head(10)
    
    # 한국 데이터 확보
    korea_row = sorted_df[sorted_df['Country'] == korea_name]
    
    # 시각화용 데이터 합치기
    if not korea_row.empty and korea_name not in top_10['Country'].values:
        plot_df = pd.concat([top_10, korea_row])
    else:
        plot_df = top_10
        
    # 순위 표시를 위해 Rank 컬럼 추가
    sorted_df['Rank'] = range(1, len(sorted_df) + 1)
    plot_df = plot_df.merge(sorted_df[['Country', 'Rank']], on='Country')
    
    # --- Altair 차트 ---
    bars = alt.Chart(plot_df).mark_bar().encode(
        x=alt.X(target_mbti, title='Score'),
        y=alt.Y('Country', sort='-x', title='Country'),
        color=alt.condition(
            alt.datum.Country == korea_name,
            alt.value('red'),
            alt.value('lightgray')
        ),
        tooltip=['Country', target_mbti, 'Rank']
    )
    
    text = bars.mark_text(align='left', baseline='middle', dx=3).encode(text=target_mbti)
    
    final_chart = (bars + text).properties(height=500)
    st.altair_chart(final_chart, use_container_width=True)
    
    # 텍스트 요약
    if not korea_row.empty:
        real_rank = sorted_df.loc[sorted_df['Country'] == korea_name, 'Rank'].values[0]
        st.info(f"📌 **{korea_name}**의 **{target_mbti}** 지수는 **{sorted_df.loc[sorted_df['Country'] == korea_name, target_mbti].values[0]}**이며, 전체 **{real_rank}위**입니다.")
