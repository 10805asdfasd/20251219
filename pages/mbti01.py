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
st.markdown("데이터 파일(`mbti.csv`)을 기반으로 국가별 성향, 순위, 그리고 최다 유형 분류를 제공합니다.")

# --- 데이터 로드 함수 ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('mbti.csv')
        return df
    except FileNotFoundError:
        return None

df = load_data()

# --- 국가명 한글 매핑 (최종 업데이트) ---
country_map = {
    # 주요 국가 및 아시아/유럽/북미 등
    "South Korea": "대한민국", "Korea, South": "대한민국", "Korea": "대한민국",
    "United States": "미국", "USA": "미국",
    "Japan": "일본", "China": "중국", "Russia": "러시아",
    "United Kingdom": "영국", "UK": "영국", "Germany": "독일",
    "France": "프랑스", "Italy": "이탈리아", "Spain": "스페인",
    "Canada": "캐나다", "Australia": "호주", "Brazil": "브라질",
    "India": "인도", "Mexico": "멕시코", "Indonesia": "인도네시아",
    "Turkey": "터키", "Saudi Arabia": "사우디아라비아", "Switzerland": "스위스",
    "Sweden": "스웨덴", "Norway": "노르웨이", "Finland": "핀란드",
    "Denmark": "덴마크", "Netherlands": "네덜란드", "Belgium": "벨기에",
    "Poland": "폴란드", "Ukraine": "우크라이나", "Vietnam": "베트남",
    "Thailand": "태국", "Philippines": "필리핀", "Malaysia": "말레이시아",
    "Singapore": "싱가포르", "Taiwan": "대만", "Argentina": "아르헨티나",
    "Chile": "칠레", "Colombia": "콜롬비아", "Peru": "페루",
    "Egypt": "이집트", "South Africa": "남아공", "Israel": "이스라엘",
    "Iran": "이란", "Iraq": "이라크", "New Zealand": "뉴질랜드",
    "Portugal": "포르투갈", "Greece": "그리스", "Austria": "오스트리아",
    "Ireland": "아일랜드", "Hungary": "헝가리", "Czech Republic": "체코",
    
    # 기타 국가들 (알파벳 순 정렬)
    "Afghanistan": "아프가니스탄", "Albania": "알바니아", "Algeria": "알제리", 
    "Andorra": "안도라", "Angola": "앙골라", "Antigua and Barbuda": "앤티가 바부다", 
    "Armenia": "아르메니아", "Azerbaijan": "아제르바이잔", "Bahamas": "바하마", 
    "Bahrain": "바레인", "Bangladesh": "방글라데시", "Barbados": "바베이도스", 
    "Belarus": "벨라루스", "Belize": "벨리즈", "Bhutan": "부탄", 
    "Bosnia and Herzegovina": "보스니아 헤르체고비나", "Botswana": "보츠와나", 
    "Brunei": "브루나이", "Bulgaria": "불가리아", "Burkina Faso": "부르키나파소",
    "Cambodia": "캄보디아", "Cameroon": "카메룬", "Congo": "콩고 공화국", 
    "Congo (Kinshasa)": "콩고 민주 공화국", "Costa Rica": "코스타리카", 
    "Croatia": "크로아티아", "Cuba": "쿠바", "Cyprus": "키프로스", 
    "Djibouti": "지부티", "Dominica": "도미니카 연방", 
    "Dominican Republic": "도미니카 공화국", "Ecuador": "에콰도르", 
    "El Salvador": "엘살바도르", "Estonia": "에스토니아", "Ethiopia": "에티오피아",
    "Faroe Islands": "페로 제도", "Fiji": "피지", "Georgia": "조지아", 
    "Ghana": "가나", "Grenada": "그레나다", "Guatemala": "과테말라", 
    "Guinea": "기니", "Guyana": "가이아나", "Haiti": "아이티", 
    "Honduras": "온두라스", "Iceland": "아이슬란드", "Jamaica": "자메이카", 
    "Jordan": "요르단", "Kazakhstan": "카자흐스탄", "Kenya": "케냐", 
    "Kuwait": "쿠웨이트", "Kyrgyzstan": "키르기스스탄", "Laos": "라오스", 
    "Latvia": "라트비아", "Lebanon": "레바논", "Lesotho": "레소토", 
    "Libya": "리비아", "Lithuania": "리투아니아", "Luxembourg": "룩셈부르크",
    "Macedonia": "마케도니아", "Madagascar": "마다가스카르", "Malawi": "말라위", 
    "Maldives": "몰디브", "Mali": "말리", "Malta": "몰타", 
    "Mauritius": "모리셔스", "Moldova": "몰도바", "Monaco": "모나코", 
    "Mongolia": "몽골", "Montenegro": "몬테네그로", "Morocco": "모로코", 
    "Mozambique": "모잠비크", "Myanmar": "미얀마", "Namibia": "나미비아", 
    "Nepal": "네팔", "Nicaragua": "니카라과", "Niger": "니제르", 
    "Nigeria": "나이지리아", "Oman": "오만", "Pakistan": "파키스탄", 
    "Panama": "파나마", "Papua New Guinea": "파푸아뉴기니", "Paraguay": "파라과이", 
    "Qatar": "카타르", "Romania": "루마니아", "Rwanda": "르완다",
    "Saint Kitts and Nevis": "세인트키츠 네비스", "Saint Lucia": "세인트루시아",
    "Saint Vincent and the Grenadines": "세인트빈센트 그레나딘",
    "Senegal": "세네갈", "Serbia": "세르비아", "Seychelles": "세이셸", 
    "Slovakia": "슬로바키아", "Slovenia": "슬로베니아", "Somalia": "소말리아",
    "Sri Lanka": "스리랑카", "Sudan": "수단", "Suriname": "수리남", 
    "Syria": "시리아", "Tajikistan": "타지키스탄", "Tanzania": "탄자니아", 
    "Trinidad and Tobago": "트리니다드 토바고", "Tunisia": "튀니지", 
    "Uganda": "우간다", "United Arab Emirates": "아랍에미리트", 
    "Uruguay": "우루과이", "Uzbekistan": "우즈베키스탄", "Vanuatu": "바누아투", 
    "Yemen": "예멘", "Zambia": "잠비아", "Zimbabwe": "짐바브웨"
}

