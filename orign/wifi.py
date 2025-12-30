import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, FastMarkerCluster
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# ---------------------------------------------------------
# 1. 페이지 설정
# ---------------------------------------------------------
st.set_page_config(layout="wide", page_title="경기도 안전 와이파이 지도")

st.title("🛡️ 경기도 공공와이파이 보안 지도")

# ---------------------------------------------------------
# 2. 데이터 로드 (캐싱 최적화)
# ---------------------------------------------------------
@st.cache_data
def load_data():
    # encoding은 상황에 따라 'cp949' 또는 'utf-8'
    df = pd.read_csv('무료와이파이정보.csv', encoding='utf-8') 
    
    df = df.rename(columns={
        '와이파이SSID': 'SSID',
        'WGS84위도': 'lat',
        'WGS84경도': 'lon',
        '설치장소명': 'place_name',
        '설치장소상세': 'detail_address',
        '서비스제공사명': 'provider'
    })
    
    df['SSID'] = df['SSID'].fillna('Unknown')
    df['provider'] = df['provider'].fillna('Unknown')
    
    # 좌표 변환 및 결측치 제거
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
# 3. 보안 분석 함수
# ---------------------------------------------------------
def get_security_info(ssid, provider):
    ssid_lower = str(ssid).lower()
    provider_lower = str(provider).lower()
    
    if ssid == 'Unknown' or ssid == '':
        color = 'gray'
        if any(x in provider_lower for x in ['kt', 'skt', 'lgu+', 'u+']):
            status = "정보 없음 (추정: 보통)"
            score = 2
        else:
            status = "정보 없음 (추정: 낮음)"
            score = 0
    else:
        if any(x in ssid_lower for x in ['secure', 'giga', 'te']): 
            color = 'green'
            status = "안전 (암호화)"
            score = 3
        elif any(x in ssid_lower for x in ['free', 'public', 'open', 'guest']):
            color = 'red'
            status = "주의 (개방형)"
            score = 1
        else:
            color = 'orange'
            status = "일반 (확인 필요)"
            score = 2
    return color, status, score

# ---------------------------------------------------------
# 4. 사이드바 (Form 사용으로 깜빡임 방지)
# ---------------------------------------------------------
with st.sidebar.form(key='search_form'):
    st.header("🔍 검색 설정")
    location_input = st.text_input("장소 입력 (예: 수원역)", value="수원역")
    search_radius = st.slider("검색 반경 (m)", 100, 3000, 500)
    
    # 이 버튼을 눌러야만 지도가 갱신됩니다! (속도 향상 핵심)
    submit_button = st.form_submit_button(label='검색 및 지도 업데이트')

# 초기 좌표 (경기도청)
location_coords = [37.289, 127.053]

if submit_button or location_input:
    geolocator = Nominatim(user_agent="gyeonggi_wifi_fast")
    try:
        loc = geolocator.geocode(f"경기도 {location_input}")
        if loc:
            location_coords = [loc.latitude, loc.longitude]
        else:
            st.sidebar.warning("장소를 못 찾아서 기본 위치로 이동합니다.")
    except:
        pass

# ---------------------------------------------------------
# 5. 지도 데이터 필터링 (속도 개선된 로직)
# ---------------------------------------------------------
# iterrows() 대신 리스트 컴프리헨션 사용 (속도 10배 향상)
nearby_wifi = []

# 계산을 위해 필요한 데이터만 numpy나 list로 변환하여 순회
rows = zip(df['lat'], df['lon'], df['SSID'], df['provider'], df['place_name'], df['detail_address'])

for lat, lon, ssid, provider, place, detail in rows:
    wifi_loc = (lat, lon)
    # 거리 계산
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

# 현재 위치 표시
folium.Marker(
    location=location_coords,
    popup="검색 위치",
    icon=folium.Icon(color='blue', icon='user', prefix='fa')
).add_to(m)

folium.Circle(
    location=location_coords,
    radius=search_radius, color='#3186cc', fill=True, fill_opacity=0.1
).add_to(m)

# 마커 클러스터 추가
marker_cluster = MarkerCluster().add_to(m)

# 필터링된 데이터만 마커 생성
for item in nearby_wifi:
    folium.Marker(
        location=[item['lat'], item['lon']],
        popup=folium.Popup(f"<b>{item['장소명']}</b><br>{item['SSID']}<br>{item['보안상태']}", max_width=300),
        icon=folium.Icon(color=item['color'], icon='wifi', prefix='fa')
    ).add_to(marker_cluster)

# ★★★ 핵심 최적화: returned_objects=[] ★★★
# 지도를 움직여도 데이터를 다시 받아오지 않게 설정하여 렉을 줄임
st_folium(m, width="100%", height=500, returned_objects=[])

# ---------------------------------------------------------
# 7. 결과 테이블 (정렬 기능 추가됨)
# ---------------------------------------------------------
st.markdown("---")

if nearby_wifi:
    st.subheader(f"📍 검색 결과: {len(nearby_wifi)}개 발견")
    
    # 리스트를 데이터프레임으로 변환
    df_res = pd.DataFrame(nearby_wifi)
    
    # [정렬 UI] 라디오 버튼으로 정렬 기준 선택
    col1, col2 = st.columns([1, 3]) # 디자인을 위해 컬럼 분할
    with col1:
        sort_option = st.radio(
            "📋 정렬 기준 선택:",
            ("안전도 우선 (추천)", "거리 우선"),
            help="안전도 우선: 보안 점수가 높은 순서대로 정렬합니다.\n거리 우선: 현재 위치에서 가까운 순서대로 정렬합니다."
        )

    # [정렬 로직]
    if sort_option == "안전도 우선 (추천)":
        # 1순위: 점수(높은게 위로), 2순위: 거리(가까운게 위로)
        df_res = df_res.sort_values(by=['점수', '거리(m)'], ascending=[False, True])
    else:
        # 거리(가까운게 위로)
        df_res = df_res.sort_values(by='거리(m)', ascending=True)
    
    # 보여줄 컬럼 정의
    cols = ['장소명', '보안상태', 'SSID', '거리(m)', '상세주소', '제공자']
    
    # [스타일링] 보안 상태에 따라 글자색 변경
    def color_coding(val):
        if '안전' in val: 
            return 'color: green; font-weight: bold'
        elif '주의' in val: 
            return 'color: red; font-weight: bold'
        elif '보통' in val:
            return 'color: orange; font-weight: bold'
        return 'color: gray' # 정보 없음 등

    # 테이블 출력 (use_container_width=True로 가로 꽉 차게)
    st.dataframe(
        df_res[cols].style.applymap(color_coding, subset=['보안상태'])
                          .format({'거리(m)': '{:.1f}m'}), # 거리 소수점 예쁘게 표시
        use_container_width=True,
        hide_index=True # 0, 1, 2... 인덱스 번호 숨기기 (깔끔함)
    )

else:
    # 검색 결과가 없을 때
    st.info("설정된 범위 내에 와이파이가 없습니다. 검색 반경을 넓히거나 다른 장소를 입력해보세요.")
