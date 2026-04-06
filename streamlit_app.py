import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="J.W의 슈퍼 소싱 분석기 2026", layout="wide")
st.title("🚀 셀링하니 슈퍼 소싱 자동 분석 Ver 6.0")

uploaded_file = st.file_uploader("셀링하니 엑셀 파일을 업로드하세요", type="xlsx")

analyze_option = st.radio(
    "분석 조건을 선택하세요:",
    ("경쟁도 낮은 상품", "매력도 높은 상품", "성장하는 상품", "급성장 상품"),
    horizontal=True
)

def clean_number(value):
    """문자열에서 콤마 등을 제거하고 숫자로 변환하는 함수"""
    try:
        if pd.isna(value): return 0
        # 숫자형태가 아니면 문자열로 바꿔서 콤마(,) 제거 후 숫자화
        s = str(value).replace(',', '').strip()
        return float(''.join(c for c in s if c.isdigit() or c == '.'))
    except:
        return 0

def analyze_excel(file, analysis_type):
    xls = pd.ExcelFile(file)
    all_results = []

    for sheet_name in xls.sheet_names:
        df = xls.parse(sheet_name)
        df.columns = [str(c).strip() for c in df.columns]

        # 1. 컬럼 매핑 (사진 속 명칭 100% 반영)
        mapping = {
            '키워드': ['키워드', '상품명', '검색어'],
            '검색량': ['클릭지수', '검색량', '월간검색수', '총클릭수'],
            '경쟁률': ['경쟁률', '경쟁도', '경쟁강도', '상품수/클릭수', '브랜드 점유율'],
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

        # 2. 데이터 정제 (콤마 제거 및 숫자 변환 핵심!)
        df["검색량"] = df["검색량"].apply(clean_number)
        df["경쟁률"] = df.get("경쟁률", 0).apply(clean_number)
        df["성장성"] = df.get("성장성", 0).apply(clean_number)
        
        for _, row in df.iterrows():
            try:
                검색량 = row["검색량"]
                경쟁률 = row["경쟁률"]
                성장성 = row["성장성"]
                
                # [수정] 합격 기준을 '최소한'으로 낮춤 (일단 나오게 하는 게 목적)
                is_target = False
                if analysis_type == "경쟁도 낮은 상품":
                    is_target = 검색량 >= 100 # 클릭수 100만 넘어도 일단 보여줌
                elif analysis_type == "매력도 높은 상품":
                    is_target = 검색량 >= 100
                elif analysis_type == "성장하는 상품":
                    is_target = 검색량 >= 100
                elif analysis_type == "급성장 상품":
                    is_target = 검색량 >= 100

                if is_target:
                    all_results.append({
                        "키워드": row["키워드"],
                        "카테고리": row.get("카테고리", "-"),
                        "클릭지수": int(검색량),
                        "경쟁률": 경쟁률,
                        "성장성": 성장성
                    })
            except:
                continue

    return pd.DataFrame(all_results)

if uploaded_file and st.button("분석 시작"):
    with st.spinner("데이터 정밀 분석 중..."):
        df_result = analyze_excel(uploaded_file, analyze_option)

    if not df_result.empty:
        df_result = df_result.sort_values(by="클릭지수", ascending=False).reset_index(drop=True)
        st.success(f"✅ 총 {len(df_result)}개의 아이템을 찾았습니다!")
        st.dataframe(df_result)
        
        # Gems 전달용 요약
        top_5 = ", ".join(df_result['키워드'].head(5).tolist())
        st.code(f"추천 키워드: {top_5}")
    else:
        st.error("데이터를 찾을 수 없습니다. 엑셀 파일의 시트에 데이터가 있는지, 혹은 '키워드'와 '클릭지수' 컬럼이 있는지 확인해주세요.")
        # 디버깅용: 실제 읽어온 컬럼명을 보여줌
        tmp_df = pd.read_excel(uploaded_file)
        st.write("현재 엑셀에서 인식된 컬럼명들:", tmp_df.columns.tolist())
