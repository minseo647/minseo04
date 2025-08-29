"""
Hybrid Data Collector
기존 JSON 파일들을 활용하면서 RSS로는 최근 1주일 기사만 수집하는 최적화된 수집기
"""

import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HybridDataCollector:
    def __init__(self):
        """하이브리드 데이터 수집기 초기화"""
        self.project_root = Path(__file__).parent.parent
        self.json_files = self._discover_json_files()
        self.cutoff_date = datetime.now() - timedelta(days=7)  # 1주일 제한
        
    def _discover_json_files(self) -> List[Path]:
        """프로젝트 내 JSON 파일들 자동 발견"""
        json_files = []
        
        # 알려진 JSON 파일들
        known_files = [
            "news_data.json",
            "hankyung_it_20240829_20250829.json", 
            "kbench_articles.json",
            "news_articles.json"
        ]
        
        for file_name in known_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                json_files.append(file_path)
                logger.info(f"📁 발견된 JSON 파일: {file_path}")
        
        # 추가 JSON 파일 검색 (패턴 매칭)
        for json_file in self.project_root.glob("*.json"):
            if json_file not in json_files and json_file.name not in [
                "package.json", "tsconfig.json", "vercel.json"
            ]:
                json_files.append(json_file)
                logger.info(f"📁 추가 발견된 JSON 파일: {json_file}")
        
        logger.info(f"🗂️ 총 {len(json_files)}개의 JSON 파일 발견")
        return json_files

    async def collect_all_data(self) -> Dict[str, Any]:
        """전체 데이터 수집 (JSON 파일 + 최근 RSS)"""
        start_time = datetime.now()
        logger.info("🚀 하이브리드 데이터 수집 시작")
        
        try:
            # 1. 기존 JSON 파일들 로드
            json_stats = await self._load_json_files()
            
            # 2. 최근 1주일 RSS 데이터 수집
            rss_stats = await self._collect_recent_rss()
            
            # 결과 통계
            total_stats = {
                'start_time': start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration': (datetime.now() - start_time).total_seconds(),
                'json_files': {
                    'loaded_files': json_stats['loaded_files'],
                    'total_articles': json_stats['total_articles'],
                    'inserted': json_stats['inserted'],
                    'skipped': json_stats['skipped'],
                    'failed': json_stats['failed']
                },
                'rss_collection': {
                    'feeds_processed': rss_stats['feeds_processed'],
                    'recent_articles': rss_stats['recent_articles'],
                    'inserted': rss_stats['inserted'],
                    'skipped': rss_stats['skipped']
                },
                'total_inserted': json_stats['inserted'] + rss_stats['inserted'],
                'total_processed': json_stats['total_articles'] + rss_stats['recent_articles']
            }
            
            logger.info(f"✅ 하이브리드 수집 완료: JSON {json_stats['inserted']}개 + RSS {rss_stats['inserted']}개 = 총 {total_stats['total_inserted']}개 신규 추가")
            return total_stats
            
        except Exception as e:
            logger.error(f"❌ 하이브리드 수집 실패: {e}")
            raise

    async def _load_json_files(self) -> Dict[str, Any]:
        """JSON 파일들을 DB에 로드"""
        logger.info("📂 JSON 파일 로딩 시작")
        
        try:
            from json_data_loader import JSONDataLoader
            
            total_stats = {
                'loaded_files': 0,
                'total_articles': 0,
                'inserted': 0,
                'skipped': 0,
                'failed': 0
            }
            
            for json_file in self.json_files:
                logger.info(f"📄 처리 중: {json_file.name}")
                
                try:
                    loader = JSONDataLoader(json_file_path=str(json_file))
                    
                    # 데이터 로드 및 검증
                    if loader.load_data():
                        articles_count = len(loader.articles_data)
                        logger.info(f"  └─ 로드된 기사 수: {articles_count}")
                        
                        # DB에 저장
                        stats = loader.save_articles_to_db()
                        
                        total_stats['loaded_files'] += 1
                        total_stats['total_articles'] += articles_count
                        total_stats['inserted'] += stats.get('inserted', 0)
                        total_stats['skipped'] += stats.get('skipped', 0)
                        total_stats['failed'] += stats.get('failed', 0)
                        
                        logger.info(f"  └─ DB 저장: {stats['inserted']}개 신규, {stats['skipped']}개 중복, {stats['failed']}개 실패")
                    else:
                        logger.warning(f"  └─ 파일 로드 실패: {json_file.name}")
                        
                except Exception as e:
                    logger.error(f"  └─ 파일 처리 오류 {json_file.name}: {e}")
                    continue
            
            logger.info(f"📂 JSON 로딩 완료: {total_stats['loaded_files']}개 파일, {total_stats['inserted']}개 신규 기사")
            return total_stats
            
        except ImportError:
            logger.error("❌ JSONDataLoader 모듈을 찾을 수 없습니다")
            return {'loaded_files': 0, 'total_articles': 0, 'inserted': 0, 'skipped': 0, 'failed': 0}

    async def _collect_recent_rss(self) -> Dict[str, Any]:
        """최근 1주일 RSS 데이터만 수집"""
        logger.info("📡 최근 1주일 RSS 수집 시작")
        
        try:
            from weekly_news_collector import collect_weekly_news_async
            
            # 기존 weekly collector를 사용하되, 날짜 필터링 강화
            logger.info(f"🗓️ 수집 기준: {self.cutoff_date.strftime('%Y-%m-%d')} 이후 기사")
            
            # RSS 수집 실행
            result = await collect_weekly_news_async()
            
            if result and 'stats' in result:
                stats = result['stats']
                rss_stats = {
                    'feeds_processed': result.get('successful_feeds', 0),
                    'recent_articles': stats.get('total_processed', 0),
                    'inserted': stats.get('total_inserted', 0),
                    'skipped': stats.get('total_skipped', 0)
                }
                
                logger.info(f"📡 RSS 수집 완료: {rss_stats['feeds_processed']}개 피드, {rss_stats['inserted']}개 신규")
                return rss_stats
            else:
                logger.warning("RSS 수집 결과가 비어있습니다")
                return {'feeds_processed': 0, 'recent_articles': 0, 'inserted': 0, 'skipped': 0}
                
        except ImportError:
            logger.error("❌ weekly_news_collector 모듈을 찾을 수 없습니다")
            return {'feeds_processed': 0, 'recent_articles': 0, 'inserted': 0, 'skipped': 0}
        except Exception as e:
            logger.error(f"❌ RSS 수집 오류: {e}")
            return {'feeds_processed': 0, 'recent_articles': 0, 'inserted': 0, 'skipped': 0}

    def get_data_sources_info(self) -> Dict[str, Any]:
        """데이터 소스 정보 반환"""
        return {
            'json_files': [
                {
                    'name': f.name,
                    'path': str(f),
                    'size_mb': round(f.stat().st_size / 1024 / 1024, 2),
                    'modified': datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                }
                for f in self.json_files
            ],
            'rss_collection_period': f"최근 {7}일",
            'cutoff_date': self.cutoff_date.isoformat()
        }

