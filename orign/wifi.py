import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# ---------------------------------------------------------
# 1. 페이지 설정 (서울 전용으로 변경)
# ---------------------------------------------------------
st.set_page_config(layout="wide", page_title="서울시 공공와이파이 보안 지도")

# 제목 수정
st.title("🛡️ 서울특별시 공공와이파이 보안 지도")
st.markdown("""
<style>
    .stRadio > label {font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. 데이터 로드 (서울 데이터만 필터링)
# ---------------------------------------------------------
@st.cache_data
def load_data():
    # 파일 읽기
    df = pd.read_csv('무료와이파이정보.csv', encoding='utf-8') 
    
    # 컬럼 정리
    df = df.rename(columns={
        '와이파이SSID': 'SSID',
        'WGS84위도': 'lat',
        'WGS84경도': 'lon',
        '설치장소명': 'place_name',
        '설치장소상세': 'detail_address',
        '서비스제공사명': 'provider',
        '설치시도명': 'city'  # 지역 필터링용
    })
    
    # ★ 핵심 수정: 오직 '서울특별시' 데이터만 남김!
    if 'city' in df.columns:
        df = df[df['city'] == '서울특별시']
    
    # 결측치 채우기
    df['SSID'] = df['SSID'].fillna('Unknown')
    df['provider'] = df['provider'].fillna('Unknown')
    
    # 좌표 숫자 변환
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
    df = df.dropna(subset=['lat', 'lon'])
    
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"데이터 로드 오류: {e}")
    st.stop()

# ---------------------------------------------------------
# 3. 보안 분석 로직
# ---------------------------------------------------------
def get_security_info(ssid, provider):
    ssid_lower = str(ssid).lower()
    provider_lower = str(provider).lower()
    
    # Case 1: SSID가 없는 경우
    if ssid == 'Unknown' or ssid == '':
        color = 'gray'
        if any(x in provider_lower for x in ['kt', 'skt', 'lgu+', 'u+']):
            status = "정보 없음 (추정: 보통)"
            score = 2
        else:
            status = "정보 없음 (추정: 낮음)"
            score = 0
            
    # Case 2: SSID가 있는 경우
    else:
        # 안전 (SEOUL_Secure 등)
        if any(x in ssid_lower for x in ['secure', 'giga', 'te']): 
            color = 'green'
            status = "안전 (암호화)"
            score = 3
        # 주의 (개방형)
        elif any(x in ssid_lower for x in ['free', 'public', 'open', 'guest']):
            color = 'red'
            status = "주의 (개방형)"
            score = 1
        # 그 외
        else:
            color = 'orange'
            status = "일반 (확인 필요)"
            score = 2
            
    return color, status, score

# ---------------------------------------------------------
# 4. 사이드바 (검색 설정)
# ---------------------------------------------------------
with st.sidebar.form(key='search_form'):
    st.header("🔍 서울 지역 검색")
    # 서울의 대표적인 장소로 기본값 변경
    location_input = st.text_input("장소 입력 (예: 강남역, 홍대입구)", value="서울시청")
    search_radius = st.slider("검색 반경 (m)", 100, 3000, 500)
    submit_button = st.form_submit_button(label='검색 및 지도 업데이트')

# 기본 좌표 (서울시청)
location_coords = [37.5665, 126.9780]

if submit_button or location_input:
    geolocator = Nominatim(user_agent="seoul_wifi_map")
    try:
        # 서울 지역 위주로 검색되도록 수정
        loc = geolocator.geocode(f"서울 {location_input}")
        if loc:
            location_coords = [loc.latitude, loc.longitude]
        else:
            st.sidebar.warning("장소를 찾을 수 없어 서울시청으로 이동합니다.")
    except:
        pass

# ---------------------------------------------------------
# 5. 데이터 필터링 (속도 최적화)
# ---------------------------------------------------------
nearby_wifi = []
rows = zip(df['lat'], df['lon'], df['SSID'], df['provider'], df['place_name'], df['detail_address'])

for lat, lon, ssid, provider, place, detail in rows:
    wifi_loc = (lat, lon)
    distance = geodesic(location_coords, wifi_loc).meters
    
    if distance <= search_radius:
        color, status, score = get_security_info(ssid, provider)
        nearby_wifi.append({
            'lat': lat,
            'lon': lon,
            '장소명': place,
            'SSID': ssid,
            '상세주소': detail,
            '제공자': provider,
            '보안상태': status,
            '거리(m)': round(distance, 1),
            '점수': score,
            'color': color
        })

# ---------------------------------------------------------
# 6. 지도 그리기
# ---------------------------------------------------------
m = folium.Map(location=location_coords, zoom_start=15)

# 내 위치 표시
folium.Marker(
    location=location_coords,
    popup="검색 위치",
    icon=folium.Icon(color='blue', icon='user', prefix='fa')
).add_to(m)

# 반경 표시
folium.Circle(
    location=location_coords,
    radius=search_radius, color='#3186cc', fill=True, fill_opacity=0.1
).add_to(m)

# 마커 클러스터
marker_cluster = MarkerCluster().add_to(m)

for item in nearby_wifi:
    folium.Marker(
        location=[item['lat'], item['lon']],
        popup=folium.Popup(f"<b>{item['장소명']}</b><br>SSID: {item['SSID']}<br>상태: {item['보안상태']}", max_width=300),
        tooltip=f"{item['장소명']} ({item['보안상태']})",
        icon=folium.Icon(color=item['color'], icon='wifi', prefix='fa')
    ).add_to(marker_cluster)

# 지도 출력
st_folium(m, width="100%", height=500, returned_objects=[])

# ---------------------------------------------------------
# 7. 결과 테이블
# ---------------------------------------------------------
st.markdown("---")

if nearby_wifi:
    st.subheader(f"📍 검색 결과: {len(nearby_wifi)}개 발견")
    
    df_res = pd.DataFrame(nearby_wifi)
    
    col1, col2 = st.columns([1, 3])
    with col1:
        sort_option = st.radio(
            "📋 정렬 기준:",
            ("안전도 우선 (추천)", "거리 우선")
        )

    if sort_option == "안전도 우선 (추천)":
        df_res = df_res.sort_values(by=['점수', '거리(m)'], ascending=[False, True])
    else:
        df_res = df_res.sort_values(by='거리(m)', ascending=True)
    
    cols = ['장소명', '보안상태', 'SSID', '거리(m)', '상세주소', '제공자']
    
    def color_coding(val):
        if '안전' in val: 
            return 'color: green; font-weight: bold'
        elif '주의' in val: 
            return 'color: red; font-weight: bold'
        elif '일반' in val or '보통' in val:
            return 'color: orange; font-weight: bold'
        return 'color: gray'

    st.dataframe(
        df_res[cols].style.applymap(color_coding, subset=['보안상태'])
                          .format({'거리(m)': '{:.1f}m'}),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("설정된 범위 내에 서울시 공공와이파이가 없습니다.")