def translate_country(name):
    return country_map.get(name, name) # 매핑에 없으면 원래 이름 반환

# --- 데이터 로드 실패 시 안내 ---
if df is None:
    st.error("❌ 'mbti.csv' 파일을 찾을 수 없습니다.")
    st.info("같은 폴더에 'mbti.csv' 이름의 파일이 있는지 확인해주세요.")
    st.stop()

# --- 사이드바: 옵션 설정 ---
with st.sidebar:
    st.header("⚙️ 설정")
    
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
tab1, tab2, tab3 = st.tabs(["🏳️ 국가별 순위 분석", "🏆 유형별 TOP 10 & 비교", "🗺️ 국가별 최다 MBTI 분류"])

mbti_cols = [col for col in df.columns if col != 'Country']

# === Tab 1: 국가별 상세 순위 분석 ===
with tab1:
    st.subheader("국가별 MBTI 성향 순위")
    selected_country = st.selectbox("분석할 국가를 선택하세요", country_list)
    
    country_data = df[df['Country'] == selected_country].iloc[0]
    
    chart_data = pd.DataFrame({
        'MBTI': mbti_cols,
        'Score': country_data[mbti_cols].values
    })
    
    chart_data = chart_data.sort_values(by='Score', ascending=False).reset_index(drop=True)
    chart_data.index = chart_data.index + 1
    chart_data.index.name = 'Rank'
    chart_data = chart_data.reset_index()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"**📊 {selected_country}의 MBTI 분포 (높은 순)**")
        c = alt.Chart(chart_data).mark_bar().encode(
            x=alt.X('MBTI', sort='-y'),
            y='Score',
            color=alt.value('#4c78a8'), 
            tooltip=['Rank', 'MBTI', 'Score']
        ).properties(height=500)
        text = c.mark_text(dy=-10).encode(text='Score')
        st.altair_chart(c + text, use_container_width=True)
        
    with col2:
        st.markdown(f"**📋 {selected_country} 상세 순위표**")
        st.dataframe(
            chart_data[['Rank', 'MBTI', 'Score']],
            hide_index=True,
            use_container_width=True
        )

