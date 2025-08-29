import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- UPDATED: Use Hybrid Data Collector ---
async def run_hybrid_collection():
    """Runs the new hybrid data collector (JSON files + recent RSS)."""
    try:
        from hybrid_data_collector import collect_hybrid_data_async
        logger.info("🚀 Starting hybrid data collection (JSON files + recent RSS)...")
        result = await collect_hybrid_data_async()
        logger.info(f"✅ Hybrid collection finished. Total inserted: {result.get('total_inserted', 0)}")
        return result
    except Exception as e:
        logger.error(f"💥 Hybrid collection failed: {e}")
        return None

# --- LEGACY: Individual components (kept for backward compatibility) ---
async def run_weekly_collection():
    """LEGACY: Runs the weekly news collector only."""
    try:
        from weekly_news_collector import collect_weekly_news_async
        logger.info("🚀 Starting weekly news collection...")
        result = await collect_weekly_news_async()
        logger.info(f"✅ Weekly news collection finished. Stats: {result.get('stats')}")
        return result
    except Exception as e:
        logger.error(f"💥 Weekly news collection failed: {e}")
        return None

def run_json_loading():
    """LEGACY: Loads data from specified JSON files into the database."""
    try:
        from json_data_loader import JSONDataLoader
        
        # Auto-discover JSON files
        project_root = Path(__file__).parent.parent
        json_files = [
            "news_data.json",  # 추가된 메인 파일
            "hankyung_it_20240829_20250829.json",
            "kbench_articles.json", 
            "news_articles.json"
        ]
        
        logger.info("🚀 Starting JSON data loading...")
        
        total_stats = {'inserted': 0, 'skipped': 0, 'failed': 0}

        for file_name in json_files:
            json_path = project_root / file_name
            if not json_path.exists():
                logger.warning(f"⚠️ JSON file not found, skipping: {json_path}")
                continue
            
            logger.info(f"📄 Processing: {file_name}")
            loader = JSONDataLoader(json_file_path=str(json_path))
            stats = loader.save_articles_to_db() 
            
            total_stats['inserted'] += stats.get('inserted', 0)
            total_stats['skipped'] += stats.get('skipped', 0)
            total_stats['failed'] += stats.get('failed', 0)
            
            logger.info(f"  └─ {stats.get('inserted', 0)} inserted, {stats.get('skipped', 0)} skipped")

        logger.info(f"✅ JSON data loading finished. Total Stats: {total_stats}")
        return total_stats

    except Exception as e:
        logger.error(f"💥 JSON data loading failed: {e}")
        return None


# --- Main Orchestrator (Updated) ---
async def main():
    """Main function - now uses hybrid collector by default."""
    logger.info("🔥 Starting integrated data collection process...")
    
    try:
        # Use new hybrid collector (combines JSON + RSS)
        result = await run_hybrid_collection()
        
        if result:
            print("\n" + "="*60)
            print("🎉 통합 데이터 수집 완료")
            print("="*60)
            print(f"📁 JSON 파일: {result['json_files']['inserted']}개 추가")
            print(f"📡 RSS 수집: {result['rss_collection']['inserted']}개 추가") 
            print(f"📊 총 결과: {result['total_inserted']}개 신규 기사")
            print(f"⏱️ 소요시간: {result['duration']:.1f}초")
            print("="*60)
        else:
            logger.error("하이브리드 수집 실패")
            
    except Exception as e:
        logger.error(f"💥 Integrated collection failed: {e}")
    
    logger.info("🎉 Integrated data collection process finished!")

# --- Legacy Main (for backward compatibility) ---
async def main_legacy():
    """Legacy main function - separate JSON and RSS collection."""
    logger.info("🔥 Starting LEGACY integrated data collection process...")
    
    # Step 1: Load historical data from JSON files  
    json_result = run_json_loading()
    
    # Step 2: Collect recent weekly news
    rss_result = await run_weekly_collection()
    
    logger.info("🎉 Legacy integrated data collection process finished successfully!")
    return {'json': json_result, 'rss': rss_result}

if __name__ == "__main__":
    try:
        from database import init_db
        logger.info("Initializing database...")
        init_db()
    except Exception as e:
        logger.error(f"DB initialization failed: {e}")

    asyncio.run(main())