import streamlit as st
import csv
from datetime import datetime
import statistics

# 제목
st.title("지난 110년간 기온 변화 분석 웹앱")

# 데이터 불러오기
years = []
temps = []

with open("test.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)  # 헤더 건너뛰기
    for row in reader:
        try:
            year = int(row[0])
            temp = float(row[1])
            years.append(year)
            temps.append(temp)
        except:
            continue

# 데이터프레임 형태로 변환 (Streamlit 차트용)
import pandas as pd
df = pd.DataFrame({"Year": years, "Temperature": temps})

# 차트 표시
st.subheader("연도별 평균 기온 변화")
st.line_chart(df.set_index("Year"))

# 기온 상승 여부 분석
if len(years) > 0:
    first_year, last_year = years[0], years[-1]
    first_temp, last_temp = temps[0], temps[-1]

    st.subheader("기온 상승 여부 분석")
    st.write(f"시작 연도({first_year}) 평균 기온: {first_temp:.2f}")
    st.write(f"마지막 연도({last_year}) 평균 기온: {last_temp:.2f}")

    if last_temp > first_temp:
        st.success("지난 110년 동안 기온이 상승했습니다 🌡️📈")
    else:
        st.warning("지난 110년 동안 기온이 하락하거나 큰 변화가 없습니다 🌡️📉")

# 추가 기능: 이동평균으로 추세 확인
window = st.slider("이동평균 윈도우 크기 선택", 5, 30, 10)
moving_avg = []

for i in range(len(temps)):
    if i < window:
        moving_avg.append(statistics.mean(temps[:i+1]))
    else:
        moving_avg.append(statistics.mean(temps[i-window+1:i+1]))

df["Moving Average"] = moving_avg
st.subheader("이동평균 추세")
st.area_chart(df.set_index("Year")[["Moving Average"]])