# === Tab 2: 유형별 TOP 10 & 한국 비교 ===
with tab2:
    st.subheader(f"MBTI 유형별 상위 국가 & {korea_name} 위치")
    target_mbti = st.selectbox("순위를 확인할 MBTI 유형", mbti_cols)
    
    sorted_df = df[['Country', target_mbti]].sort_values(by=target_mbti, ascending=False)
    top_10 = sorted_df.head(10)
    korea_row = sorted_df[sorted_df['Country'] == korea_name]
    
    if not korea_row.empty and korea_name not in top_10['Country'].values:
        plot_df = pd.concat([top_10, korea_row])
    else:
        plot_df = top_10
        
    sorted_df['Rank'] = range(1, len(sorted_df) + 1)
    plot_df = plot_df.merge(sorted_df[['Country', 'Rank']], on='Country')
    
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
    st.altair_chart((bars + text).properties(height=500), use_container_width=True)
    
    if not korea_row.empty:
        real_rank = sorted_df.loc[sorted_df['Country'] == korea_name, 'Rank'].values[0]
        st.info(f"📌 **{korea_name}**의 **{target_mbti}** 지수는 **{sorted_df.loc[sorted_df['Country'] == korea_name, target_mbti].values[0]}**이며, 전체 **{real_rank}위**입니다.")

# === Tab 3: 국가별 최다 MBTI 분류 (신규 기능) ===
with tab3:
    st.subheader("🗺️ 국가별 대표(최다) MBTI 유형 분류")
    st.markdown("각 국가별로 점수가 가장 높은 MBTI 유형을 찾아 분류했습니다.")
    
    # 1. 각 행(국가)별로 최대 값을 가진 컬럼(MBTI) 찾기
    # idxmax(axis=1)은 각 행에서 최대값을 가진 열의 이름을 반환합니다.
    df_class = df.copy()
    df_class['Dominant_MBTI'] = df_class[mbti_cols].idxmax(axis=1)
    
    # 2. 국가명 한글 번역 적용
    df_class['Country_KR'] = df_class['Country'].apply(translate_country)
    
    # 3. MBTI별로 그룹화하여 국가 리스트 만들기
    # reset_index를 통해 데이터프레임 형태로 변환
    grouped_df = df_class.groupby('Dominant_MBTI')['Country_KR'].apply(list).reset_index()
    
    # 4. 리스트를 보기 좋게 문자열로 변환 (예: "한국, 미국, 일본")
    grouped_df['Countries'] = grouped_df['Country_KR'].apply(lambda x: ', '.join(x))
    grouped_df['Count'] = grouped_df['Country_KR'].apply(len) # 해당 유형인 국가 수
    
    # 5. 국가 수가 많은 MBTI 순서대로 정렬
    grouped_df = grouped_df.sort_values(by='Count', ascending=False)
    
    # 6. 최종 표시용 데이터프레임
    display_df = grouped_df[['Dominant_MBTI', 'Count', 'Countries']]
    display_df.columns = ['최다 MBTI 유형', '국가 수', '해당 국가 목록']
    
# 7. 스타일링하여 표 출력
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "최다 MBTI 유형": st.column_config.TextColumn("대표 MBTI", width="small"),
            "국가 수": st.column_config.NumberColumn("국가 수", width="small"),
            "해당 국가 목록": st.column_config.TextColumn("국가 목록 (한글)", width="large"),
        }
    )
