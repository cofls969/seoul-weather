import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="서울 기온 변화 (100년)",
    page_icon="🌡️",
    layout="wide"
)

@st.cache_data
def load_data(url):
    """지정된 URL에서 CSV 데이터를 로드하고 전처리합니다."""
    encodings_to_try = ['utf-8', 'cp949', 'euc-kr']
    df = None
    
    for encoding in encodings_to_try:
        try:
            # CSV 파일 읽기 시도
            df = pd.read_csv(url, encoding=encoding)
            break # 성공하면 반복문 탈출
        except UnicodeDecodeError:
            continue # 실패하면 다음 인코딩 시도
        except Exception as e:
            st.error(f"데이터를 불러오는 중 예상치 못한 오류가 발생했습니다: {e}")
            return None

    if df is None:
        st.error("지원되는 인코딩 방식(utf-8, cp949, euc-kr)으로 파일을 읽을 수 없습니다.")
        return None

    try:
        # 데이터프레임의 실제 열 이름 확인용 (디버깅용, 나중에 지워도 됩니다)
        # st.write("실제 데이터 열 이름:", df.columns.tolist())

        # 열 이름 공백 제거 및 정리
        df.columns = df.columns.str.strip()

        # 열 이름 매핑 (데이터 파일에 따라 열 이름이 다를 수 있으므로 유연하게 대처)
        date_col = next((col for col in df.columns if '날짜' in col or '일시' in col), None)
        temp_col = next((col for col in df.columns if '평균기온' in col), None)

        if date_col is None or temp_col is None:
            st.error(f"필요한 열을 찾을 수 없습니다. (현재 열: {df.columns.tolist()})")
            return None

        # '날짜' 열을 datetime 타입으로 변환
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        # 결측치가 있는 행 제거
        df = df.dropna(subset=[date_col, temp_col])
        
        # '연도' 열 추가
        df['연도'] = df[date_col].dt.year
        
        # 통일된 이름으로 열 이름 변경
        df = df.rename(columns={date_col: '날짜', temp_col: '평균기온(℃)'})
        
        return df
    except Exception as e:
        st.error(f"데이터를 처리하는 중 오류가 발생했습니다: {e}")
        return None

def main():
    st.title("🌡️ 서울의 100년 기온 변화")
    st.write("과거 100년 동안 서울의 연평균 기온이 어떻게 변해왔는지 확인해 보세요.")

    # 데이터 URL
    data_url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"
    
    with st.spinner("데이터를 불러오는 중입니다..."):
        df = load_data(data_url)

    if df is not None:
        # 연도별로 그룹화하여 평균 기온 계산
        yearly_temp = df.groupby('연도')['평균기온(℃)'].mean().reset_index()
        
        # 데이터가 충분히 긴지 확인
        if not yearly_temp.empty:
            st.subheader("📈 연평균 기온 변화 그래프")
            
            # 추세선 계산
            z = np.polyfit(yearly_temp['연도'], yearly_temp['평균기온(℃)'], 1)
            p = np.poly1d(z)
            yearly_temp['추세선'] = p(yearly_temp['연도'])
            
            # Streamlit 내장 차트를 사용하여 렌더링 (사용자 브라우저 폰트 사용 -> 한글 안 깨짐)
            chart_data = yearly_temp.set_index('연도')[['평균기온(℃)', '추세선']]
            st.line_chart(chart_data, color=["#ff6347", "#808080"])
            
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
