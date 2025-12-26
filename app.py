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


def date_to_week_format(date_obj: datetime) -> str:
    """
    날짜를 YYYYWW 형식으로 변환
    예: 2025-12-26 → 202552 (2025년 52주차)
    """
    year = date_obj.isocalendar()[0]  # ISO 연도
    week = date_obj.isocalendar()[1]  # ISO 주차
    return f"{year}{week:02d}"


class PriceIndexAPI:
    """부동산 가격지수 API 클래스"""
    
    BASE_URL = "https://www.reb.or.kr/r-one/openapi/SttsApiTblData.do"
    
    # 통계표 ID
    STATBL_IDS = {
        '매매': 'T244183132827305',
        '전세': 'T247713133046872'
    }
    
    CYCLE_CODE = "WK"  # 주간
    
    # 지역코드 (전체)
    REGION_CODES = {
        '전국': '50001',
        '수도권': '50002',
        '지방권': '50003',
        '6대광역시': '50004',
        '5대광역시': '50005',
        '9개도': '50006',
        '8개도': '50007',
        '서울': '50008',
        '서울>강북지역': '50009',
        '서울>강북지역>도심권': '50010',
        '서울>강북지역>동북권': '50011',
        '서울>강북지역>서북권': '50012',
        '서울>강남지역': '50013',
        '서울>강남지역>서남권': '50014',
        '서울>강남지역>동남권': '50015',
        '경기': '50016',
        '경기>경부1권': '50017',
        '경기>경부2권': '50018',
        '경기>서해안권': '50019',
        '경기>동부1권': '50020',
        '경기>동부2권': '50021',
        '경기>경의권': '50022',
        '경기>경원권': '50023',
        '부산': '50025',
        '부산>중부산권': '50026',
        '세종': '50033',
        '서울>강북지역>도심권>종로구': '50043',
        '서울>강북지역>도심권>중구': '50044',
        '서울>강북지역>도심권>용산구': '50045',
        '서울>강북지역>동북권>성동구': '50047',
        '서울>강북지역>동북권>광진구': '50048',
        '서울>강북지역>동북권>동대문구': '50049',
        '서울>강북지역>동북권>중랑구': '50050',
        '서울>강북지역>동북권>성북구': '50051',
        '서울>강북지역>동북권>강북구': '50052',
        '서울>강북지역>동북권>도봉구': '50053',
        '서울>강북지역>동북권>노원구': '50054',
        '서울>강북지역>서북권>은평구': '50056',
        '서울>강북지역>서북권>서대문구': '50057',
        '서울>강북지역>서북권>마포구': '50058',
        '서울>강남지역>서남권>양천구': '50060',
        '서울>강남지역>서남권>강서구': '50061',
        '서울>강남지역>서남권>구로구': '50062',
        '서울>강남지역>서남권>금천구': '50063',
        '서울>강남지역>서남권>영등포구': '50064',
        '서울>강남지역>서남권>동작구': '50065',
        '서울>강남지역>서남권>관악구': '50066',
        '서울>강남지역>동남권>서초구': '50067',
        '서울>강남지역>동남권>강남구': '50068',
        '서울>강남지역>동남권>송파구': '50069',
        '서울>강남지역>동남권>강동구': '50070',
        '경기>경부1권>과천시': '50071',
        '경기>경부1권>안양시': '50072',
        '경기>경부1권>안양시>만안구': '50073',
        '경기>경부1권>안양시>동안구': '50074',
        '경기>경부1권>군포시': '50075',
        '경기>경부1권>의왕시': '50076',
        '경기>경부1권>성남시': '50077',
        '경기>경부1권>성남시>수정구': '50078',
        '경기>경부1권>성남시>중원구': '50079',
        '경기>경부1권>성남시>분당구': '50080',
        '경기>경부2권>안성시': '50081',
        '경기>경부2권>수원시': '50083',
        '경기>경부2권>수원시>장안구': '50084',
        '경기>경부2권>수원시>권선구': '50085',
        '경기>경부2권>수원시>팔달구': '50086',
        '경기>경부2권>수원시>영통구': '50087',
        '경기>경부2권>용인시': '50088',
        '경기>경부2권>용인시>처인구': '50089',
        '경기>경부2권>용인시>기흥구': '50090',
        '경기>경부2권>용인시>수지구': '50091',
        '경기>서해안권>부천시': '50093',
        '경기>서해안권>부천시>원미구': '50094',
        '경기>서해안권>부천시>소사구': '50095',
        '경기>서해안권>부천시>오정구': '50096',
        '경기>서해안권>광명시': '50097',
        '경기>서해안권>평택시': '50098',
        '경기>서해안권>안산시': '50099',
        '경기>서해안권>안산시>상록구': '50100',
        '경기>서해안권>안산시>단원구': '50101',
        '경기>서해안권>오산시': '50102',
        '경기>서해안권>시흥시': '50103',
        '경기>서해안권>화성시': '50104',
        '경기>동부1권>구리시': '50106',
        '경기>동부1권>남양주시': '50107',
        '경기>동부1권>하남시': '50108',
        '경기>동부1권>광주시': '50109',
        '경기>동부2권>이천시': '50111',
        '경기>동부2권>여주시': '50112',
        '경기>경의권>고양시': '50114',
        '경기>경의권>고양시>덕양구': '50115',
        '경기>경의권>고양시>일산동구': '50116',
        '경기>경의권>고양시>일산서구': '50117',
        '경기>경의권>김포시': '50118',
        '경기>경원권>의정부시': '50120',
        '경기>경원권>동두천시': '50121',
        '경기>경원권>양주시': '50122',
        '경기>경원권>포천시': '50123',
        '인천': '50124',
        '인천>중구': '50125',
        '인천>동구': '50126',
        '인천>연수구': '50127',
        '인천>남동구': '50128',
        '인천>부평구': '50129',
        '인천>계양구': '50130',
        '인천>서구': '50131',
        '부산>중부산권>중구': '50132',
        '부산>중부산권>서구': '50133',
        '부산>중부산권>동구': '50134',
        '부산>중부산권>영도구': '50135',
        '부산>중부산권>남구': '50136',
        '부산>중부산권>부산진구': '50137',
        '부산>중부산권>연제구': '50138',
        '부산>중부산권>수영구': '50139',
        '부산>동부산권': '50140',
        '부산>동부산권>동래구': '50141',
        '부산>동부산권>해운대구': '50142',
        '부산>동부산권>금정구': '50143',
        '부산>동부산권>기장군': '50144',
        '부산>서부산권': '50145',
        '부산>서부산권>북구': '50146',
        '부산>서부산권>사하구': '50147',
        '부산>서부산권>강서구': '50148',
        '부산>서부산권>사상구': '50149',
        '대구': '50150',
        '대구>중구': '50151',
        '대구>동구': '50152',
        '대구>서구': '50153',
        '대구>남구': '50154',
        '대구>북구': '50155',
        '대구>수성구': '50156',
        '대구>달서구': '50157',
        '대구>달성군': '50158',
        '광주': '50159',
        '광주>동구': '50160',
        '광주>서구': '50161',
        '광주>남구': '50162',
        '광주>북구': '50163',
        '광주>광산구': '50164',
        '대전': '50165',
        '대전>동구': '50166',
        '대전>중구': '50167',
        '대전>서구': '50168',
        '대전>유성구': '50169',
        '대전>대덕구': '50170',
        '울산': '50171',
        '울산>중구': '50172',
        '울산>남구': '50173',
        '울산>동구': '50174',
        '울산>북구': '50175',
        '울산>울주군': '50176',
        '강원': '50177',
        '강원>춘천시': '50178',
        '강원>원주시': '50179',
        '강원>강릉시': '50180',
        '강원>동해시': '50181',
        '강원>태백시': '50182',
        '강원>속초시': '50183',
        '강원>삼척시': '50184',
        '충북': '50185',
        '충북>청주시': '50186',
        '충북>청주시>상당구': '50187',
        '충북>청주시>서원구': '50188',
        '충북>청주시>흥덕구': '50189',
        '충북>청주시>청원구': '50190',
        '충북>충주시': '50191',
        '충북>제천시': '50192',
        '충북>음성군': '50193',
        '충남': '50194',
        '충남>천안시': '50195',
        '충남>천안시>동남구': '50196',
        '충남>천안시>서북구': '50197',
        '충남>공주시': '50198',
        '충남>보령시': '50199',
        '충남>아산시': '50200',
        '충남>서산시': '50201',
        '충남>논산시': '50202',
        '충남>계룡시': '50203',
        '충남>당진시': '50204',
        '충남>홍성군': '50205',
        '충남>예산군': '50206',
        '전북': '50207',
        '전북>전주시': '50208',
        '전북>전주시>완산구': '50209',
        '전북>전주시>덕진구': '50210',
        '전북>군산시': '50211',
        '전북>익산시': '50212',
        '전북>정읍시': '50213',
        '전북>남원시': '50214',
        '전북>김제시': '50215',
        '전남': '50216',
        '전남>목포시': '50217',
        '전남>여수시': '50218',
        '전남>순천시': '50219',
        '전남>나주시': '50220',
        '전남>광양시': '50221',
        '전남>무안군': '50222',
        '경북': '50223',
        '경북>포항시': '50224',
        '경북>포항시>남구': '50225',
        '경북>포항시>북구': '50226',
        '경북>경주시': '50227',
        '경북>김천시': '50228',
        '경북>안동시': '50229',
        '경북>구미시': '50230',
        '경북>영주시': '50231',
        '경북>영천시': '50232',
        '경북>상주시': '50233',
        '경북>문경시': '50234',
        '경북>경산시': '50235',
        '경북>칠곡군': '50236',
        '경남': '50237',
        '경남>창원시': '50238',
        '경남>창원시>의창구': '50239',
        '경남>창원시>성산구': '50240',
        '경남>창원시>마산합포구': '50241',
        '경남>창원시>마산회원구': '50242',
        '경남>창원시>진해구': '50243',
        '경남>통영시': '50244',
        '경남>사천시': '50245',
        '경남>김해시': '50246',
        '경남>밀양시': '50247',
        '경남>거제시': '50248',
        '경남>양산시': '50249',
        '제주': '50250',
        '제주>제주시': '50251',
        '제주>서귀포시': '50252',
        '경기>경의권>파주시': '50253',
        '인천>미추홀구': '50254',
        '경남>진주시': '50255',
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
            start_date: 시작 주차 (YYYYWW 형식, 예: 202401 = 2024년 1주차)
            end_date: 종료 주차 (YYYYWW 형식, 예: 202452 = 2024년 52주차)
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
            'pSize': 1000,  # 최대 1000개 (1년 = 52주, 여유있게)
            'CLS_ID': region_code,
        }
        
        # 디버그: 실제 요청 파라미터 출력
        if st.session_state.get('show_debug', False):
            st.write(f"🔍 API 요청: {price_type}, 지역코드: {region_code}")
            st.write(f"   시작: {start_date}, 종료: {end_date}")
        
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
            
            # 주간 데이터 처리
            # WRTTIME_DESC가 실제 날짜 (YYYY-MM-DD 형식)
            if 'WRTTIME_DESC' in df.columns:
                df['날짜'] = pd.to_datetime(df['WRTTIME_DESC'], format='%Y-%m-%d', errors='coerce')
            elif 'WRTTIME_IDTFR_ID' in df.columns:
                # WRTTIME_DESC가 없으면 WRTTIME_IDTFR_ID 사용
                df['날짜'] = pd.to_datetime(df['WRTTIME_IDTFR_ID'], format='%Y%m%d', errors='coerce')
            
            # 숫자 변환
            if 'DTA_VAL' in df.columns:
                df['지수'] = pd.to_numeric(df['DTA_VAL'], errors='coerce')
            
            # 필요한 컬럼만 선택
            result_df = df[['날짜', '지수']].copy()
            result_df['가격유형'] = price_type
            
            # 날짜로 정렬
            result_df = result_df.sort_values('날짜').reset_index(drop=True)
            
            # 결측값 제거
            result_df = result_df.dropna(subset=['날짜', '지수'])
            
            return result_df
            
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
    
    # YYYYWW 형식으로 변환 (년도 + 주차)
    start_str = date_to_week_format(start_date)
    end_str = date_to_week_format(end_date)
    
    return start_str, end_str


