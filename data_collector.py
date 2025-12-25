import pandas as pd
import requests
from datetime import datetime, timedelta
import os
from typing import Optional, Dict, List
import xml.etree.ElementTree as ET
import json


class RealEstateDataCollector:
    """한국부동산원 데이터 수집 클래스"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        초기화
        
        API 키 우선순위:
        1. 직접 전달된 api_key
        2. Streamlit Secrets (st.secrets.API_KEY)
        3. 환경변수 (.env 파일 또는 시스템 환경변수)
        """
        if api_key:
            self.api_key = api_key
        else:
            # Streamlit Secrets 확인
            try:
                import streamlit as st
                self.api_key = st.secrets.get("API_KEY", None)
            except (ImportError, FileNotFoundError, AttributeError):
                # Streamlit이 없거나 secrets가 없는 경우 환경변수 사용
                self.api_key = os.getenv('API_KEY')
        
        # 한국부동산원 R-ONE Open API 기본 URL
        self.base_url = "https://api.reb.or.kr/r-one/openapi"
        
        # 시도 코드 매핑
        self.sido_codes = {
            '전국': '00',
            '서울': '11',
            '부산': '26',
            '대구': '27',
            '인천': '28',
            '광주': '29',
            '대전': '30',
            '울산': '31',
            '세종': '36',
            '경기': '41',
            '강원': '42',
            '충북': '43',
            '충남': '44',
            '전북': '45',
            '전남': '46',
            '경북': '47',
            '경남': '48',
            '제주': '50'
        }
    
    def fetch_weekly_price_index(self, 
                                 sido: str = '전국',
                                 weeks: int = 12) -> pd.DataFrame:
        """
        주간 아파트 가격지수 조회
        
        Parameters:
        - sido: 시도명 (예: '서울', '부산', '전국')
        - weeks: 조회할 주 수 (기본 12주)
        
        Returns:
        - DataFrame: 주간 가격지수 데이터
        """
        if not self.api_key:
            raise ValueError("API 키가 필요합니다. .env 파일에 API_KEY를 설정하거나 초기화시 전달하세요.")
        
        # 조회 기간 설정
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks)
        
        # 시도 코드 가져오기
        sido_code = self.sido_codes.get(sido, '00')
        
        all_data = []
        
        # 주간 데이터는 보통 매주 목요일 기준으로 발표
        # 각 주차별로 데이터 수집
        current_date = start_date
        while current_date <= end_date:
            try:
                # 주간 데이터 조회
                weekly_data = self._fetch_single_week_data(
                    sido_code=sido_code,
                    date=current_date
                )
                
                if weekly_data:
                    all_data.extend(weekly_data)
                
                # 1주일씩 증가
                current_date += timedelta(weeks=1)
                
            except Exception as e:
                print(f"데이터 조회 중 오류 ({current_date.strftime('%Y-%m-%d')}): {str(e)}")
                current_date += timedelta(weeks=1)
                continue
        
        if not all_data:
            print("조회된 데이터가 없습니다. API 키와 네트워크를 확인하세요.")
            return pd.DataFrame()
        
        # DataFrame 변환
        df = pd.DataFrame(all_data)
        df['조사일'] = pd.to_datetime(df['조사일'])
        
        return df
    
    def _fetch_single_week_data(self, sido_code: str, date: datetime) -> List[Dict]:
        """
        특정 주의 데이터 조회 (내부 메서드)
        """
        # API 엔드포인트 (실제 엔드포인트는 한국부동산원 문서 참조)
        endpoint = f"{self.base_url}/weeklyHousingPrice"
        
        # 파라미터 설정
        params = {
            'serviceKey': self.api_key,
            'sidoCode': sido_code,
            'inqDate': date.strftime('%Y%m%d'),
            'numOfRows': 100,
            'pageNo': 1,
            'type': 'json'  # json 또는 xml
        }
        
        try:
            response = requests.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            
            # JSON 응답 파싱
            data = response.json()
            
            # 응답 구조는 API 문서에 따라 다를 수 있음
            # 일반적인 공공데이터 포털 구조 가정
            if 'response' in data:
                items = data['response'].get('body', {}).get('items', {}).get('item', [])
                
                # item이 단일 딕셔너리인 경우 리스트로 변환
                if isinstance(items, dict):
                    items = [items]
                
                # 데이터 변환
                processed_items = []
                for item in items:
                    processed_items.append({
                        '조사일': date.strftime('%Y-%m-%d'),
                        '시도': self._get_sido_name(item.get('sidoCode', sido_code)),
                        '시군구': item.get('sigunguName', '전체'),
                        '매매가격지수': float(item.get('saleIndex', 0)),
                        '매매주간변동률': float(item.get('saleChangeRate', 0)),
                        '전세가격지수': float(item.get('jeonseIndex', 0)),
                        '전세주간변동률': float(item.get('jeonseChangeRate', 0)),
                    })
                
                return processed_items
            
            return []
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API 호출 실패: {str(e)}")
        except (KeyError, ValueError) as e:
            raise Exception(f"응답 데이터 파싱 실패: {str(e)}")
    
    def _get_sido_name(self, sido_code: str) -> str:
        """시도 코드로 시도명 찾기"""
        for name, code in self.sido_codes.items():
            if code == sido_code:
                return name
        return '알수없음'
    
    def fetch_multiple_regions(self, 
                              sidos: List[str] = None,
                              weeks: int = 12) -> pd.DataFrame:
        """
        여러 지역의 데이터 한번에 조회
        
        Parameters:
        - sidos: 시도 리스트 (None인 경우 전국 데이터만 조회)
        - weeks: 조회할 주 수
        
        Returns:
        - DataFrame: 통합된 가격지수 데이터
        """
        if sidos is None:
            sidos = ['전국']
        
        all_dataframes = []
        
        for sido in sidos:
            print(f"{sido} 데이터 조회 중...")
            try:
                df = self.fetch_weekly_price_index(sido=sido, weeks=weeks)
                if not df.empty:
                    all_dataframes.append(df)
            except Exception as e:
                print(f"{sido} 조회 실패: {str(e)}")
                continue
        
        if not all_dataframes:
            print("조회된 데이터가 없습니다.")
            return pd.DataFrame()
        
        # 모든 데이터 통합
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        combined_df = combined_df.sort_values(['조사일', '시도', '시군구'])
        
        return combined_df
    
    def fetch_data_from_file(self, file_path: str) -> pd.DataFrame:
        """
        로컬 파일에서 데이터 로드
        공공데이터포털에서 다운로드한 파일 사용
        """
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8-sig')
            elif file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            else:
                raise ValueError("지원하지 않는 파일 형식입니다. CSV 또는 XLSX 파일을 사용하세요.")
            
            # 날짜 컬럼 변환
            if '조사일' in df.columns:
                df['조사일'] = pd.to_datetime(df['조사일'])
            
            return df
        except Exception as e:
            print(f"파일 로드 중 오류 발생: {str(e)}")
            return None
    
    def test_api_connection(self) -> bool:
        """API 연결 테스트"""
        if not self.api_key:
            print("❌ API 키가 설정되지 않았습니다.")
            return False
        
        try:
            # 간단한 테스트 요청
            df = self.fetch_weekly_price_index(sido='전국', weeks=1)
            if not df.empty:
                print("✅ API 연결 성공!")
                return True
            else:
                print("⚠️ API 연결은 되었으나 데이터가 없습니다.")
                return False
        except Exception as e:
            print(f"❌ API 연결 실패: {str(e)}")
            return False
    
    def save_data(self, df: pd.DataFrame, file_path: str):
        """데이터를 파일로 저장"""
        try:
            if file_path.endswith('.csv'):
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
            elif file_path.endswith('.xlsx'):
                df.to_excel(file_path, index=False)
            print(f"데이터가 {file_path}에 저장되었습니다.")
        except Exception as e:
            print(f"파일 저장 중 오류 발생: {str(e)}")
    
    def get_region_list(self) -> List[str]:
        """지역 목록 반환"""
        return [
            '전국', '서울', '부산', '대구', '인천', '광주', 
            '대전', '울산', '세종', '경기', '강원', '충북',
            '충남', '전북', '전남', '경북', '경남', '제주'
        ]
    
    def calculate_statistics(self, df: pd.DataFrame) -> Dict:
        """데이터 통계 계산"""
        if df.empty:
            return {}
        
        stats = {
            '전체_데이터_수': len(df),
            '조사_기간': f"{df['조사일'].min()} ~ {df['조사일'].max()}",
            '평균_매매변동률': df['매매주간변동률'].mean(),
            '평균_전세변동률': df['전세주간변동률'].mean(),
            '최대_상승_지역': df.loc[df['매매주간변동률'].idxmax(), '시도'],
            '최대_하락_지역': df.loc[df['매매주간변동률'].idxmin(), '시도'],
        }
        
        return stats


