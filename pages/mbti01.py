import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# --- 페이지 설정 ---
st.set_page_config(
    page_title="Global MBTI Analyzer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 스타일 설정 (한글 폰트 깨짐 방지 - 영문 위주 표기 권장) ---
# 스트림릿 클라우드(Linux) 환경에서는 한글 폰트가 없을 수 있어
# 차트 내 라벨은 가급적 영문(데이터의 Country명 등)을 사용하는 것이 안전합니다.
plt.rcParams['font.family'] = 'sans-serif'

# --- 타이틀 ---
st.title("🌏 국가별 MBTI 성향 분석 및 비교")
st.markdown("데이터 파일(`mbti_data.csv`)을 기반으로 국가별 성향과 순위를 분석합니다.")

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
    st.info("앱이 실행되는 폴더에 데이터 파일을 업로드해주세요.")
    st.stop() # 실행 중단

# --- 사이드바: 기본 데이터 확인 ---
with st.sidebar:
    st.header("📊 데이터 옵션")
    if st.checkbox("원본 데이터 보기"):
        st.dataframe(df)
    
    # 한국의 영문 표기 찾기 (데이터에 따라 Korea, South Korea, Republic of Korea 등 다를 수 있음)
    # 편의상 'Korea'가 포함된 첫 번째 국가를 한국으로 가정하거나, 사용자가 선택하게 함
    country_list = df['Country'].unique().tolist()
    default_korea = next((c for c in country_list if "Korea" in c), None)
    
    korea_name = st.selectbox(
        "한국 데이터명 선택 (비교용)", 
        country_list, 
        index=country_list.index(default_korea) if default_korea else 0
    )

# --- 탭 구성 ---
tab1, tab2 = st.tabs(["🏳️ 국가별 상세 분석", "🏆 유형별 TOP 10 & 한국 비교"])

# === Tab 1: 국가별 상세 분석 ===
with tab1:
    st.subheader("국가별 MBTI 분포 확인")
    
    selected_country = st.selectbox("분석할 국가를 선택하세요", country_list)
    
    # 선택된 국가 데이터 필터링
    country_data = df[df['Country'] == selected_country].iloc[0]
    
    # MBTI 컬럼만 추출 (Country 제외)
    mbti_cols = [col for col in df.columns if col != 'Country']
    values = country_data[mbti_cols].values
    
    # 차트 그리기
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(mbti_cols, values, color='skyblue')
    
    # 수치 표시
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.1f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')
    
    ax.set_title(f"MBTI Distribution: {selected_country}")
    ax.set_ylabel("Percentage / Score")
    st.pyplot(fig)


# === Tab 2: 유형별 TOP 10 & 한국 비교 ===
with tab2:
    st.subheader("MBTI 유형별 상위 국가 & 한국 위치")
    
    target_mbti = st.selectbox("순위를 확인하고 싶은 MBTI 유형", mbti_cols)
    
    # 해당 MBTI 기준으로 내림차순 정렬
    sorted_df = df[['Country', target_mbti]].sort_values(by=target_mbti, ascending=False)
    
    # Top 10 추출
    top_10 = sorted_df.head(10)
    
    # 한국 데이터 가져오기
    korea_data = sorted_df[sorted_df['Country'] == korea_name]
    
    # 시각화용 데이터 병합 (Top 10에 한국이 없으면 추가해서 보여줌)
    if not korea_data.empty and korea_name not in top_10['Country'].values:
        plot_df = pd.concat([top_10, korea_data])
    else:
        plot_df = top_10
    
    # 차트 그리기
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    
    # 색상 설정 (한국은 빨간색, 나머지는 회색)
    colors = ['red' if x == korea_name else 'lightgray' for x in plot_df['Country']]
    
    # 가로 막대 그래프
    bars = ax2.barh(plot_df['Country'], plot_df[target_mbti], color=colors)
    ax2.invert_yaxis() # 순위가 높은게 위로 오도록
    
    # 수치 표시
    for bar in bars:
        width = bar.get_width()
        ax2.text(width + 0.1, 
                 bar.get_y() + bar.get_height()/2, 
                 f'{width:.1f}', 
                 va='center')

    ax2.set_title(f"Top Countries for {target_mbti} (vs {korea_name})")
    ax2.set_xlabel("Score / Percentage")
    
    st.pyplot(fig2)
    
    # 텍스트로 요약
    if not korea_data.empty:
        korea_rank = sorted_df[sorted_df['Country'] == korea_name].index[0]
        real_rank = sorted_df.index.get_loc(korea_rank) + 1
        st.success(f"🇰🇷 **{korea_name}**의 **{target_mbti}** 순위는 전체 {len(df)}개 국가 중 **{real_rank}위** 입니다.")
    else:
        st.warning("선택하신 한국 데이터명이 목록에 없습니다.")