def create_chart(df: pd.DataFrame, chart_type: str, regions: List[str], normalize: bool = False):
    """차트 생성"""
    
    if df.empty:
        st.warning("표시할 데이터가 없습니다.")
        return
    
    # 보정 처리
    if normalize:
        # 2022년 1월 31일에 해당하는 주차 계산
        base_date = datetime(2022, 1, 31)
        base_week = date_to_week_format(base_date)  # 202205 형식
        
        # 기준일 데이터로 정규화
        df_normalized = df.copy()
        
        for region in regions:
            for price_type in df['가격유형'].unique():
                mask = (df_normalized['지역'] == region) & (df_normalized['가격유형'] == price_type)
                region_data = df_normalized[mask].copy()
                
                if not region_data.empty:
                    # 2022-01-31에 가장 가까운 날짜 찾기
                    region_data['날짜_diff'] = abs((region_data['날짜'] - base_date).dt.days)
                    base_idx = region_data['날짜_diff'].idxmin()
                    base_value = region_data.loc[base_idx, '지수']
                    
                    if base_value and base_value > 0:
                        # 100 기준으로 정규화
                        df_normalized.loc[mask, '지수'] = (df_normalized.loc[mask, '지수'] / base_value) * 100
        
        df = df_normalized
    
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
                    name=f"{region}",
                    line=dict(width=2),
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                  '날짜: %{x|%Y-%m-%d}<br>' +
                                  ('지수: %{y:.2f}' if normalize else '지수: %{y:.2f}') +
                                  '<extra></extra>'
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
                    name=f"{region}",
                    line=dict(width=2),
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                  '날짜: %{x|%Y-%m-%d}<br>' +
                                  ('지수: %{y:.2f}' if normalize else '지수: %{y:.2f}') +
                                  '<extra></extra>'
                ))
    
    elif chart_type == "매매/전세":
        # 매매와 전세를 동시에 표시
        for region in regions:
            # 매매 데이터
            df_sale = df[(df['지역'] == region) & (df['가격유형'] == '매매')]
            if not df_sale.empty:
                fig.add_trace(go.Scatter(
                    x=df_sale['날짜'],
                    y=df_sale['지수'],
                    mode='lines',
                    name=f"{region} 매매",
                    line=dict(width=2, dash='solid'),
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                  '날짜: %{x|%Y-%m-%d}<br>' +
                                  ('지수: %{y:.2f}' if normalize else '지수: %{y:.2f}') +
                                  '<extra></extra>'
                ))
            
            # 전세 데이터
            df_jeonse = df[(df['지역'] == region) & (df['가격유형'] == '전세')]
            if not df_jeonse.empty:
                fig.add_trace(go.Scatter(
                    x=df_jeonse['날짜'],
                    y=df_jeonse['지수'],
                    mode='lines',
                    name=f"{region} 전세",
                    line=dict(width=2, dash='dot'),
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                  '날짜: %{x|%Y-%m-%d}<br>' +
                                  ('지수: %{y:.2f}' if normalize else '지수: %{y:.2f}') +
                                  '<extra></extra>'
                ))
    
    # 레이아웃 설정
    if chart_type == "매매/전세":
        title = "매매/전세 가격지수 비교"
    else:
        title = f"{chart_type} 가격지수 추이"
    
    if normalize:
        title += " (2022-01-31 = 100 기준)"
        yaxis_title = "정규화 지수 (2022-01-31 = 100)"
    else:
        yaxis_title = "지수"
    
    fig.update_layout(
        title=title,
        xaxis_title="날짜 (주간)",
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


def create_heatmap(df: pd.DataFrame, regions: List[str], chart_type: str, mode: str = "누적 변화율"):
    """지역별 시계열 증감률 히트맵"""
    
    if df.empty:
        st.warning("히트맵을 그릴 데이터가 없습니다.")
        return
    
    # 차트 유형에 따라 데이터 필터링
    if chart_type == "매매":
        df_filtered = df[df['가격유형'] == '매매'].copy()
        title_suffix = "매매 가격지수"
    elif chart_type == "전세":
        df_filtered = df[df['가격유형'] == '전세'].copy()
        title_suffix = "전세 가격지수"
    else:  # 매매/전세
        # 매매와 전세 각각 히트맵 생성
        for price_type, suffix in [('매매', '매매 가격지수'), ('전세', '전세 가격지수')]:
            df_type = df[df['가격유형'] == price_type].copy()
            if not df_type.empty:
                _create_single_heatmap(df_type, regions, f"{suffix} 시계열 히트맵", mode)
        return
    
    _create_single_heatmap(df_filtered, regions, f"{title_suffix} 시계열 히트맵", mode)


def _create_single_heatmap(df: pd.DataFrame, regions: List[str], title: str, mode: str = "누적 변화율"):
    """단일 히트맵 생성 (내부 함수)"""
    
    if df.empty:
        st.warning("히트맵을 그릴 데이터가 없습니다.")
        return
    
    # 각 지역의 데이터 처리
    heatmap_data = []
    
    for region in regions:
        region_data = df[df['지역'] == region].sort_values('날짜')
        
        if not region_data.empty and len(region_data) > 0:
            region_data = region_data.copy()
            
            if mode == "누적 변화율":
                # 최초 지수 대비 변화율
                base_index = region_data.iloc[0]['지수']
                
                if base_index and base_index > 0:
                    region_data['변화율'] = ((region_data['지수'] - base_index) / base_index) * 100
                    region_data['지역'] = region
                    heatmap_data.append(region_data[['날짜', '지역', '변화율']])
            
            else:  # 전주 변동률
                # 전주 대비 변동률 계산
                region_data['변화율'] = region_data['지수'].pct_change() * 100
                region_data['지역'] = region
                # 첫 번째 값은 NaN이므로 0으로 처리
                region_data['변화율'] = region_data['변화율'].fillna(0)
                heatmap_data.append(region_data[['날짜', '지역', '변화율']])
    
    if not heatmap_data:
        st.warning("히트맵을 그릴 데이터가 없습니다.")
        return
    
    # 데이터 결합
    combined_df = pd.concat(heatmap_data, ignore_index=True)
    
    # 피벗 테이블 생성: 날짜(x축) x 지역(y축)
    pivot_df = combined_df.pivot(index='지역', columns='날짜', values='변화율')
    
    # 지역 순서 유지
    pivot_df = pivot_df.reindex(regions)
    
    # 데이터 포인트 수 표시
    total_weeks = len(pivot_df.columns)
    
    if mode == "누적 변화율":
        mode_text = "최초 시점 대비"
        st.info(f"📅 총 {total_weeks}주 데이터 표시 중 (최초 시점 대비 누적 변화율)")
        zmin, zmax = -10, 10
        colorbar_title = "누적 변화율(%)"
    else:  # 전주 변동률
        mode_text = "전주 대비"
        st.info(f"📅 총 {total_weeks}주 데이터 표시 중 (전주 대비 변동률)")
        zmin, zmax = -1, 1  # 전주 변동률은 -1% ~ +1%
        colorbar_title = "전주 변동률(%)"
    
    # 히트맵 생성
    fig = go.Figure(data=go.Heatmap(
        z=pivot_df.values,
        x=pivot_df.columns,
        y=pivot_df.index,
        colorscale='RdYlGn',  # 빨강(하락)-노랑(중립)-초록(상승)
        zmid=0,  # 0을 중간값으로
        colorbar=dict(title=colorbar_title),
        hovertemplate='지역: %{y}<br>날짜: %{x|%Y-%m-%d}<br>' + colorbar_title + ': %{z:.2f}%<extra></extra>',
        zmin=zmin,
        zmax=zmax,
    ))
    
    # x축 틱 간격 계산 (주 수에 따라 조정)
    if total_weeks <= 12:
        dtick = 7 * 24 * 60 * 60 * 1000  # 1주마다
    elif total_weeks <= 52:
        dtick = 7 * 24 * 60 * 60 * 1000 * 4  # 4주마다
    else:
        dtick = 7 * 24 * 60 * 60 * 1000 * 8  # 8주마다
    
    fig.update_layout(
        title=f"{title} ({mode_text})",
        xaxis_title="날짜 (주간)",
        yaxis_title="지역",
        height=max(400, len(regions) * 25),  # 지역 수에 따라 높이 조정
        xaxis={
            'tickformat': '%Y-%m-%d',
            'tickangle': -45,
            'dtick': dtick
        },
        margin=dict(l=200, r=50, t=80, b=100)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def main():
    """메인 함수"""
    
    # 타이틀
    st.title("🏠 부동산 가격지수 대시보드")
    st.markdown("한국 부동산원 주간 매매/전세 가격지수")
    
    # 현재 날짜 표시
    current_date = datetime.now()
    st.caption(f"📅 오늘 날짜: {current_date.strftime('%Y년 %m월 %d일 (%A)')}")
    
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
            default=[
                '서울',
                '경기',
                '서울>강남지역',
                '서울>강북지역',
                '경기>경부1권>성남시>분당구',
                '경기>경부2권>수원시>영통구',
                '경기>경부2권>용인시>수지구',
                '경기>서해안권>평택시',
                '인천>연수구',
                '부산>동부산권>해운대구'
            ],
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
            default_start = datetime(2013, 8, 5)  # 2013년 8월 5일
            custom_start = st.date_input(
                "시작일",
                value=default_start,
                max_value=datetime.now()
            ).strftime('%Y-%m-%d')
        with col2:
            custom_end = st.date_input(
                "종료일",
                value=datetime.now(),
                max_value=datetime.now()
            ).strftime('%Y-%m-%d')
    
    # 차트 유형 선택
    st.sidebar.subheader("📊 차트 유형")
    chart_type = st.sidebar.radio(
        "차트",
        ["매매", "전세", "매매/전세"],
        label_visibility="collapsed"
    )
    
    # 보정 옵션
    st.sidebar.subheader("⚙️ 차트 옵션")
    normalize_base = st.sidebar.checkbox(
        "📐 기준일 보정 (2022-01-31 = 100)",
        value=False,
        help="2022년 1월 31일을 100으로 설정하여 지역간 비교를 용이하게 합니다."
    )
    
    # 히트맵 옵션
    st.sidebar.subheader("🔥 히트맵 옵션")
    heatmap_mode = st.sidebar.radio(
        "히트맵 표시 방식",
        ["누적 변화율", "전주 변동률"],
        label_visibility="collapsed",
        help="누적: 최초 대비 변화율 / 전주: 전주 대비 변동률"
    )
    
    # 조회 버튼
    st.sidebar.markdown("---")
    
    # 현재 설정 미리보기
    if selected_regions:
        preview_end = datetime.now()
        if period == "1년":
            preview_start = preview_end - timedelta(days=365)
        elif period == "3년":
            preview_start = preview_end - timedelta(days=365*3)
        elif period == "5년":
            preview_start = preview_end - timedelta(days=365*5)
        elif period == "10년":
            preview_start = preview_end - timedelta(days=365*10)
        elif period == "사용자 지정" and custom_start and custom_end:
            preview_start = datetime.strptime(custom_start, '%Y-%m-%d')
            preview_end = datetime.strptime(custom_end, '%Y-%m-%d')
        else:
            preview_start = preview_end - timedelta(days=365)
        
        st.sidebar.info(f"""
        📅 **조회 기간**  
        {preview_start.strftime('%Y-%m-%d')} ~ {preview_end.strftime('%Y-%m-%d')}  
        ({(preview_end - preview_start).days}일)
        
        📍 **선택 지역**: {len(selected_regions)}개  
        📊 **차트**: {chart_type}
        """)
    
    query_button = st.sidebar.button("🔍 데이터 조회", type="primary", use_container_width=True)
    
    # 메인 영역
    if not selected_regions:
        st.info("👈 사이드바에서 지역을 선택하세요.")
        return
    
    if query_button:
        # 날짜 범위 계산
        start_date, end_date = calculate_date_range(period, custom_start, custom_end)
        
        # 주차를 날짜로 변환해서 표시 (YYYYWW → 년도, 주차)
        start_year = int(start_date[:4])
        start_week = int(start_date[4:])
        end_year = int(end_date[:4])
        end_week = int(end_date[4:])
        
        # 날짜 확인용 메시지
        st.success(f"""
        ✅ **데이터 조회 시작**  
        📅 기간: {start_year}년 {start_week}주차 ~ {end_year}년 {end_week}주차  
        🔢 API 파라미터: START={start_date}, END={end_date}  
        📍 지역: {len(selected_regions)}개 ({', '.join(selected_regions[:3])}{'...' if len(selected_regions) > 3 else ''})  
        📊 유형: {chart_type}
        """)
        
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
        
        # 데이터 정보 표시
        with st.expander("📊 데이터 조회 정보", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("총 데이터", f"{len(df):,}건")
            with col2:
                st.metric("지역 수", f"{df['지역'].nunique()}개")
            with col3:
                date_range = (df['날짜'].max() - df['날짜'].min()).days
                st.metric("기간", f"{date_range}일")
            with col4:
                weeks = len(df) // (df['지역'].nunique() * df['가격유형'].nunique())
                st.metric("주차", f"약 {weeks}주")
            
            # 지역별 데이터 수
            st.write("**지역별 데이터 수:**")
            region_counts = df.groupby(['지역', '가격유형']).size().unstack(fill_value=0)
            st.dataframe(region_counts, use_container_width=True)
        
        # 탭 생성
        tab1, tab2, tab3 = st.tabs(["📈 차트", "📊 통계", "📋 데이터"])
        
        with tab1:
            # 차트 표시
            create_chart(df, chart_type, selected_regions, normalize_base)
        
        with tab2:
            # 증감률 히트맵만 표시
            st.subheader("시계열 증감률 히트맵")
            if heatmap_mode == "누적 변화율":
                st.info("📊 최초 시점 대비 각 시점의 변화율을 색상으로 표시합니다. (빨강: 하락, 초록: 상승)")
            else:
                st.info("📊 전주 대비 변동률을 색상으로 표시합니다. (빨강: 하락, 초록: 상승)")
            create_heatmap(df, selected_regions, chart_type, heatmap_mode)
        
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
            - 매매: 매매 가격지수만 표시
            - 전세: 전세 가격지수만 표시
            - 매매/전세: 매매와 전세 동시 표시 (실선/점선)
            
            **4. 데이터 조회**
            - '데이터 조회' 버튼 클릭
            - 차트, 통계, 데이터 탭에서 결과 확인
            - 통계 탭에서 히트맵으로 증감률 비교
            """)
        
        st.markdown("---")
        st.subheader("ℹ️ 정보")
        st.markdown("""
        - **데이터 출처**: 한국 부동산원 (R-ONE)
        - **통계표 ID**: 
          - 매매: T244183132827305
          - 전세: T247713133046872
        - **주기**: 주간 (WK) - 매주 월요일 기준
        - **지역 수**: 총 256개 지역
        - **업데이트**: 매주 (공표 시점에 따라 최신 데이터는 1-2주 지연될 수 있음)
        
        **주간 데이터 특성**:
        - 각 데이터는 해당 주의 월요일 기준으로 표시됩니다
        - 실제 공표일과 차트 표시 날짜는 다를 수 있습니다
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