def main():
    """테스트 코드"""
    print("=== 한국부동산원 데이터 수집기 테스트 ===\n")
    
    # API 키 확인
    api_key = os.getenv('API_KEY')
    if not api_key:
        print("⚠️  API 키가 설정되지 않았습니다.")
        print("📝 .env 파일에 API_KEY를 설정하거나 환경변수를 설정하세요.")
        print("\n사용 예시:")
        print("1. .env 파일 생성:")
        print("   API_KEY=your_api_key_here")
        print("\n2. 환경변수 설정:")
        print("   export API_KEY=your_api_key_here  # Linux/Mac")
        print("   set API_KEY=your_api_key_here     # Windows")
        return
    
    collector = RealEstateDataCollector(api_key)
    
    # API 연결 테스트
    print("1. API 연결 테스트")
    print("-" * 50)
    collector.test_api_connection()
    
    # 데이터 수집
    print("\n2. 데이터 수집 (전국, 최근 4주)")
    print("-" * 50)
    try:
        df = collector.fetch_weekly_price_index(sido='전국', weeks=4)
        
        if not df.empty:
            print(f"✅ 데이터 수집 성공! ({len(df)}개 레코드)")
            
            # 데이터 저장
            os.makedirs('data', exist_ok=True)
            collector.save_data(df, 'data/real_estate_data.csv')
            
            # 통계 출력
            stats = collector.calculate_statistics(df)
            print("\n=== 데이터 통계 ===")
            for key, value in stats.items():
                print(f"{key}: {value}")
            
            print("\n=== 데이터 샘플 ===")
            print(df.head(10))
        else:
            print("⚠️  데이터가 조회되지 않았습니다.")
            print("API 키 또는 엔드포인트를 확인하세요.")
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        print("\n문제 해결:")
        print("1. API 키가 올바른지 확인하세요")
        print("2. 한국부동산원 R-ONE에서 인증키를 발급받으셨는지 확인하세요")
        print("3. 네트워크 연결을 확인하세요")


if __name__ == "__main__":
    main()
