import streamlit as st
import pandas as pd
import datetime
import io

st.set_page_config(page_title="J.W의 슈퍼 소싱 분석기 2026", layout="wide")
st.title("🚀 셀링하니 슈퍼 소싱 자동 분석 Ver 5.5")

uploaded_file = st.file_uploader("셀링하니 엑셀 파일을 업로드하세요", type="xlsx")

analyze_option = st.radio(
    "분석 조건을 선택하세요:",
    ("경쟁도 낮은 상품", "매력도 높은 상품", "성장하는 상품", "급성장 상품"),
    horizontal=True
)

def analyze_excel(file, analysis_type):
    xls = pd.ExcelFile(file)
    all_results = []
    debug_info = [] # 데이터가 왜 안나오는지 진단용

    for sheet_name in xls.sheet_names:
        df = xls.parse(sheet_name)
        df.columns = [str(c).strip() for c in df.columns]

        # 컬럼 매핑
        mapping = {
            '키워드': ['키워드', '상품명', '검색어'],
            '검색량': ['클릭지수', '검색량', '월간검색수', '총클릭수'],
            '경쟁률': ['경쟁률', '경쟁도', '경쟁강도', '상품수/클릭수'],
            '성장성': ['성장성', '성장도'],
            '카테고리': ['전체 카테고리', '카테고리', '카테고리전체']
        }
        
        for standard, aliases in mapping.items():
            for alias in aliases:
                if alias in df.columns:
                    df.rename(columns={alias: standard}, inplace=True)
                    break

        if '키워드' not in df.columns or '검색량' not in df.columns:
            continue

        # 데이터 숫자형 변환 및 결측치 처리
        df["검색량"] = pd.to_numeric(df["검색량"], errors='coerce').fillna(0)
        df["경쟁률"] = pd.to_numeric(df.get("경쟁률", 0), errors='coerce').fillna(0)
        df["성장성"] = pd.to_numeric(df.get("성장성", 0), errors='coerce').fillna(0)
        
        for _, row in df.iterrows():
            try:
                검색량 = int(row["검색량"])
                경쟁률 = float(row["경쟁률"])
                성장성 = float(row["성장성"])
                
                # [수정] 합격 기준을 대폭 낮췄습니다 (초보자용 데이터 확보)
                is_target = False
                if analysis_type == "경쟁도 낮은 상품":
                    # 검색량 500 이상, 경쟁률 10 미만이면 합격
                    is_target = 검색량 >= 500 and (경쟁률 < 10 or 경쟁률 == 0)
                elif analysis_type == "매력도 높은 상품":
                    is_target = 검색량 >= 1000
                elif analysis_type == "성장하는 상품":
                    is_target = 성장성 > 0 and 검색량 >= 500
                elif analysis_type == "급성장 상품":
                    is_target = 성장성 >= 0.05 and 검색량 >= 500

                if is_target:
                    all_results.append({
                        "키워드": row["키워드"],
                        "카테고리": row.get("카테고리", "-"),
                        "클릭지수": 검색량,
                        "경쟁률": 경쟁률 if 경쟁률 > 0 else "데이터없음",
                        "성장성": f"{성장성*100:.1f}%" if 성장성 != 0 else "0%",
                        "계절성": row.get("계절성", "-")
                    })
            except:
                continue

    return pd.DataFrame(all_results)

if uploaded_file and st.button("실시간 분석 시작"):
    with st.spinner("데이터 필터링 중..."):
        df_result = analyze_excel(uploaded_file, analyze_option)

    if not df_result.empty:
        df_result = df_result.sort_values(by="클릭지수", ascending=False).reset_index(drop=True)
        st.success(f"✅ 조건에 맞는 상품 {len(df_result)}개를 찾았습니다!")
        st.dataframe(df_result)
        
        # Gems 전달용 코드박스
        st.code(f"추천 키워드 리스트: {', '.join(df_result['키워드'].head(10).tolist())}")
    else:
        # 데이터가 없을 때의 친절한 설명
        st.error("앗! 현재 선택하신 조건에 맞는 상품이 엑셀에 하나도 없습니다.")
        st.info("""
        **해결 방법:**
        1. 엑셀 파일에 **'클릭지수'가 500 이상**인 데이터가 있는지 확인해주세요.
        2. '경쟁도 낮은 상품' 대신 **'매력도 높은 상품'**을 선택하고 다시 시도해보세요.
        3. 셀링하니에서 데이터를 뽑을 때 검색량 범위를 더 넓게 설정해서 다시 다운로드 받아보세요.
        """)
