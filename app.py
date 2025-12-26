"""
한국 부동산원 주간 매매/전세 가격지수 대시보드
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from typing import Optional, Dict, List

# 페이지 설정
st.set_page_config(
    page_title="부동산 가격지수 대시보드",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

class PriceIndexAPI:
    """부동산 가격지수 API 클래스"""
    
    BASE_URL = "https://www.reb.or.kr/r-one/openapi/SttsApiTblData.do"
    
    # 통계표 ID
    STATBL_IDS = {
        '매매': 'T244183132827305',
        '전세': 'T247713133046872'
    }
    
    CYCLE_CODE = "WK"  # 주간
    
    # 지역코드
    REGION_CODES = {
        '전국': '50001',
        '서울': '50008',
        '경기': '50016',
        '인천': '50124',
        '부산': '50025',
        '대구': '50150',
        '광주': '50159',
        '대전': '50165',
        '울산': '50171',
        '세종': '50033',
        '강원': '50177',
        '충북': '50185',
        '충남': '50194',
        '전북': '50207',
        '전남': '50216',
        '경북': '50223',
        '경남': '50237',
        '제주': '50250',
    }
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def get_data(
        self,
        price_type: str,
        start_date: str,
        end_date: str,
        region_code: str
    ) -> Optional[pd.DataFrame]:
        """
        가격지수 데이터 조회
        
        Args:
            price_type: '매매' or '전세'
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)
            region_code: 지역코드
        
        Returns:
            DataFrame 또는 None
        """
        statbl_id = self.STATBL_IDS.get(price_type)
        if not statbl_id:
            return None
        
        params = {
            'STATBL_ID': statbl_id,
            'DTACYCLE_CD': self.CYCLE_CODE,
            'START_WRTTIME': start_date,
            'END_WRTTIME': end_date,
            'Type': 'json',
            'Key': self.api_key,
            'pIndex': 1,
            'pSize': 1000,
            'CLS_ID': region_code,
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # 에러 체크
            if 'RESULT' in data:
                result = data['RESULT']
                if result['CODE'] != 'INFO-000':
                    return None
            
            # 데이터 추출
            rows = []
            if 'SttsApiTblData' in data:
                stts_data = data['SttsApiTblData']
                if isinstance(stts_data, list) and len(stts_data) > 1:
                    if 'row' in stts_data[1]:
                        rows = stts_data[1]['row']
                        if not isinstance(rows, list):
                            rows = [rows]
            
            if not rows:
                return None
            
            df = pd.DataFrame(rows)
            
            # 날짜 변환
            if 'WRTTIME_IDTFR_ID' in df.columns:
                df['날짜'] = pd.to_datetime(df['WRTTIME_IDTFR_ID'], format='%Y%m%d', errors='coerce')
            
            # 숫자 변환
            if 'DTA_VAL' in df.columns:
                df['지수'] = pd.to_numeric(df['DTA_VAL'], errors='coerce')
            
            # 필요한 컬럼만 선택
            df = df[['날짜', '지수']].copy()
            df['가격유형'] = price_type
            
            # 정렬
            df = df.sort_values('날짜').reset_index(drop=True)
            
            return df
            
        except Exception as e:
            st.error(f"데이터 조회 오류: {e}")
            return None
    
    def get_multiple_data(
        self,
        price_types: List[str],
        start_date: str,
        end_date: str,
        region_names: List[str]
    ) -> pd.DataFrame:
        """
        여러 지역 및 가격유형 데이터를 한 번에 조회
        
        Args:
            price_types: ['매매', '전세']
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)
            region_names: 지역명 리스트
        
        Returns:
            통합된 DataFrame
        """
        all_data = []
        total_tasks = len(price_types) * len(region_names)
        current_task = 0
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for region_name in region_names:
            region_code = self.REGION_CODES.get(region_name)
            if not region_code:
                continue
            
            for price_type in price_types:
                current_task += 1
                status_text.text(f"조회 중... {region_name} {price_type} ({current_task}/{total_tasks})")
                progress_bar.progress(current_task / total_tasks)
                
                df = self.get_data(price_type, start_date, end_date, region_code)
                
                if df is not None and not df.empty:
                    df['지역'] = region_name
                    all_data.append(df)
        
        progress_bar.empty()
        status_text.empty()
        
        if all_data:
            combined = pd.concat(all_data, ignore_index=True)
            return combined
        else:
            return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_data(api_key: str, price_types: List[str], start_date: str, end_date: str, regions: List[str]):
    """데이터 로드 (캐시 사용)"""
    api = PriceIndexAPI(api_key)
    return api.get_multiple_data(price_types, start_date, end_date, regions)


def calculate_date_range(period: str, custom_start: Optional[str] = None, custom_end: Optional[str] = None):
    """기간에 따른 날짜 범위 계산"""
    end_date = datetime.now()
    
    if period == "1년":
        start_date = end_date - timedelta(days=365)
    elif period == "3년":
        start_date = end_date - timedelta(days=365*3)
    elif period == "5년":
        start_date = end_date - timedelta(days=365*5)
    elif period == "10년":
        start_date = end_date - timedelta(days=365*10)
    elif period == "사용자 지정":
        if custom_start and custom_end:
            start_date = datetime.strptime(custom_start, '%Y-%m-%d')
            end_date = datetime.strptime(custom_end, '%Y-%m-%d')
        else:
            start_date = end_date - timedelta(days=365)
    else:
        start_date = end_date - timedelta(days=365)
    
    return start_date.strftime('%Y%m%d'), end_date.strftime('%Y%m%d')


def create_chart(df: pd.DataFrame, chart_type: str, regions: List[str]):
    """차트 생성"""
    
    if df.empty:
        st.warning("표시할 데이터가 없습니다.")
        return
    
    fig = go.Figure()
    
    if chart_type == "매매":
        # 매매 지수만
        df_filtered = df[df['가격유형'] == '매매']
        
        for region in regions:
            region_data = df_filtered[df_filtered['지역'] == region]
            if not region_data.empty:
                fig.add_trace(go.Scatter(
                    x=region_data['날짜'],
                    y=region_data['지수'],
                    mode='lines',
                    name=f"{region} 매매",
                    line=dict(width=2)
                ))
    
    elif chart_type == "전세":
        # 전세 지수만
        df_filtered = df[df['가격유형'] == '전세']
        
        for region in regions:
            region_data = df_filtered[df_filtered['지역'] == region]
            if not region_data.empty:
                fig.add_trace(go.Scatter(
                    x=region_data['날짜'],
                    y=region_data['지수'],
                    mode='lines',
                    name=f"{region} 전세",
                    line=dict(width=2)
                ))
    
    elif chart_type == "매매/전세":
        # 매매/전세 비율
        df_pivot = df.pivot_table(
            index=['날짜', '지역'],
            columns='가격유형',
            values='지수'
        ).reset_index()
        
        if '매매' in df_pivot.columns and '전세' in df_pivot.columns:
            df_pivot['매매전세비율'] = (df_pivot['매매'] / df_pivot['전세']) * 100
            
            for region in regions:
                region_data = df_pivot[df_pivot['지역'] == region]
                if not region_data.empty:
                    fig.add_trace(go.Scatter(
                        x=region_data['날짜'],
                        y=region_data['매매전세비율'],
                        mode='lines',
                        name=f"{region}",
                        line=dict(width=2)
                    ))
    
    # 레이아웃 설정
    if chart_type == "매매/전세":
        title = "매매/전세 비율 추이"
        yaxis_title = "매매전세비율 (%)"
    else:
        title = f"{chart_type} 가격지수 추이"
        yaxis_title = "지수"
    
    fig.update_layout(
        title=title,
        xaxis_title="날짜",
        yaxis_title=yaxis_title,
        hovermode='x unified',
        height=600,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.01
        ),
        margin=dict(r=150)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def create_statistics_table(df: pd.DataFrame, regions: List[str]):
    """통계 테이블 생성"""
    
    if df.empty:
        return
    
    stats_list = []
    
    for region in regions:
        region_data = df[df['지역'] == region]
        
        for price_type in ['매매', '전세']:
            type_data = region_data[region_data['가격유형'] == price_type]
            
            if not type_data.empty:
                latest = type_data.iloc[-1]['지수']
                earliest = type_data.iloc[0]['지수']
                change = latest - earliest
                change_pct = (change / earliest) * 100 if earliest != 0 else 0
                
                stats_list.append({
                    '지역': region,
                    '유형': price_type,
                    '최초지수': f"{earliest:.2f}",
                    '최근지수': f"{latest:.2f}",
                    '변화': f"{change:+.2f}",
                    '변화율(%)': f"{change_pct:+.2f}%"
                })
    
    if stats_list:
        stats_df = pd.DataFrame(stats_list)
        st.dataframe(stats_df, use_container_width=True, hide_index=True)


def main():
    """메인 함수"""
    
    # 타이틀
    st.title("🏠 부동산 가격지수 대시보드")
    st.markdown("한국 부동산원 주간 매매/전세 가격지수")
    
    # API 키 확인
    try:
        api_key = st.secrets["API_KEY"]
    except Exception:
        st.error("⚠️ API 키가 설정되지 않았습니다. Streamlit Cloud의 Secrets에 API_KEY를 추가하세요.")
        st.info("""
        **Secrets 설정 방법:**
        1. Streamlit Cloud 대시보드에서 앱 선택
        2. Settings > Secrets 클릭
        3. 다음 내용 추가:
        ```
        API_KEY = "your_api_key_here"
        ```
        """)
        st.stop()
    
    # 사이드바 설정
    st.sidebar.header("⚙️ 설정")
    
    # 지역 선택
    st.sidebar.subheader("📍 지역 선택")
    
    region_list = list(PriceIndexAPI.REGION_CODES.keys())
    
    # 전체 선택 옵션
    select_all = st.sidebar.checkbox("전체 선택", value=False)
    
    if select_all:
        selected_regions = st.sidebar.multiselect(
            "지역",
            options=region_list,
            default=region_list,
            label_visibility="collapsed"
        )
    else:
        selected_regions = st.sidebar.multiselect(
            "지역",
            options=region_list,
            default=['전국', '서울', '경기'],
            label_visibility="collapsed"
        )
    
    # 기간 선택
    st.sidebar.subheader("📅 기간 선택")
    period = st.sidebar.selectbox(
        "기간",
        ["1년", "3년", "5년", "10년", "사용자 지정"],
        label_visibility="collapsed"
    )
    
    custom_start = None
    custom_end = None
    
    if period == "사용자 지정":
        col1, col2 = st.sidebar.columns(2)
        with col1:
            custom_start = st.date_input(
                "시작일",
                value=datetime.now() - timedelta(days=365)
            ).strftime('%Y-%m-%d')
        with col2:
            custom_end = st.date_input(
                "종료일",
                value=datetime.now()
            ).strftime('%Y-%m-%d')
    
    # 차트 유형 선택
    st.sidebar.subheader("📊 차트 유형")
    chart_type = st.sidebar.radio(
        "차트",
        ["매매", "전세", "매매/전세"],
        label_visibility="collapsed"
    )
    
    # 조회 버튼
    st.sidebar.markdown("---")
    query_button = st.sidebar.button("🔍 데이터 조회", type="primary", use_container_width=True)
    
    # 메인 영역
    if not selected_regions:
        st.info("👈 사이드바에서 지역을 선택하세요.")
        return
    
    if query_button:
        # 날짜 범위 계산
        start_date, end_date = calculate_date_range(period, custom_start, custom_end)
        
        # 가격 유형 결정
        if chart_type == "매매":
            price_types = ['매매']
        elif chart_type == "전세":
            price_types = ['전세']
        else:  # 매매/전세
            price_types = ['매매', '전세']
        
        # 데이터 로드
        with st.spinner("데이터를 불러오는 중..."):
            df = load_data(api_key, price_types, start_date, end_date, selected_regions)
        
        if df.empty:
            st.error("조회된 데이터가 없습니다. 기간을 조정하거나 다른 지역을 선택해보세요.")
            return
        
        # 탭 생성
        tab1, tab2, tab3 = st.tabs(["📈 차트", "📊 통계", "📋 데이터"])
        
        with tab1:
            # 차트 표시
            create_chart(df, chart_type, selected_regions)
        
        with tab2:
            # 통계 테이블
            st.subheader("주요 통계")
            create_statistics_table(df, selected_regions)
            
            # 추가 통계
            if chart_type == "매매/전세":
                st.subheader("매매/전세 비율 통계")
                
                df_pivot = df.pivot_table(
                    index=['날짜', '지역'],
                    columns='가격유형',
                    values='지수'
                ).reset_index()
                
                if '매매' in df_pivot.columns and '전세' in df_pivot.columns:
                    df_pivot['매매전세비율'] = (df_pivot['매매'] / df_pivot['전세']) * 100
                    
                    ratio_stats = []
                    for region in selected_regions:
                        region_data = df_pivot[df_pivot['지역'] == region]
                        if not region_data.empty:
                            latest_ratio = region_data.iloc[-1]['매매전세비율']
                            avg_ratio = region_data['매매전세비율'].mean()
                            max_ratio = region_data['매매전세비율'].max()
                            min_ratio = region_data['매매전세비율'].min()
                            
                            ratio_stats.append({
                                '지역': region,
                                '최근비율(%)': f"{latest_ratio:.2f}",
                                '평균비율(%)': f"{avg_ratio:.2f}",
                                '최고비율(%)': f"{max_ratio:.2f}",
                                '최저비율(%)': f"{min_ratio:.2f}"
                            })
                    
                    if ratio_stats:
                        st.dataframe(pd.DataFrame(ratio_stats), use_container_width=True, hide_index=True)
        
        with tab3:
            # 원본 데이터 표시
            st.subheader("조회 데이터")
            
            # 다운로드 버튼
            csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button(
                label="📥 CSV 다운로드",
                data=csv,
                file_name=f"price_index_{start_date}_{end_date}.csv",
                mime="text/csv"
            )
            
            # 데이터프레임 표시
            st.dataframe(df, use_container_width=True, height=400)
            
            # 데이터 요약
            st.subheader("데이터 요약")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("총 데이터 수", f"{len(df):,}건")
            with col2:
                st.metric("지역 수", f"{df['지역'].nunique()}개")
            with col3:
                st.metric("가격유형", f"{df['가격유형'].nunique()}개")
            with col4:
                st.metric("기간", f"{(df['날짜'].max() - df['날짜'].min()).days}일")
    
    else:
        # 초기 화면
        st.info("👈 사이드바에서 설정 후 '데이터 조회' 버튼을 클릭하세요.")
        
        # 사용 안내
        st.markdown("---")
        st.subheader("📖 사용 방법")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **1. 지역 선택**
            - 원하는 지역을 선택하세요
            - 전체 선택 체크박스로 모든 지역 선택 가능
            - 최소 1개 이상 선택 필요
            
            **2. 기간 선택**
            - 1년, 3년, 5년, 10년 중 선택
            - 사용자 지정으로 원하는 기간 설정 가능
            """)
        
        with col2:
            st.markdown("""
            **3. 차트 유형**
            - 매매: 매매 가격지수
            - 전세: 전세 가격지수
            - 매매/전세: 매매가격 ÷ 전세가격 비율
            
            **4. 데이터 조회**
            - '데이터 조회' 버튼 클릭
            - 차트, 통계, 데이터 탭에서 결과 확인
            """)
        
        st.markdown("---")
        st.subheader("ℹ️ 정보")
        st.markdown("""
        - **데이터 출처**: 한국 부동산원 (R-ONE)
        - **통계표 ID**: 
          - 매매: T244183132827305
          - 전세: T247713133046872
        - **주기**: 주간
        - **업데이트**: 매주 (공표 시점에 따라 최신 데이터는 1-2주 지연될 수 있음)
        """)
    
    # 푸터
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    <div style='text-align: center'>
    <small>데이터: 한국 부동산원<br>
    주간 매매/전세 가격지수</small>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
