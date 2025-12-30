import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# ---------------------------------------------------------
# 1. 페이지 설정 및 제목
# ---------------------------------------------------------
st.set_page_config(layout="wide", page_title="경기도 안전 와이파이 지도")

st.title("🛡️ 경기도 공공와이파이 보안 지도")
st.markdown("""
이 대시보드는 **SSID 및 망 제공자 정보**를 분석하여 와이파이의 보안성을 시각화합니다.
- 🟢 **초록색**: 암호화된 안전한 와이파이 (Secure)
- 🟡 **노란색**: 통신사 제공 상용망 (보통)
- 🔴 **빨간색**: 개방형/공용 와이파이 (주의 필요)
- ⚪ **회색**: SSID 정보 없음 (제공자 정보를 통해 추정)
""")

# ---------------------------------------------------------
# 2. 데이터 로드 및 전처리 (캐싱 적용)
# ---------------------------------------------------------
@st.cache_data
def load_data():
    # 파일명은 사용자가 업로드한 파일명과 일치해야 합니다.
    df = pd.read_csv('12_04_07_E_무료와이파이정보.csv', encoding='cp949') # 혹은 utf-8
    
    # 필요한 컬럼만 선택 및 이름 정리 (업로드한 파일 기준)
    # 실제 컬럼명: 설치장소명, 설치장소상세, 설치시군구명, 서비스제공사명, 와이파이SSID, WGS84위도, WGS84경도
    df = df.rename(columns={
        '와이파이SSID': 'SSID',
        'WGS84위도': 'lat',
        'WGS84경도': 'lon',
        '설치장소명': 'place_name',
        '설치장소상세': 'detail_address',
        '서비스제공사명': 'provider'
    })
    
    # 결측치 처리
    df['SSID'] = df['SSID'].fillna('Unknown')
    df['provider'] = df['provider'].fillna('Unknown')
    
    # 좌표 데이터 숫자 변환 (오류 발생 시 NaN 처리 후 제거)
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
    df = df.dropna(subset=['lat', 'lon'])
    
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("데이터 파일(12_04_07_E_무료와이파이정보.csv)이 없습니다. 같은 폴더에 파일을 넣어주세요.")
    st.stop()

# ---------------------------------------------------------
# 3. 보안성 평가 로직 (Core Logic)
# ---------------------------------------------------------
def analyze_security(row):
    ssid = str(row['SSID']).lower()
    provider = str(row['provider']).lower()
    
    # [Case 1] SSID가 없는 경우 (회색) -> 추정 로직
    if row['SSID'] == 'Unknown' or row['SSID'] == '':
        color = 'gray'
        # 메이저 통신사면 관리가 될 확률이 높다고 가정 (추정: 비교적 높음)
        if any(x in provider for x in ['kt', 'skt', 'lgu+', 'u+']):
            status = "정보 없음 (추정: 보통)"
            level = 2 # 정렬용 점수
        else:
            status = "정보 없음 (추정: 낮음)"
            level = 0
    
    # [Case 2] SSID가 있는 경우
    else:
        # 안전 (Secure 키워드 등)
        if any(x in ssid for x in ['secure', 'giga', 'te']): 
            color = 'green'
            status = "안전 (암호화)"
            level = 3
        # 위험 (Free, Public, Open, Guest)
        elif any(x in ssid for x in ['free', 'public', 'open', 'guest']):
            color = 'red'
            status = "주의 (개방형)"
            level = 1
        # 그 외 (통신사 이름만 있거나 애매한 경우 -> 노란색)
        else:
            color = 'orange' # 노란색 계열
            status = "일반 (확인 필요)"
            level = 2
            
    return pd.Series([color, status, level])

# 데이터프레임에 보안 분석 결과 적용
df[['color', 'security_status', 'security_score']] = df.apply(analyze_security, axis=1)

# ---------------------------------------------------------
# 4. 사이드바: 위치 검색 및 필터 설정
# ---------------------------------------------------------
st.sidebar.header("🔍 검색 설정")

location_input = st.sidebar.text_input("현재 위치 또는 검색할 장소 입력", value="수원역")
search_radius = st.sidebar.slider("검색 반경 (m)", 100, 3000, 500)

# 지오코딩 (주소 -> 좌표 변환)
geolocator = Nominatim(user_agent="gyeonggi_wifi_security_map")
location_coords = None

