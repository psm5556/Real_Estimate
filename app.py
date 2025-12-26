"""
날짜 계산 로직 테스트 (YYYYWW 형식)
"""

from datetime import datetime, timedelta

def date_to_week_format(date_obj):
    """날짜를 YYYYWW 형식으로 변환"""
    year = date_obj.isocalendar()[0]  # ISO 연도
    week = date_obj.isocalendar()[1]  # ISO 주차
    return f"{year}{week:02d}"


def calculate_date_range(period: str, custom_start=None, custom_end=None):
    """기간에 따른 날짜 범위 계산"""
    end_date = datetime.now()
    
    print(f"현재 날짜: {end_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"선택 기간: {period}")
    
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
    
    # YYYYWW 형식으로 변환
    start_str = date_to_week_format(start_date)
    end_str = date_to_week_format(end_date)
    
    # ISO 주차 정보
    start_iso = start_date.isocalendar()
    end_iso = end_date.isocalendar()
    
    print(f"\n계산된 날짜:")
    print(f"  시작: {start_date.strftime('%Y-%m-%d')} (ISO: {start_iso[0]}년 {start_iso[1]}주 {start_iso[2]}요일)")
    print(f"        → {start_str}")
    print(f"  종료: {end_date.strftime('%Y-%m-%d')} (ISO: {end_iso[0]}년 {end_iso[1]}주 {end_iso[2]}요일)")
    print(f"        → {end_str}")
    print(f"  기간: {(end_date - start_date).days}일")
    
    # 주차 계산
    total_weeks = end_iso[1] - start_iso[1] + (end_iso[0] - start_iso[0]) * 52
    print(f"  예상 주수: {total_weeks}주")
    
    return start_str, end_str


if __name__ == "__main__":
    print("=" * 80)
    print("날짜 → 주차 변환 테스트 (YYYYWW 형식)")
    print("=" * 80)
    
    # 1년
    print("\n[테스트 1] 1년")
    start, end = calculate_date_range("1년")
    print(f"\n✅ API 파라미터: START_WRTTIME={start}, END_WRTTIME={end}")
    
    # 3년
    print("\n" + "=" * 80)
    print("[테스트 2] 3년")
    start, end = calculate_date_range("3년")
    print(f"\n✅ API 파라미터: START_WRTTIME={start}, END_WRTTIME={end}")
    
    # 사용자 지정
    print("\n" + "=" * 80)
    print("[테스트 3] 사용자 지정 (2024-01-01 ~ 2024-12-31)")
    start, end = calculate_date_range("사용자 지정", "2024-01-01", "2024-12-31")
    print(f"\n✅ API 파라미터: START_WRTTIME={start}, END_WRTTIME={end}")
    
    # 특정 날짜들 테스트
    print("\n" + "=" * 80)
    print("[테스트 4] 특정 날짜들의 주차 변환")
    print("-" * 80)
    test_dates = [
        "2024-01-01",  # 2024년 시작
        "2024-12-31",  # 2024년 끝
        "2025-01-01",  # 2025년 시작
        "2025-12-26",  # 오늘
        "2025-12-31",  # 2025년 끝
    ]
    
    for date_str in test_dates:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        iso = date_obj.isocalendar()
        week_format = date_to_week_format(date_obj)
        weekday_names = ['월', '화', '수', '목', '금', '토', '일']
        print(f"{date_str} ({weekday_names[iso[2]-1]}) → {iso[0]}년 {iso[1]:02d}주차 → {week_format}")
    
    print("\n" + "=" * 80)
    print("✓ 테스트 완료")
    print("=" * 80)
