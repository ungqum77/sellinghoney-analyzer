# streamlit_app.py
import streamlit as st
import pandas as pd
import datetime
import io

st.set_page_config(page_title="셀링하니 슈퍼 소싱 자동 분석", layout="centered")
st.title("셀링하니 슈퍼 소싱 자동 분석 Ver 3.0")

uploaded_file = st.file_uploader("엑셀 파일 업로드 (10개 시트)", type="xlsx")

analyze_option = st.radio(
    "분석 조건을 선택하세요:",
    ("경쟁도 낮은 상품", "매력도 높은 상품", "성장하는 상품", "급성장 상품")
)

start_analysis = st.button("분석 시작")

option_map = {
    "경쟁도 낮은 상품": "lowCompetition",
    "매력도 높은 상품": "highAttractiveness",
    "성장하는 상품": "growing",
    "급성장 상품": "explosive",
}

def analyze_excel(file, analysis_type):
    xls = pd.ExcelFile(file)
    result = []

    for sheet_name in xls.sheet_names:
        df = xls.parse(sheet_name)
        df = df.dropna(subset=["검색량", "경쟁률"])
        for _, row in df.iterrows():
            try:
                경쟁률 = float(row["경쟁률"])
                검색량 = int(row["검색량"])
                쇼핑성 = row["쇼핑성키워드"] in [True, "TRUE"]
                매력도 = float(row.get("매력도", 0))
                성장성 = float(row.get("성장성", 0))

                조건 = {
                    "lowCompetition": 경쟁률 < 4 and 검색량 >= 5000 and 쇼핑성,
                    "highAttractiveness": 매력도 >= 3 and 검색량 >= 5000 and 쇼핑성,
                    "growing": 성장성 >= 0 and 검색량 >= 5000 and 쇼핑성 and 경쟁률 < 4,
                    "explosive": 성장성 >= 0.15 and 검색량 >= 5000 and 쇼핑성,
                }

                if 조건[analysis_type]:
                    result.append({
                        "순서_검색량순": 0,
                        "키워드": row["키워드"],
                        "카테고리전체": row["카테고리전체"],
                        "검색량": 검색량,
                        "경쟁률": 경쟁률,
                        "광고경쟁강도": row["광고경쟁강도"],
                        "계절성": row["계절성"],
                    })
            except:
                continue

    result_df = pd.DataFrame(result)
    result_df = result_df.sort_values(by="검색량", ascending=False).reset_index(drop=True)
    result_df["순서_검색량순"] = result_df.index + 1
    return result_df

if uploaded_file and start_analysis:
    analysis_key = option_map[analyze_option]
    with st.spinner("분석 중입니다... 잠시만 기다려주세요."):
        df_result = analyze_excel(uploaded_file, analysis_key)

    if not df_result.empty:
        st.success("오래 기다려주셔서 감사합니다. 완벽한 상품 리스트가 준비되었습니다. 브랜드 키워드가 포함되어 있을 수 있으니 참고하세요")
        st.dataframe(df_result.head(10))

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df_result.to_excel(writer, index=False, sheet_name="분석결과")

        today = datetime.date.today().strftime("%y.%m.%d")
        filename = f"{today} 셀링하니 좋은 상품 리스트_{analyze_option}.xlsx"

        st.download_button(
            label="엑셀 다운로드",
            data=buffer,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("선택한 조건에 맞는 데이터가 없습니다.")

st.markdown("---")
st.markdown("다른 파일을 업로드 하시면 새로운 분석을 진행 합니다")
