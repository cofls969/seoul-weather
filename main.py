import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="서울 기온 변화 (100년)",
    page_icon="🌡️",
    layout="wide"
)

import matplotlib.font_manager as fm
import os

@st.cache_resource
def set_korean_font():
    """Streamlit Cloud 등 Linux 환경에서 한글 폰트(NanumGothic)를 설정합니다."""
    # 시스템에 설치된 폰트 중 나눔 폰트 찾기
    font_list = fm.findSystemFonts(fontpaths=None, fontext='ttf')
    nanum_fonts = [f for f in font_list if 'Nanum' in f]
    
    if nanum_fonts:
        # 나눔 폰트가 있으면 첫 번째 폰트를 사용
        font_path = nanum_fonts[0]
        font_name = fm.FontProperties(fname=font_path).get_name()
        plt.rc('font', family=font_name)
    else:
        # 폰트가 없을 경우 기본 폰트 사용 시도 (경고 메시지 출력 안 함)
        pass
    
    plt.rcParams['axes.unicode_minus'] = False # 마이너스 기호 깨짐 방지

set_korean_font()

@st.cache_data
def load_data(url):
    """지정된 URL에서 CSV 데이터를 로드하고 전처리합니다."""
    try:
        # CSV 파일 읽기 (인코딩 'cp949' 또는 'euc-kr' 처리, 에러 발생 시 무시)
        # 웹에 있는 데이터이므로 pandas가 알아서 다운로드하여 읽습니다.
        df = pd.read_csv(url, encoding='cp949') 
        
        # '날짜' 열을 datetime 타입으로 변환
        df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
        
        # 결측치가 있는 행 제거
        df = df.dropna(subset=['날짜', '평균기온(℃)'])
        
        # '연도' 열 추가
        df['연도'] = df['날짜'].dt.year
        
        return df
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
        return None

def main():
    st.title("🌡️ 서울의 100년 기온 변화")
    st.write("과거 100년 동안 서울의 연평균 기온이 어떻게 변해왔는지 확인해 보세요.")

    # 데이터 URL
    data_url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"
    
    with st.spinner("데이터를 불러오는 중입니다..."):
        df = load_data(data_url)

    if df is not None:
        # 1923년(현재 연도 기준 약 100년 전)부터의 데이터만 필터링 (데이터에 따라 조정 가능)
        # 여기서는 전체 데이터 중 최근 100년에 가까운 의미를 갖도록 그룹화합니다.
        
        # 연도별로 그룹화하여 평균 기온 계산
        yearly_temp = df.groupby('연도')['평균기온(℃)'].mean().reset_index()
        
        # 데이터가 충분히 긴지 확인
        if not yearly_temp.empty:
            st.subheader("📈 연평균 기온 변화 그래프")
            
            # Matplotlib를 사용하여 그래프 생성
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # 선 그래프 그리기
            ax.plot(yearly_temp['연도'], yearly_temp['평균기온(℃)'], 
                    color='tomato', linewidth=2, marker='o', markersize=4, label='연평균 기온')
            
            # 추세선 (선택 사항 - 데이터의 전반적인 방향을 보여줌)
            import numpy as np
            z = np.polyfit(yearly_temp['연도'], yearly_temp['평균기온(℃)'], 1)
            p = np.poly1d(z)
            ax.plot(yearly_temp['연도'], p(yearly_temp['연도']), 
                    color='gray', linestyle='--', linewidth=1.5, label='추세선')

            # 그래프 꾸미기
            ax.set_title("서울시 연평균 기온 변화", fontsize=16, fontweight='bold', pad=15)
            ax.set_xlabel("연도", fontsize=12)
            ax.set_ylabel("평균기온 (℃)", fontsize=12)
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.legend(fontsize=12)
            
            # Streamlit에 그래프 표시
            st.pyplot(fig)
            
            st.markdown("---")
            st.subheader("💡 데이터 요약")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("데이터 분석 기간", f"{yearly_temp['연도'].min()}년 ~ {yearly_temp['연도'].max()}년")
            with col2:
                highest_year = yearly_temp.loc[yearly_temp['평균기온(℃)'].idxmax()]
                st.metric(f"가장 더웠던 해 ({int(highest_year['연도'])}년)", f"{highest_year['평균기온(℃)']:.1f}℃")
            with col3:
                lowest_year = yearly_temp.loc[yearly_temp['평균기온(℃)'].idxmin()]
                st.metric(f"가장 추웠던 해 ({int(lowest_year['연도'])}년)", f"{lowest_year['평균기온(℃)']:.1f}℃")
            
            with st.expander("원본 데이터 보기 (처음 100개 행)"):
                st.dataframe(df.head(100), use_container_width=True)
                
        else:
            st.warning("분석할 데이터가 충분하지 않습니다.")

if __name__ == "__main__":
    main()
