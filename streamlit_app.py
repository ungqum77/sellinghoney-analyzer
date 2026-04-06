import streamlit as st
import pandas as pd
import datetime
import io

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="J.W의 전천후 소싱 분석기", layout="wide")
st.title("🚀 셀링하니 4대 전략 통합 분석기 Ver 7.0")
st.markdown("---")

# 2. 사이드바 설정 (출력 개수 조절)
st.sidebar.header("📊 출력 설정")
show_count = st.sidebar.slider("화면에 보여줄 상품 개수 선택", min_value=5, max_value=100, value=20, step=5)

# 3. 파일 업로드
uploaded_file = st.file_uploader("셀링하니 엑셀 파일을 업로드하세요 (xlsx)", type="xlsx")

def analyze_all_strategies(file):
    """파일 하나를 읽어 4가지 전략 결과를 딕셔너리로 반환"""
    xls = pd.ExcelFile(file)
    # 결과를 담을 그릇 준비
    final_reports = {
        "경쟁도 낮은 상품": [],
        "매력도 높은 상품": [],
        "성장하는 상품": [],
        "급성장 상품": []
    }

    for sheet_name in xls.sheet_names:
        df = xls.parse(sheet_name)
        df.columns = [str(c).strip() for c in df.columns]

        # 컬럼 명칭 유연하게 매핑 (무료/유료 버전 모두 대응)
        mapping = {
            '키워드': ['키워드', '상품명', '검색어'],
            '검색량': ['클릭지수', '검색량', '월간검색수', '총클릭수'],
            '경쟁률': ['경쟁률', '경쟁도', '상품수/클릭수', '경쟁강도'],
            '매력도': ['매력도', '상품매력도'],
            '성장성': ['성장성', '성장도']
        }
        
        for standard, aliases in mapping.items():
            for alias in aliases:
                if alias in df.columns:
                    df.rename(columns={alias: standard}, inplace=True)
                    break

        if '키워드' not in df.columns or '검색량' not in df.columns:
            continue

        # 데이터 숫자형 변환 및 콤마 제거
        def to_num(val):
            try: return float(str(val).replace(',', ''))
            except: return 0

        df["검색량"] = df["검색량"].apply(to_num)
        df["경쟁률"] = df.get("경쟁률", 0).apply(to_num)
        df["매력도"] = df.get("매력도", 0).apply(to_num)
        df["성장성"] = df.get("성장성", 0).apply(to_num)

        for _, row in df.iterrows():
            item = {
                "키워드": row["키워드"],
                "카테고리": row.get("전체 카테고리", row.get("카테고리", "-")),
                "검색량": int(row["검색량"]),
                "경쟁률": round(row["경쟁률"], 2),
                "매력도": round(row["매력도"], 2),
                "성장성": round(row["성장성"], 2)
            }
            
            # [전략 1] 경쟁도 낮은 (검색량 2000↑, 경쟁률 4↓)
            if item["검색량"] >= 2000 and (0 < item["경쟁률"] < 4):
                final_reports["경쟁도 낮은 상품"].append(item)
            
            # [전략 2] 매력도 높은 (매력도 3↑, 검색량 3000↑)
            if item["매력도"] >= 3 and item["검색량"] >= 3000:
                final_reports["매력도 높은 상품"].append(item)
                
            # [전략 3] 성장하는 (성장성 0↑, 검색량 2000↑)
            if item["성장성"] > 0 and item["검색량"] >= 2000:
                final_reports["성장하는 상품"].append(item)
                
            # [전략 4] 급성장 (성장성 0.15↑, 검색량 1000↑)
            if item["성장성"] >= 0.15 and item["검색량"] >= 1000:
                final_reports["급성장 상품"].append(item)

    # DataFrame 변환 및 검색량 순 정렬
    for key in final_reports:
        df_tmp = pd.DataFrame(final_reports[key])
        if not df_tmp.empty:
            final_reports[key] = df_tmp.sort_values(by="검색량", ascending=False).reset_index(drop=True)
        else:
            final_reports[key] = pd.DataFrame()
            
    return final_reports

if uploaded_file:
    # 1회 분석으로 모든 결과 도출
    with st.spinner("🚀 4대 전략적 관점으로 데이터를 동시에 분석 중입니다..."):
        all_results = analyze_all_strategies(uploaded_file)
    
    st.success("✅ 분석 완료! 상단 라디오 버튼을 클릭하여 리포트를 전환하세요.")

    # 4가지 필터 선택 (라디오 버튼)
    choice = st.radio(
        "🧐 어떤 전략의 상품을 확인하시겠습니까?", 
        list(all_results.keys()), 
        horizontal=True
    )
    
    target_df = all_results[choice]
    
    if not target_df.empty:
        # 사용자가 설정한 개수만큼 슬라이싱
        display_df = target_df.head(show_count).copy()
        display_df.index = display_df.index + 1 # 순번 1부터 시작
        
        st.subheader(f"📊 {choice} 리포트 (TOP {len(display_df)})")
        st.dataframe(display_df, use_container_width=True)
        
        # 💡 Gems 브릿지 (강의 핵심 포인트)
        st.markdown("---")
        st.subheader("🤖 Gemini Gems용 데이터 복사")
        top_k = ", ".join(display_df['키워드'].head(5).tolist())
        st.code(f"추천 키워드 리스트: {top_k}\n이 상품들의 타겟 페르소나와 상세페이지 기획안을 작성해줘.")
        
        # 엑셀 다운로드
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            display_df.to_excel(writer, index=False)
        
        st.download_button(
            label=f"📥 {choice} 리스트 엑셀 다운로드",
            data=buffer,
            file_name=f"JW_Sourcing_{choice}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning(f"앗! '{choice}' 조건에 부합하는 상품이 엑셀 파일 내에 없습니다. 다른 전략을 선택해보세요.")

st.markdown("---")
st.caption("Produced by CEO J.W Lim | Digital Startup Strategist")
