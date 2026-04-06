import streamlit as st
import pandas as pd
import datetime
import io

st.set_page_config(page_title="J.W의 슈퍼 소싱 분석기 2026", layout="wide")
st.title("🚀 셀링하니 슈퍼 소싱 자동 분석 Ver 5.0")
st.info("최신 엑셀 양식(클릭지수, 성장성 등)에 최적화되었습니다.")

uploaded_file = st.file_uploader("셀링하니에서 받은 엑셀 파일을 업로드하세요", type="xlsx")

analyze_option = st.radio(
    "분석 조건을 선택하세요:",
    ("경쟁도 낮은 상품", "매력도 높은 상품", "성장하는 상품", "급성장 상품"),
    horizontal=True
)

def analyze_excel(file, analysis_type):
    xls = pd.ExcelFile(file)
    all_results = []

    for sheet_name in xls.sheet_names:
        df = xls.parse(sheet_name)
        # 컬럼명 앞뒤 공백 제거
        df.columns = [str(c).strip() for c in df.columns]

        # [핵심] 사진 속 명칭으로 매핑 (에러 방지)
        mapping = {
            '키워드': ['키워드', '상품명', '검색어'],
            '검색량': ['클릭지수', '검색량', '월간검색수', '총클릭수'],
            '경쟁률': ['경쟁률', '경쟁도', '경쟁강도', '상품수/클릭수'], # 경쟁률이 없으면 직접 계산할 수도 있음
            '성장성': ['성장성', '성장도'],
            '카테고리': ['전체 카테고리', '카테고리', '카테고리전체']
        }
        
        for standard, aliases in mapping.items():
            for alias in aliases:
                if alias in df.columns:
                    df.rename(columns={alias: standard}, inplace=True)
                    break

        # 필수 데이터가 '클릭지수(검색량)'만 있어도 일단 진행하게 수정
        if '키워드' not in df.columns or '검색량' not in df.columns:
            continue

        # 데이터 숫자형 변환 (에러 방지)
        df["검색량"] = pd.to_numeric(df["검색량"], errors='coerce').fillna(0)
        df["경쟁률"] = pd.to_numeric(df["경쟁률"], errors='coerce').fillna(0) # 없으면 0
        df["성장성"] = pd.to_numeric(df.get("성장성", 0), errors='coerce').fillna(0)
        
        for _, row in df.iterrows():
            try:
                검색량 = int(row["검색량"])
                경쟁률 = float(row["경쟁률"])
                성장성 = float(row["성장성"])
                
                # 분석 조건 설정 (클릭지수 기반으로 변경)
                is_target = False
                if analysis_type == "경쟁도 낮은 상품":
                    is_target = 검색량 >= 3000 and 경쟁률 < 5
                elif analysis_type == "매력도 높은 상품":
                    is_target = 검색량 >= 5000
                elif analysis_type == "성장하는 상품":
                    is_target = 성장성 > 0 and 검색량 >= 2000
                elif analysis_type == "급성장 상품":
                    is_target = 성장성 >= 0.1 and 검색량 >= 2000

                if is_target:
                    all_results.append({
                        "키워드": row["키워드"],
                        "카테고리": row.get("카테고리", "-"),
                        "클릭지수(검색량)": 검색량,
                        "경쟁률": 경쟁률,
                        "성장성": f"{성장성*100:.1f}%" if 성장성 != 0 else "-",
                        "계절성": row.get("계절성", "-")
                    })
            except:
                continue

    return pd.DataFrame(all_results)

if uploaded_file and st.button("실시간 분석 시작"):
    with st.spinner("데이터를 정제하는 중입니다..."):
        df_result = analyze_excel(uploaded_file, analyze_option)

    if not df_result.empty:
        df_result = df_result.sort_values(by="클릭지수(검색량)", ascending=False).reset_index(drop=True)
        st.success(f"✅ 총 {len(df_result)}개의 유망 상품 아이템을 찾았습니다!")
        st.dataframe(df_result)

        # Gems 연동용 요약 텍스트
        st.markdown("---")
        st.subheader("🤖 Gemini Gems에 전달할 데이터")
        top_keywords = ", ".join(df_result['키워드'].head(5).tolist())
        summary_text = f"상위 추천 키워드: {top_keywords}\n이 상품들에 대한 타겟 분석과 상세페이지 기획을 시작해줘."
        st.code(summary_text)
        
        # 다운로드 버튼
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df_result.to_excel(writer, index=False)
        st.download_button("결과 파일 다운로드", buffer, "JW_Sourcing_Result.xlsx")
    else:
        st.warning("조건에 맞는 상품이 없습니다. 분석 조건을 변경하거나 엑셀 데이터를 확인해주세요.")
