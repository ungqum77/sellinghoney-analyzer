import streamlit as st
import pandas as pd
import datetime
import io

st.set_page_config(page_title="J.W의 슈퍼 소싱 분석기 2026", layout="wide")
st.title("🚀 셀링하니 슈퍼 소싱 자동 분석 Ver 4.0")
st.subheader("데이터는 정제하고, 전략은 Gems에게 맡기세요!")

uploaded_file = st.file_uploader("엑셀 파일(xlsx)을 업로드하세요", type="xlsx")

analyze_option = st.radio(
    "분석 조건을 선택하세요:",
    ("경쟁도 낮은 상품", "매력도 높은 상품", "성장하는 상품", "급성장 상품"),
    horizontal=True
)

option_map = {
    "경쟁도 낮은 상품": "lowCompetition",
    "매력도 높은 상품": "highAttractiveness",
    "성장하는 상품": "growing",
    "급성장 상품": "explosive",
}

def analyze_excel(file, analysis_type):
    xls = pd.ExcelFile(file)
    all_results = []

    for sheet_name in xls.sheet_names:
        df = xls.parse(sheet_name)
        
        # [수정포인트 1] 컬럼명 유연하게 찾기 (공백 제거 등)
        df.columns = [str(c).strip() for c in df.columns]
        
        # 필수 컬럼 체크
        required_cols = ["키워드", "검색량", "경쟁률"]
        if not all(col in df.columns for col in required_cols):
            continue # 필수 컬럼 없으면 이 시트는 건너뜀

        # [수정포인트 2] 에러 방지를 위해 수치 데이터 강제 변환
        df["검색량"] = pd.to_numeric(df["검색량"], errors='coerce').fillna(0)
        df["경쟁률"] = pd.to_numeric(df["경쟁률"], errors='coerce').fillna(999)
        
        for _, row in df.iterrows():
            try:
                경쟁률 = float(row["경쟁률"])
                검색량 = int(row["검색량"])
                
                # 쇼핑성 키워드 체크 (없으면 기본 True)
                쇼핑성 = True
                if "쇼핑성키워드" in row:
                    쇼핑성 = str(row["쇼핑성키워드"]).upper() in ["TRUE", "Y", "쇼핑성"]

                매력도 = float(row.get("매력도", 0))
                성장성 = float(row.get("성장성", 0))

                조건 = {
                    "lowCompetition": 경쟁률 < 4 and 검색량 >= 5000 and 쇼핑성,
                    "highAttractiveness": 매력도 >= 3 and 검색량 >= 5000 and 쇼핑성,
                    "growing": 성장성 >= 0 and 검색량 >= 5000 and 쇼핑성 and 경쟁률 < 4,
                    "explosive": 성장성 >= 0.15 and 검색량 >= 5000 and 쇼핑성,
                }

                if 조건[analysis_type]:
                    all_results.append({
                        "키워드": row["키워드"],
                        "카테고리": row.get("카테고리전체", "미분류"),
                        "검색량": 검색량,
                        "경쟁률": 경쟁률,
                        "계절성": row.get("계절성", "-"),
                    })
            except:
                continue

    return pd.DataFrame(all_results)

if uploaded_file and st.button("분석 시작"):
    with st.spinner("데이터 분석 중..."):
        df_result = analyze_excel(uploaded_file, option_map[analyze_option])

    if not df_result.empty:
        df_result = df_result.sort_values(by="검색량", ascending=False).reset_index(drop=True)
        st.success(f"총 {len(df_result)}개의 유망 상품을 찾았습니다!")
        
        # 화면 출력
        st.dataframe(df_result)

        # [중요] Gems로 전달할 텍스트 요약 생성
        st.info("💡 아래 요약 내용을 복사해서 Gemini Gems에 붙여넣으세요!")
        summary_text = f"분석 결과 상위 5개 아이템: {', '.join(df_result['키워드'].head(5).tolist())}"
        st.code(summary_text)

        # 엑셀 다운로드 버튼
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df_result.to_excel(writer, index=False)
        
        st.download_button("결과 파일 다운로드", buffer, f"analysis_{analyze_option}.xlsx")
    else:
        st.warning("조건에 맞는 상품이 없습니다. 엑셀의 컬럼명(키워드, 검색량, 경쟁률)을 확인해주세요.")
