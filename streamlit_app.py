import streamlit as st
import pandas as pd
import datetime
import io

st.set_page_config(page_title="셀링하니 슈퍼 소싱 자동 분석", layout="centered")
st.title("셀링하니 슈퍼 소싱 자동 분석 Ver 3.0 (Restored)")

uploaded_file = st.file_uploader("엑셀 파일 업로드 (셀링하니 데이터)", type="xlsx")

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
        
        # 컬럼명 정리 (공백 제거)
        df.columns = [str(c).strip() for c in df.columns]
        
        # 필수 컬럼(검색량, 경쟁률)이 있는지 확인 (무료 버전 대응)
        # 만약 '클릭지수'로 되어 있다면 '검색량'으로 이름 변경
        if '클릭지수' in df.columns:
            df.rename(columns={'클릭지수': '검색량'}, inplace=True)
        if '경쟁도' in df.columns:
            df.rename(columns={'경쟁도': '경쟁률'}, inplace=True)

        # 필수 컬럼이 없으면 해당 시트 스킵
        if not {'검색량', '경쟁률'}.issubset(df.columns):
            continue

        for _, row in df.iterrows():
            try:
                # 데이터 숫자 변환 및 콤마 제거
                경쟁률 = float(str(row["경쟁률"]).replace(',', ''))
                검색량 = int(str(row["검색량"]).replace(',', ''))
                
                # 쇼핑성키워드 컬럼이 없으면 기본 True로 처리 (무료 버전 대응)
                쇼핑성 = True
                if "쇼핑성키워드" in df.columns:
                    쇼핑성 = str(row["쇼핑성키워드"]).upper() in [True, "TRUE", "Y", "쇼핑성"]
                
                # 매력도, 성장성 컬럼이 없으면 0으로 처리
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
                        "키워드": row.get("키워드", "알수없음"),
                        "카테고리전체": row.get("카테고리전체", row.get("전체 카테고리", "-")),
                        "검색량": 검색량,
                        "경쟁률": 경쟁률,
                        "광고경쟁강도": row.get("광고경쟁강도", "-"),
                        "계절성": row.get("계절성", "-"),
                    })
            except:
                continue

    result_df = pd.DataFrame(result)
    if not result_df.empty:
        result_df = result_df.sort_values(by="검색량", ascending=False).reset_index(drop=True)
        result_df["순서_검색량순"] = result_df.index + 1
    return result_df

if uploaded_file and start_analysis:
    analysis_key = option_map[analyze_option]
    with st.spinner("분석 중입니다... 잠시만 기다려주세요."):
        df_result = analyze_excel(uploaded_file, analysis_key)

    if not df_result.empty:
        st.success("완벽한 상품 리스트가 준비되었습니다.")
        st.dataframe(df_result.head(10))

        # Gems 연동을 위한 텍스트 박스 추가 (강의용)
        st.info("💡 이 키워드들을 복사해서 Gemini Gems에 넣으세요!")
        top_keywords = ", ".join(df_result['키워드'].head(5).tolist())
        st.code(f"추천 키워드 리스트: {top_keywords}")

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df_result.to_excel(writer, index=False, sheet_name="분석결과")

        today = datetime.date.today().strftime("%y.%m.%d")
        filename = f"{today} 소싱 리스트_{analyze_option}.xlsx"

        st.download_button(
            label="엑셀 다운로드",
            data=buffer,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("조건에 맞는 데이터가 없습니다. 검색량 기준(5000)을 확인하거나 다른 파일을 업로드해주세요.")

st.markdown("---")
st.markdown("다른 파일을 업로드 하시면 새로운 분석을 진행 합니다")
