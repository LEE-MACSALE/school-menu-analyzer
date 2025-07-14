import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

# 식품 영양 DB (간이 버전)
food_nutrition_db = {
    "밥": {"칼로리": 300, "탄수화물": 65, "단백질": 6, "지방": 1},
    "김치": {"칼로리": 50, "탄수화물": 5, "단백질": 2, "지방": 1},
    "미역국": {"칼로리": 70, "탄수화물": 6, "단백질": 4, "지방": 3},
    "돈까스": {"칼로리": 450, "탄수화물": 25, "단백질": 20, "지방": 30},
    "계란찜": {"칼로리": 110, "탄수화물": 1, "단백질": 8, "지방": 9},
    "떡볶이": {"칼로리": 300, "탄수화물": 50, "단백질": 5, "지방": 7},
    "요구르트": {"칼로리": 80, "탄수화물": 12, "단백질": 3, "지방": 2},
}

# 식단 크롤링 함수 (키 자동 추론)
def get_menu_by_date(date_str):
    url = "https://school.gyo6.net/pocheolhs/ad/fm/foodmenu/selectFoodMenuView.do?mi=165626"
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')

        menus = {}
        rows = soup.select('table.tbl_type tbody tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 2:
                continue
            day_text = cols[0].text.strip().replace("\n", "").replace(" ", "")
            menu_text = cols[1].text.strip()
            menus[day_text] = menu_text

        # 실제 등록된 키 디버깅 출력 (Streamlit 화면에 표시)
        st.write("📌 등록된 날짜 키 목록:")
        for key in menus.keys():
            st.write(f" - {key}")

        # 날짜 포맷 생성
        day = datetime.strptime(date_str, "%Y-%m-%d").day
        weekday_kor = ["월", "화", "수", "목", "금", "토", "일"]
        weekday = weekday_kor[datetime.strptime(date_str, "%Y-%m-%d").weekday()]
        keys_to_try = [
            f"{day}",
            f"{day}일",
            f"{day}({weekday})",
            f"{day}일({weekday})",
            f"{day}일{weekday}"
        ]

        # 키 매칭 시도
        for key in keys_to_try:
            if key in menus:
                return menus[key]

        return "메뉴 없음"
    except Exception as e:
        return f"오류 발생: {str(e)}"

# 영양 분석 함수
def analyze_menu(menu_text):
    items = menu_text.replace('\n', ',').replace(' ', '').split(',')
    total = {"칼로리": 0, "탄수화물": 0, "단백질": 0, "지방": 0}
    detail = []

    for item in items:
        if item in food_nutrition_db:
            data = food_nutrition_db[item]
            for k in total:
                total[k] += data[k]
            detail.append({"음식": item, **data})
        else:
            detail.append({"음식": item, "칼로리": None, "탄수화물": None, "단백질": None, "지방": None})

    return total, pd.DataFrame(detail)

# 권장 섭취량 비교
def show_comparison(total):
    rec = {"칼로리": 900, "탄수화물": 130, "단백질": 20, "지방": 30}
    ratio = {k: total[k]/rec[k]*100 if rec[k] else 0 for k in total}

    st.subheader("🔍 섭취량 비교")
    for k in total:
        st.write(f"{k}: {total[k]:.1f} / {rec[k]} ({ratio[k]:.1f}%)")

    fig, ax = plt.subplots()
    ax.bar(ratio.keys(), ratio.values())
    ax.axhline(100, color='r', linestyle='--')
    ax.set_ylabel("섭취 비율 (%)")
    st.pyplot(fig)

# Streamlit 앱
st.set_page_config(page_title="포철고 급식 영양소 분석기", layout="centered")
st.title("🍱 포철고 급식 영양소 분석기")

date = st.date_input("분석할 날짜를 선택하세요", value=datetime.today())
date_str = date.strftime("%Y-%m-%d")

menu = get_menu_by_date(date_str)
st.subheader("📋 오늘의 식단")
st.write(menu)

if "오류 발생" in menu:
    st.error(menu)
elif menu == "메뉴 없음":
    st.warning("선택한 날짜에 메뉴가 없습니다.")
else:
    total, df = analyze_menu(menu)
    st.subheader("📊 음식별 영양소")
    st.dataframe(df)
    show_comparison(total)