if location_input:
    try:
        # 경기도 지역 위주로 검색되도록 문자열 보정
        loc = geolocator.geocode(f"경기도 {location_input}")
        if loc:
            location_coords = (loc.latitude, loc.longitude)
            st.sidebar.success(f"위치 확인: {loc.address}")
        else:
            st.sidebar.warning("장소를 찾을 수 없습니다. 경기도청을 중심으로 표시합니다.")
            location_coords = (37.289, 127.053) # 기본값: 경기도청
    except:
        st.sidebar.error("위치 검색 서비스 오류. 잠시 후 다시 시도해주세요.")
        location_coords = (37.289, 127.053)

# ---------------------------------------------------------
# 5. 지도 생성 및 마커 표시
# ---------------------------------------------------------
m = folium.Map(location=location_coords, zoom_start=15)

# 마커 클러스터 (너무 많은 마커가 겹치는 것 방지)
marker_cluster = MarkerCluster().add_to(m)

# 검색 반경 내 데이터 필터링을 위한 리스트
nearby_wifi = []

for idx, row in df.iterrows():
    wifi_loc = (row['lat'], row['lon'])
    
    # 거리 계산 (m 단위)
    distance = geodesic(location_coords, wifi_loc).meters
    
    # 반경 내에 있으면 리스트에 추가
    if distance <= search_radius:
        nearby_wifi.append({
            '장소명': row['place_name'],
            '상세주소': row['detail_address'],
            'SSID': row['SSID'],
            '보안상태': row['security_status'],
            '거리(m)': round(distance, 1),
            '제공자': row['provider'],
            '점수': row['security_score']
        })
        
        # 지도에 마커 추가 (반경 내 와이파이만 표시하여 지도 성능 최적화)
        # 아이콘 색상 매핑 (Folium 색상 제한으로 orange 사용)
        icon_color = row['color']
        
        folium.Marker(
            location=wifi_loc,
            popup=folium.Popup(f"""
            <b>{row['place_name']}</b><br>
            SSID: {row['SSID']}<br>
            상태: {row['security_status']}<br>
            제공: {row['provider']}
            """, max_width=300),
            tooltip=f"{row['place_name']} ({row['security_status']})",
            icon=folium.Icon(color=icon_color, icon='wifi', prefix='fa')
        ).add_to(marker_cluster)

# 현재 위치 표시 (파란색 사람 아이콘)
folium.Marker(
    location=location_coords,
    popup="현재 설정된 위치",
    icon=folium.Icon(color='blue', icon='user', prefix='fa')
).add_to(m)

# 반경 원 표시
folium.Circle(
    location=location_coords,
    radius=search_radius,
    color='#3186cc',
    fill=True,
    fill_opacity=0.1
).add_to(m)

# 지도 출력
st_folium(m, width="100%", height=500)

# ---------------------------------------------------------
# 6. 하단 데이터 테이블 (분석 결과)
# ---------------------------------------------------------
st.markdown("---")
st.subheader(f"📍 '{location_input}' 반경 {search_radius}m 내 와이파이 ({len(nearby_wifi)}곳)")

if nearby_wifi:
    # 데이터프레임 변환
    result_df = pd.DataFrame(nearby_wifi)
    
    # 정렬 옵션
    sort_option = st.radio("정렬 기준:", ("안전한 순서 (보안 점수)", "가까운 순서 (거리)"), horizontal=True)
    
    if sort_option == "안전한 순서 (보안 점수)":
        # 점수 내림차순, 그 다음 거리 오름차순
        result_df = result_df.sort_values(by=['점수', '거리(m)'], ascending=[False, True])
    else:
        result_df = result_df.sort_values(by='거리(m)')
    
    # 사용자에게 보여줄 컬럼 선택
    display_cols = ['장소명', '보안상태', 'SSID', '거리(m)', '상세주소', '제공자']
    
    # 스타일링 (보안상태에 따라 색상 입히기)
    def highlight_security(val):
        color = 'black'
        if '안전' in val: color = 'green'
        elif '주의' in val: color = 'red'
        elif '추정: 낮음' in val: color = 'gray'
        elif '일반' in val: color = '#B8860B' # DarkGoldenRod
        return f'color: {color}; font-weight: bold;'

    st.dataframe(
        result_df[display_cols].style.applymap(highlight_security, subset=['보안상태']),
        use_container_width=True
    )
else:
    st.info("설정된 반경 내에 공공와이파이 정보가 없습니다. 범위를 넓히거나 다른 장소를 검색해보세요.")