# 전역 인스턴스
hybrid_collector = HybridDataCollector()

async def collect_hybrid_data_async():
    """외부에서 호출할 수 있는 비동기 함수"""
    return await hybrid_collector.collect_all_data()

def get_hybrid_collector_info():
    """수집기 정보 반환"""
    return hybrid_collector.get_data_sources_info()

# CLI 실행
async def main():
    """메인 실행 함수"""
    logger.info("🔥 하이브리드 데이터 수집 프로세스 시작")
    
    # 데이터베이스 초기화
    try:
        from database import init_db
        logger.info("🗃️ 데이터베이스 초기화...")
        init_db()
    except Exception as e:
        logger.error(f"DB 초기화 실패: {e}")
        return
    
    # 데이터 수집 실행
    try:
        result = await hybrid_collector.collect_all_data()
        
        # 결과 출력
        print("\n" + "="*60)
        print("🎉 하이브리드 데이터 수집 결과")
        print("="*60)
        print(f"⏱️  소요시간: {result['duration']:.1f}초")
        print(f"📁 JSON 파일: {result['json_files']['loaded_files']}개 파일에서 {result['json_files']['inserted']}개 신규 추가")
        print(f"📡 RSS 수집: {result['rss_collection']['feeds_processed']}개 피드에서 {result['rss_collection']['inserted']}개 신규 추가")
        print(f"📊 총 결과: {result['total_inserted']}개 신규 기사 추가")
        print("="*60)
        
    except Exception as e:
        logger.error(f"💥 수집 프로세스 실패: {e}")

if __name__ == "__main__":
    asyncio.run(main())