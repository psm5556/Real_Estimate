import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from data_collector import RealEstateDataCollector

# 페이지 설정
st.set_page_config(
    page_title="한국부동산원 주간 가격지표",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stAlert {
        margin-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# 제목
st.markdown('<div class="main-header">🏠 한국부동산원 주간 가격지표 대시보드</div>', unsafe_allow_html=True)
st.markdown("---")

# 데이터 로드 함수
@st.cache_data(ttl=3600)
def load_data():
    """데이터 로드 (캐싱 적용)"""
    # API 키 확인 (Streamlit Secrets 우선)
    api_key = None
    
    # 1. Streamlit Secrets 확인
    try:
        api_key = st.secrets["API_KEY"]
    except (KeyError, FileNotFoundError):
        # 2. 환경변수 확인
        api_key = os.getenv('API_KEY')
    
    if not api_key:
        st.error("""
        ### ⚠️ API 키가 설정되지 않았습니다
        
        **Streamlit Cloud에서:**
        1. 앱 대시보드 → ⚙️ Settings → Secrets
        2. 다음 내용 추가:
        ```
        API_KEY = "your_api_key_here"
        ```
        
        **로컬 개발에서:**
        1. `.env` 파일 생성
        2. `API_KEY=your_api_key_here` 추가
        
        **API 키 발급:**
        - [한국부동산원 R-ONE](https://www.reb.or.kr/r-one) 접속
        - Open API → 인증키 발급
        """)
        return pd.DataFrame()
    
    collector = RealEstateDataCollector(api_key)
    
    # 로컬 캐시 파일 확인
    cache_file = 'data/cached_data.csv'
    use_cache = False
    
    if os.path.exists(cache_file):
        # 캐시 파일이 1시간 이내인 경우 사용
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        if (datetime.now() - file_time).seconds < 3600:
            use_cache = True
    
    if use_cache:
        st.info("📦 캐시된 데이터를 사용합니다.")
        df = pd.read_csv(cache_file)
        df['조사일'] = pd.to_datetime(df['조사일'])
    else:
        try:
            with st.spinner('API에서 데이터를 불러오는 중...'):
                # 주요 지역 데이터 수집
                sidos = ['전국', '서울', '부산', '대구', '인천', '광주', '대전', '경기']
                df = collector.fetch_multiple_regions(sidos=sidos, weeks=52)
                
                if df.empty:
                    st.warning("데이터를 불러올 수 없습니다. API 키와 연결을 확인하세요.")
                    return pd.DataFrame()
                
                # 캐시 저장
                os.makedirs('data', exist_ok=True)
                df.to_csv(cache_file, index=False, encoding='utf-8-sig')
                st.success(f"✅ 데이터 로드 완료! ({len(df)} 건)")
                
        except Exception as e:
            st.error(f"❌ 데이터 로드 실패: {str(e)}")
            st.info("API 키를 확인하거나 한국부동산원 R-ONE에서 인증키를 발급받으세요.")
            return pd.DataFrame()
    
    return df

# 데이터 로드
with st.spinner('데이터를 불러오는 중...'):
    df = load_data()

# 사이드바 - 필터링 옵션
st.sidebar.header("🔍 필터 옵션")

# 시도 선택
sido_list = ['전체'] + sorted(df['시도'].unique().tolist())
selected_sido = st.sidebar.selectbox("시도 선택", sido_list)

# 시군구 선택
if selected_sido != '전체':
    sigungu_list = ['전체'] + sorted(df[df['시도'] == selected_sido]['시군구'].unique().tolist())
else:
    sigungu_list = ['전체']
selected_sigungu = st.sidebar.selectbox("시군구 선택", sigungu_list)

# 기간 선택
st.sidebar.header("📅 조회 기간")
date_range = st.sidebar.slider(
    "조회할 주 수 선택",
    min_value=4,
    max_value=52,
    value=12,
    help="최근 몇 주간의 데이터를 조회할지 선택하세요"
)

# 지표 선택
st.sidebar.header("📊 표시 지표")
show_sale = st.sidebar.checkbox("매매가격지수", value=True)
show_jeonse = st.sidebar.checkbox("전세가격지수", value=True)

# 데이터 필터링
filtered_df = df.copy()

if selected_sido != '전체':
    filtered_df = filtered_df[filtered_df['시도'] == selected_sido]
    
if selected_sigungu != '전체':
    filtered_df = filtered_df[filtered_df['시군구'] == selected_sigungu]

# 최근 N주 데이터만 선택
max_date = filtered_df['조사일'].max()
min_date = max_date - timedelta(weeks=date_range)
filtered_df = filtered_df[filtered_df['조사일'] >= min_date]

# 대시보드 메인 영역
if filtered_df.empty:
    st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
else:
    # 주요 지표 표시
    col1, col2, col3, col4 = st.columns(4)
    
    latest_data = filtered_df[filtered_df['조사일'] == filtered_df['조사일'].max()]
    
    with col1:
        if show_sale:
            latest_sale_index = latest_data['매매가격지수'].mean()
            sale_change = latest_data['매매주간변동률'].mean()
            st.metric(
                "매매가격지수",
                f"{latest_sale_index:.2f}",
                f"{sale_change:+.3f}%",
                delta_color="normal"
            )
    
    with col2:
        if show_jeonse:
            latest_jeonse_index = latest_data['전세가격지수'].mean()
            jeonse_change = latest_data['전세주간변동률'].mean()
            st.metric(
                "전세가격지수",
                f"{latest_jeonse_index:.2f}",
                f"{jeonse_change:+.3f}%",
                delta_color="normal"
            )
    
    with col3:
        weeks_data = len(filtered_df['조사일'].unique())
        st.metric(
            "조회 기간",
            f"{weeks_data} 주",
            None
        )
    
    with col4:
        regions_count = len(filtered_df[['시도', '시군구']].drop_duplicates())
        st.metric(
            "조회 지역 수",
            f"{regions_count} 개",
            None
        )
    
    st.markdown("---")
    
    # 탭 생성
    tab1, tab2, tab3, tab4 = st.tabs(["📈 추이 그래프", "📊 변동률 분석", "🗺️ 지역별 비교", "📋 원본 데이터"])
    
    with tab1:
        st.subheader("가격지수 추이")
        
        # 시계열 그래프
        fig = go.Figure()
        
        # 지역별로 그룹화
        for region in filtered_df.groupby(['시도', '시군구']):
            region_name = f"{region[0][0]} {region[0][1]}"
            region_data = region[1].sort_values('조사일')
            
            if show_sale:
                fig.add_trace(go.Scatter(
                    x=region_data['조사일'],
                    y=region_data['매매가격지수'],
                    mode='lines+markers',
                    name=f"{region_name} - 매매",
                    line=dict(width=2)
                ))
            
            if show_jeonse:
                fig.add_trace(go.Scatter(
                    x=region_data['조사일'],
                    y=region_data['전세가격지수'],
                    mode='lines+markers',
                    name=f"{region_name} - 전세",
                    line=dict(width=2, dash='dot')
                ))
        
        fig.update_layout(
            height=500,
            xaxis_title="조사일",
            yaxis_title="가격지수",
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("주간 변동률 분석")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if show_sale:
                st.write("**매매 변동률**")
                sale_change_fig = px.bar(
                    filtered_df.sort_values('조사일'),
                    x='조사일',
                    y='매매주간변동률',
                    color='매매주간변동률',
                    color_continuous_scale=['red', 'yellow', 'green'],
                    labels={'매매주간변동률': '변동률 (%)'},
                    height=400
                )
                sale_change_fig.update_layout(showlegend=False)
                st.plotly_chart(sale_change_fig, use_container_width=True)
        
        with col2:
            if show_jeonse:
                st.write("**전세 변동률**")
                jeonse_change_fig = px.bar(
                    filtered_df.sort_values('조사일'),
                    x='조사일',
                    y='전세주간변동률',
                    color='전세주간변동률',
                    color_continuous_scale=['red', 'yellow', 'green'],
                    labels={'전세주간변동률': '변동률 (%)'},
                    height=400
                )
                jeonse_change_fig.update_layout(showlegend=False)
                st.plotly_chart(jeonse_change_fig, use_container_width=True)
        
        # 통계 요약
        st.subheader("변동률 통계")
        stats_col1, stats_col2 = st.columns(2)
        
        with stats_col1:
            if show_sale:
                st.write("**매매 변동률**")
                st.write(f"- 평균: {filtered_df['매매주간변동률'].mean():.3f}%")
                st.write(f"- 최대: {filtered_df['매매주간변동률'].max():.3f}%")
                st.write(f"- 최소: {filtered_df['매매주간변동률'].min():.3f}%")
                st.write(f"- 표준편차: {filtered_df['매매주간변동률'].std():.3f}%")
        
        with stats_col2:
            if show_jeonse:
                st.write("**전세 변동률**")
                st.write(f"- 평균: {filtered_df['전세주간변동률'].mean():.3f}%")
                st.write(f"- 최대: {filtered_df['전세주간변동률'].max():.3f}%")
                st.write(f"- 최소: {filtered_df['전세주간변동률'].min():.3f}%")
                st.write(f"- 표준편차: {filtered_df['전세주간변동률'].std():.3f}%")
    
    with tab3:
        st.subheader("지역별 가격지수 비교")
        
        # 최신 데이터로 지역 비교
        latest_comparison = filtered_df[filtered_df['조사일'] == filtered_df['조사일'].max()].copy()
        latest_comparison['지역'] = latest_comparison['시도'] + ' ' + latest_comparison['시군구']
        
        comparison_type = st.radio(
            "비교 지표 선택",
            ["매매가격지수", "전세가격지수", "매매/전세 비교"],
            horizontal=True
        )
        
        if comparison_type == "매매가격지수" and show_sale:
            fig = px.bar(
                latest_comparison.sort_values('매매가격지수', ascending=True),
                y='지역',
                x='매매가격지수',
                orientation='h',
                color='매매가격지수',
                color_continuous_scale='Blues',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
        elif comparison_type == "전세가격지수" and show_jeonse:
            fig = px.bar(
                latest_comparison.sort_values('전세가격지수', ascending=True),
                y='지역',
                x='전세가격지수',
                orientation='h',
                color='전세가격지수',
                color_continuous_scale='Greens',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
        elif comparison_type == "매매/전세 비교":
            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=latest_comparison['지역'],
                x=latest_comparison['매매가격지수'],
                name='매매',
                orientation='h',
                marker=dict(color='lightblue')
            ))
            fig.add_trace(go.Bar(
                y=latest_comparison['지역'],
                x=latest_comparison['전세가격지수'],
                name='전세',
                orientation='h',
                marker=dict(color='lightgreen')
            ))
            fig.update_layout(
                barmode='group',
                height=400,
                xaxis_title="가격지수",
                yaxis_title="지역"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.subheader("원본 데이터")
        
        # 데이터 정렬 옵션
        sort_col = st.selectbox(
            "정렬 기준",
            ['조사일', '매매가격지수', '전세가격지수', '매매주간변동률', '전세주간변동률']
        )
        sort_order = st.radio("정렬 순서", ['내림차순', '오름차순'], horizontal=True)
        
        display_df = filtered_df.sort_values(
            sort_col, 
            ascending=(sort_order == '오름차순')
        )
        
        # 데이터 표시
        st.dataframe(
            display_df.style.format({
                '매매가격지수': '{:.2f}',
                '전세가격지수': '{:.2f}',
                '매매주간변동률': '{:+.3f}%',
                '전세주간변동률': '{:+.3f}%'
            }),
            use_container_width=True,
            height=400
        )
        
        # CSV 다운로드
        csv = display_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 CSV 다운로드",
            data=csv,
            file_name=f"부동산가격지표_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

# 푸터
st.markdown("---")

# API 키 설정 상태 확인 및 안내
api_key_set = False
try:
    if st.secrets.get("API_KEY"):
        api_key_set = True
except (KeyError, FileNotFoundError):
    if os.getenv('API_KEY'):
        api_key_set = True

if not api_key_set:
    st.warning("""
        ### ⚠️ API 키를 설정하세요
        
        **Streamlit Cloud 배포 시 (권장):**
        1. 앱 대시보드에서 ⚙️ **Settings** 클릭
        2. **Secrets** 탭 선택
        3. 다음 내용 입력:
        ```toml
        API_KEY = "발급받은_인증키"
        ```
        4. **Save** 클릭
        
        **로컬 개발 시:**
        1. 프로젝트 폴더에 `.env` 파일 생성
        2. 다음 내용 입력:
        ```
        API_KEY=발급받은_인증키
        ```
        
        **API 키 발급 방법:**
        1. [한국부동산원 R-ONE](https://www.reb.or.kr/r-one) 접속
        2. 회원가입 후 로그인
        3. **Open API** → **인증키 발급** 메뉴
        4. 신청 양식 작성 및 발급
    """)
else:
    st.success("✅ API 키가 설정되었습니다.")

st.markdown("""
    <div style='text-align: center; color: gray; font-size: 0.9rem; margin-top: 2rem;'>
        <p>데이터 출처: 한국부동산원 R-ONE Open API | 업데이트: 매주 목요일</p>
    </div>
""", unsafe_allow_html=True)
