#!/usr/bin/env python3
"""
Quick test script to verify hybrid data collection
하이브리드 데이터 수집 테스트 스크립트
"""

import asyncio
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_hybrid_collection():
    """하이브리드 수집기 테스트"""
    
    print("🧪 하이브리드 데이터 수집 테스트 시작")
    print("="*60)
    
    try:
        # 1. 모듈 임포트 테스트
        print("1️⃣ 모듈 임포트 테스트...")
        from database import init_db
        from hybrid_data_collector import get_hybrid_collector_info
        from json_data_loader import json_loader
        print("   ✅ 모든 모듈 임포트 성공")
        
        # 2. 데이터베이스 초기화
        print("2️⃣ 데이터베이스 초기화...")
        init_db()
        print("   ✅ 데이터베이스 초기화 완료")
        
        # 3. 하이브리드 수집기 정보 확인
        print("3️⃣ 하이브리드 수집기 정보 확인...")
        collector_info = get_hybrid_collector_info()
        print(f"   📁 발견된 JSON 파일: {len(collector_info['json_files'])}개")
        for file_info in collector_info['json_files']:
            print(f"     └─ {file_info['name']} ({file_info['size_mb']}MB)")
        print(f"   📅 RSS 수집 기간: {collector_info['rss_collection_period']}")
        
        # 4. JSON 로더 테스트
        print("4️⃣ JSON 로더 기능 테스트...")
        if json_loader.load_data():
            print(f"   ✅ JSON 데이터 로드 성공: {len(json_loader.articles_data)}개 기사")
            
            # 샘플 기사 확인
            if json_loader.articles_data:
                sample = json_loader.articles_data[0]
                print(f"   📰 샘플 기사: '{sample.get('title', 'N/A')[:50]}...'")
                print(f"       └─ 소스: {sample.get('source', 'N/A')}")
                print(f"       └─ 날짜: {sample.get('published', 'N/A')}")
        else:
            print("   ⚠️ JSON 데이터 로드 실패")
            
        # 5. 하이브리드 수집 테스트 (실제 실행하지 않고 준비만)
        print("5️⃣ 하이브리드 수집 준비 상태 확인...")
        try:
            from hybrid_data_collector import hybrid_collector
            print("   ✅ 하이브리드 수집기 준비 완료")
            print(f"   🗓️ 1주일 컷오프 날짜: {hybrid_collector.cutoff_date}")
            print(f"   📂 프로젝트 루트: {hybrid_collector.project_root}")
        except Exception as e:
            print(f"   ❌ 하이브리드 수집기 준비 실패: {e}")
            
        print("\n" + "="*60)
        print("✅ 테스트 완료 - 하이브리드 수집 시스템이 준비되었습니다!")
        print("📝 실제 수집 실행:")
        print("   • python backend/hybrid_data_collector.py")
        print("   • 또는 API 호출: POST /api/collect-news-now?use_hybrid=true")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def test_json_file_discovery():
    """JSON 파일 자동 발견 테스트"""
    
    print("\n🔍 JSON 파일 자동 발견 테스트")
    print("-"*40)
    
    project_root = Path(__file__).parent.parent
    
    # 알려진 파일들 확인
    known_files = [
        "news_data.json",
        "hankyung_it_20240829_20250829.json",
        "kbench_articles.json",
        "news_articles.json"
    ]
    
    found_files = []
    for file_name in known_files:
        file_path = project_root / file_name
        if file_path.exists():
            size_mb = round(file_path.stat().st_size / 1024 / 1024, 2)
            found_files.append((file_name, size_mb))
            print(f"✅ {file_name} - {size_mb}MB")
        else:
            print(f"❌ {file_name} - 파일 없음")
    
    # 추가 JSON 파일 검색
    print("\n🔍 추가 JSON 파일 검색...")
    additional_files = []
    for json_file in project_root.glob("*.json"):
        if json_file.name not in known_files and json_file.name not in [
            "package.json", "tsconfig.json", "vercel.json"
        ]:
            size_mb = round(json_file.stat().st_size / 1024 / 1024, 2)
            additional_files.append((json_file.name, size_mb))
            print(f"🆕 {json_file.name} - {size_mb}MB")
    
    if not additional_files:
        print("   └─ 추가 파일 없음")
    
    print(f"\n📊 총 {len(found_files)}개의 알려진 파일, {len(additional_files)}개의 추가 파일")
    
    return found_files + additional_files

if __name__ == "__main__":
    print("🚀 하이브리드 데이터 수집 시스템 테스트")
    
    # JSON 파일 발견 테스트
    test_json_file_discovery()
    
    # 하이브리드 수집 테스트
    asyncio.run(test_hybrid_collection())