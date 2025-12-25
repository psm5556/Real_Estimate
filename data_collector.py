import pandas as pd
import requests
from datetime import datetime, timedelta
import os
from typing import Optional, Dict, List
from io import BytesIO


class RealEstateDataCollector:
    """한국부동산원 데이터 수집 클래스"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('API_KEY')
        # 공공데이터포털 파일 데이터 URL (실제 URL은 공공데이터포털에서 확인 필요)
        self.base_url = "https://www.data.go.kr/download"
        
    def generate_sample_data(self) -> pd.DataFrame:
        """샘플 데이터 생성 (테스트용)"""
        
        # 날짜 생성 (최근 52주)
        end_date = datetime.now()
        dates = [end_date - timedelta(weeks=i) for i in range(52, 0, -1)]
        
        # 주요 지역
        regions = [
            {'sido': '전국', 'sigungu': '전체'},
            {'sido': '서울', 'sigungu': '전체'},
            {'sido': '서울', 'sigungu': '강남구'},
            {'sido': '서울', 'sigungu': '서초구'},
            {'sido': '서울', 'sigungu': '송파구'},
            {'sido': '경기', 'sigungu': '전체'},
            {'sido': '경기', 'sigungu': '성남시'},
            {'sido': '경기', 'sigungu': '고양시'},
            {'sido': '인천', 'sigungu': '전체'},
            {'sido': '부산', 'sigungu': '전체'},
            {'sido': '대구', 'sigungu': '전체'},
            {'sido': '대전', 'sigungu': '전체'},
            {'sido': '광주', 'sigungu': '전체'},
        ]
        
        data = []
        
        for region in regions:
            # 기준 지수 (100 기준)
            base_index = 100
            
            # 지역별 변동성 설정
            if region['sido'] == '서울':
                trend = 0.15  # 상승 추세
                volatility = 0.3
            elif region['sido'] == '경기':
                trend = 0.12
                volatility = 0.25
            else:
                trend = 0.08
                volatility = 0.2
            
            매매_index = base_index
            전세_index = base_index
            
            for i, date in enumerate(dates):
                # 주간 변동률 생성
                import random
                random.seed(hash(f"{region['sido']}{region['sigungu']}{i}") % 10000)
                
                매매_변동 = trend + random.uniform(-volatility, volatility)
                전세_변동 = trend * 0.7 + random.uniform(-volatility, volatility)
                
                매매_index = 매매_index * (1 + 매매_변동/100)
                전세_index = 전세_index * (1 + 전세_변동/100)
                
                data.append({
                    '조사일': date.strftime('%Y-%m-%d'),
                    '시도': region['sido'],
                    '시군구': region['sigungu'],
                    '매매가격지수': round(매매_index, 2),
                    '매매주간변동률': round(매매_변동, 3),
                    '전세가격지수': round(전세_index, 2),
                    '전세주간변동률': round(전세_변동, 3),
                })
        
        df = pd.DataFrame(data)
        df['조사일'] = pd.to_datetime(df['조사일'])
        
        return df
    
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
            
            return df
        except Exception as e:
            print(f"파일 로드 중 오류 발생: {str(e)}")
            return None
    
    def fetch_data_from_api(self, 
                           start_date: str, 
                           end_date: str,
                           region_code: Optional[str] = None) -> pd.DataFrame:
        """
        공공데이터포털 API에서 데이터 가져오기
        
        Parameters:
        - start_date: 시작일 (YYYYMMDD)
        - end_date: 종료일 (YYYYMMDD)
        - region_code: 지역코드 (선택사항)
        """
        if not self.api_key:
            raise ValueError("API 키가 설정되지 않았습니다.")
        
        # 실제 API 엔드포인트는 공공데이터포털 문서 참조
        # 여기서는 예시 구조를 보여줍니다
        params = {
            'serviceKey': self.api_key,
            'startDate': start_date,
            'endDate': end_date,
            'numOfRows': 1000,
            'pageNo': 1,
            'type': 'json'
        }
        
        if region_code:
            params['regionCode'] = region_code
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            # JSON 응답 파싱 (실제 구조는 API 문서 참조)
            data = response.json()
            
            # 데이터프레임 변환
            if 'items' in data:
                df = pd.DataFrame(data['items'])
                return df
            else:
                print("데이터를 찾을 수 없습니다.")
                return pd.DataFrame()
                
        except requests.exceptions.RequestException as e:
            print(f"API 호출 중 오류 발생: {str(e)}")
            return pd.DataFrame()
    
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
    collector = RealEstateDataCollector()
    
    # 샘플 데이터 생성
    print("샘플 데이터 생성 중...")
    df = collector.generate_sample_data()
    
    # 데이터 저장
    os.makedirs('data', exist_ok=True)
    collector.save_data(df, 'data/sample_data.csv')
    
    # 통계 출력
    stats = collector.calculate_statistics(df)
    print("\n=== 데이터 통계 ===")
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print("\n데이터 샘플:")
    print(df.head(10))


if __name__ == "__main__":
    main()
