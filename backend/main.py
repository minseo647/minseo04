from fastapi import FastAPI, HTTPException, Query, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Set, Any
import json
import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
import asyncio
import base64
import io
from collections import Counter

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import enhanced modules (updated to include hybrid collector)
try:
    from database import db, init_db, get_db_connection
    from enhanced_news_collector import collector, collect_news_async
    from weekly_news_collector import collect_weekly_news_async
    from hybrid_data_collector import collect_hybrid_data_async, get_hybrid_collector_info
    from json_data_loader import json_loader
    ENHANCED_MODULES_AVAILABLE = True
    logger.info("✅ Enhanced modules loaded successfully (including hybrid collector)")
except ImportError as e:
    logger.error(f"❌ Failed to load enhanced modules: {e}")
    ENHANCED_MODULES_AVAILABLE = False

# Fallback imports
if not ENHANCED_MODULES_AVAILABLE:
    logger.info("🔄 Using fallback modules")
    try:
        from simple_news_collector import collect_all_feeds, FEEDS
        SIMPLE_COLLECTOR_AVAILABLE = True
    except ImportError:
        SIMPLE_COLLECTOR_AVAILABLE = False
        logger.error("❌ No news collector available")

app = FastAPI(
    title="News IT's Issue API",
    description="Enhanced IT/Tech News Collection and Analysis Platform",
    version="2.0.0"
)

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")
ENABLE_CORS = os.getenv("ENABLE_CORS", "true").lower() == "true"

# CORS configuration
if ENABLE_CORS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Database initialization
_db_initialized = False

async def ensure_db_initialized():
    """Ensure database is initialized"""
    global _db_initialized
    if not _db_initialized:
        try:
            if ENHANCED_MODULES_AVAILABLE:
                db.init_database()
            else:
                # Fallback initialization
                import sqlite3
                conn = sqlite3.connect("/tmp/news.db")
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS articles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        link TEXT UNIQUE NOT NULL,
                        published TEXT,
                        source TEXT,
                        summary TEXT,
                        keywords TEXT,
                        created_at TEXT DEFAULT (datetime('now'))
                    )
                """)
                conn.commit()
                conn.close()
            _db_initialized = True
            logger.info("✅ Database initialized successfully")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise HTTPException(status_code=500, detail="Database initialization failed")

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("🚀 Starting News IT's Issue API Server")
    await ensure_db_initialized()
    
    # Log configuration
    logger.info(f"Database type: {db.db_type if ENHANCED_MODULES_AVAILABLE else 'SQLite'}")
    logger.info(f"Enhanced modules: {'Available' if ENHANCED_MODULES_AVAILABLE else 'Not Available'}")
    logger.info(f"OpenAI API: {'Configured' if OPENAI_API_KEY else 'Not Configured'}")
    logger.info(f"PostgreSQL: {'Available' if DATABASE_URL else 'Not Available'}")

class Article(BaseModel):
    id: int
    title: str
    link: str
    published: str
    source: str
    summary: Optional[str]
    keywords: Optional[str]
    created_at: Optional[str]
    is_favorite: bool = False

class FavoriteRequest(BaseModel):
    article_id: int

class KeywordStats(BaseModel):
    keyword: str
    count: int

class NetworkNode(BaseModel):
    id: str
    label: str
    value: int

class NetworkEdge(BaseModel):
    from_node: str = None
    to: str
    value: int

    model_config = {"field_alias_generator": None}
    
    def dict(self, **kwargs):
        data = super().model_dump(**kwargs)
        if 'from_node' in data:
            data['from'] = data.pop('from_node')
        return data

class CollectionRequest(BaseModel):
    name: str
    rules: Optional[Dict] = None

class NewsCollectionRequest(BaseModel):
    days: int = 30
    max_pages: int = 5

# get_db_connection is now imported from database module

@app.get("/api/articles")
async def get_articles(
    limit: int = Query(100, le=2000),
    offset: int = Query(0, ge=0),
    source: Optional[str] = None,
    search: Optional[str] = None,
    favorites_only: bool = False,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    use_json: bool = Query(True, description="Use JSON data as default")
):
    """Get articles with filtering and pagination (JSON data by default)"""
    
    try:
        # 기본적으로 JSON 데이터 사용
        if use_json:
            logger.info("📖 Using JSON data source")
            
            # 검색이 있는 경우
            if search:
                articles = json_loader.search_articles(search, limit * 2)  # 여유분으로 더 많이 가져옴
            else:
                articles = json_loader.get_articles(limit + offset, 0)
            
            # 소스 필터링
            if source:
                articles = [a for a in articles if a.get('source') == source]
            
            # 즐겨찾기 필터링 (JSON 데이터에서는 DB의 즐겨찾기 정보와 결합)
            if favorites_only:
                await ensure_db_initialized()
                if ENHANCED_MODULES_AVAILABLE:
                    favorite_articles = db.get_articles_with_filters(
                        limit=limit*10, offset=0, favorites_only=True
                    )
                    favorite_links = {a.get('link') for a in favorite_articles}
                    articles = [a for a in articles if a.get('link') in favorite_links]
                else:
                    articles = []  # JSON 전용 모드에서는 즐겨찾기 지원 안함
            
            # is_favorite 필드 추가 (DB에서 즐겨찾기 상태 확인)
            if ENHANCED_MODULES_AVAILABLE:
                try:
                    await ensure_db_initialized()
                    for article in articles:
                        try:
                            favorites = db.execute_query(
                                "SELECT article_id FROM favorites f JOIN articles a ON f.article_id = a.id WHERE a.link = %s"
                                if db.db_type == "postgresql" 
                                else "SELECT article_id FROM favorites f JOIN articles a ON f.article_id = a.id WHERE a.link = ?",
                                [article.get('link', '')]
                            )
                            article['is_favorite'] = len(favorites) > 0
                        except:
                            article['is_favorite'] = False
                except:
                    for article in articles:
                        article['is_favorite'] = False
            else:
                for article in articles:
                    article['is_favorite'] = False
            
            # 페이지네이션 적용
            total_before_pagination = len(articles)
            articles = articles[offset:offset + limit]
            
            logger.info(f"📖 JSON 데이터에서 {len(articles)}개 기사 반환 (전체 {total_before_pagination}개 중)")
            return articles
        
        # DB 데이터 사용 (기존 로직)
        else:
            await ensure_db_initialized()
            
            if ENHANCED_MODULES_AVAILABLE:
                articles = db.get_articles_with_filters(
                    limit=limit,
                    offset=offset,
                    source=source,
                    search=search,
                    favorites_only=favorites_only,
                    date_from=date_from,
                    date_to=date_to
                )
                return articles
            else:
                # Fallback implementation
                import sqlite3
                conn = sqlite3.connect("/tmp/news.db")
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = "SELECT *, 0 as is_favorite FROM articles WHERE 1=1"
                params = []
                
                if source:
                    query += " AND source = ?"
                    params.append(source)
                
                if search:
                    query += " AND (title LIKE ? OR summary LIKE ? OR keywords LIKE ?)"
                    search_param = f"%{search}%"
                    params.extend([search_param, search_param, search_param])
                
                query += " ORDER BY published DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                articles = [dict(row) for row in cursor.fetchall()]
                conn.close()
                
                return articles
            
    except Exception as e:
        logger.error(f"Error fetching articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sources")
async def get_sources(use_json: bool = Query(True, description="Use JSON data as default")):
    """Get available news sources"""
    try:
        # 기본적으로 JSON 데이터 사용
        if use_json:
            sources = json_loader.get_sources()
            logger.info(f"📖 JSON에서 {len(sources)}개 소스 반환")
            return sources
        else:
            # DB에서 소스 가져오기
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT source FROM articles ORDER BY source")
            sources = [row[0] for row in cursor.fetchall()]
            conn.close()
            return sources
    except Exception as e:
        logger.error(f"Error fetching sources: {e}")
        return []

@app.get("/api/keywords/stats")
async def get_keyword_stats(limit: int = Query(50, le=200), use_json: bool = Query(True, description="Use JSON data as default")):
    """Get keyword statistics"""
    
    try:
        # 기본적으로 JSON 데이터 사용
        if use_json:
            logger.info("📖 JSON 데이터에서 키워드 통계 생성")
            articles = json_loader.get_articles(limit * 10)  # 충분한 양의 기사 가져오기
            
            keyword_counter = {}
            for article in articles:
                keywords_str = article.get('keywords', '')
                if keywords_str:
                    try:
                        # JSON 형태의 키워드 파싱
                        if keywords_str.startswith('['):
                            keywords = json.loads(keywords_str)
                        else:
                            keywords = keywords_str.split(',')
                            
                        for kw in keywords:
                            kw = str(kw).strip().strip('"').strip("'")
                            if kw and len(kw) > 1:
                                keyword_counter[kw] = keyword_counter.get(kw, 0) + 1
                    except Exception:
                        continue
            
            sorted_keywords = sorted(keyword_counter.items(), key=lambda x: x[1], reverse=True)[:limit]
            result = [{"keyword": k, "count": v} for k, v in sorted_keywords]
            logger.info(f"📖 {len(result)}개 키워드 통계 반환")
            return result
        
        # DB 데이터 사용 (기존 로직)
        else:
            await ensure_db_initialized()
            
            if ENHANCED_MODULES_AVAILABLE:
                return db.get_keyword_stats(limit)
            else:
                # Fallback implementation
                import sqlite3
                conn = sqlite3.connect("/tmp/news.db")
                cursor = conn.cursor()
                cursor.execute("SELECT keywords FROM articles WHERE keywords IS NOT NULL")
                
                keyword_counter = {}
                for row in cursor.fetchall():
                    try:
                        if row[0]:
                            # Try to parse as JSON, fallback to comma-split
                            try:
                                keywords = json.loads(row[0])
                            except:
                                keywords = row[0].split(',')
                            
                            for kw in keywords:
                                kw = kw.strip()
                                if kw:
                                    keyword_counter[kw] = keyword_counter.get(kw, 0) + 1
                    except Exception:
                        continue
                
                conn.close()
                
                sorted_keywords = sorted(keyword_counter.items(), key=lambda x: x[1], reverse=True)[:limit]
                return [{"keyword": k, "count": v} for k, v in sorted_keywords]
            
    except Exception as e:
        logger.error(f"Error getting keyword stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/keywords/network")
async def get_keyword_network(limit: int = Query(30, le=100)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT keywords FROM articles WHERE keywords IS NOT NULL")
    
    keyword_docs = []
    for row in cursor.fetchall():
        keywords = row[0].split(',') if row[0] else []
        keywords = [kw.strip() for kw in keywords if kw.strip()]
        if keywords:
            keyword_docs.append(keywords)
    
    conn.close()
    
    keyword_counter = {}
    cooccurrence = {}
    
    for doc_keywords in keyword_docs:
        for kw in doc_keywords:
            keyword_counter[kw] = keyword_counter.get(kw, 0) + 1
        
        for i, kw1 in enumerate(doc_keywords):
            for kw2 in doc_keywords[i+1:]:
                pair = tuple(sorted([kw1, kw2]))
                cooccurrence[pair] = cooccurrence.get(pair, 0) + 1
    
    top_keywords = sorted(keyword_counter.items(), key=lambda x: x[1], reverse=True)[:limit]
    top_keyword_set = {k for k, _ in top_keywords}
    
    nodes = [{"id": kw, "label": kw, "value": count} for kw, count in top_keywords]
    edges = []
    
    for (kw1, kw2), weight in cooccurrence.items():
        if kw1 in top_keyword_set and kw2 in top_keyword_set and weight > 1:
            edges.append({"from": kw1, "to": kw2, "value": weight})
    
    return {"nodes": nodes, "edges": edges}

@app.get("/api/favorites")
async def get_favorites():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.* FROM articles a
        JOIN favorites f ON a.id = f.article_id
        ORDER BY f.created_at DESC
    """)
    
    favorites = []
    for row in cursor.fetchall():
        article = dict(row)
        article['is_favorite'] = True
        favorites.append(article)
    
    conn.close()
    return favorites

@app.post("/api/favorites/add")
async def add_favorite(request: FavoriteRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT OR IGNORE INTO favorites (article_id) VALUES (?)",
            (request.article_id,)
        )
        conn.commit()
        return {"success": True, "message": "Favorite added"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@app.delete("/api/favorites/{article_id}")
async def remove_favorite(article_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM favorites WHERE article_id = ?", (article_id,))
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Favorite removed"}

@app.get("/api/stats")
async def get_stats(use_json: bool = Query(True, description="Use JSON data as default")):
    """Get general statistics"""
    try:
        # 기본적으로 JSON 데이터 사용
        if use_json:
            stats = json_loader.get_stats()
            
            # DB에서 즐겨찾기 수만 가져와서 추가
            try:
                await ensure_db_initialized()
                if ENHANCED_MODULES_AVAILABLE:
                    favorites_result = db.execute_query("SELECT COUNT(*) as count FROM favorites")
                    if favorites_result:
                        stats['total_favorites'] = favorites_result[0]['count']
                else:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM favorites")
                    stats['total_favorites'] = cursor.fetchone()[0]
                    conn.close()
            except Exception as e:
                logger.debug(f"즐겨찾기 수 조회 실패: {e}")
                stats['total_favorites'] = 0
            
            logger.info(f"📖 JSON 통계 반환: {stats['total_articles']}개 기사, {stats['total_sources']}개 소스")
            return stats
        
        # DB 데이터 사용 (기존 로직)
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM articles")
            total_articles = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT source) FROM articles")
            total_sources = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM favorites")
            total_favorites = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT DATE(published) as date, COUNT(*) as count 
                FROM articles 
                WHERE published >= date('now', '-7 days')
                GROUP BY DATE(published)
                ORDER BY date
            """)
            daily_counts = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                "total_articles": total_articles,
                "total_sources": total_sources,
                "total_favorites": total_favorites,
                "daily_counts": daily_counts
            }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {
            "total_articles": 0,
            "total_sources": 0, 
            "total_favorites": 0,
            "daily_counts": []
        }

# Inline news collection functions
def collect_from_rss(feed_url: str, source: str, max_items: int = 10):
    """Collect articles from RSS feed"""
    try:
        import feedparser
        import requests
        from datetime import datetime
        
        print(f"📡 Collecting from {source}...")
        
        feed = feedparser.parse(feed_url)
        if not hasattr(feed, 'entries') or not feed.entries:
            return []
        
        articles = []
        for entry in feed.entries[:max_items]:
            try:
                title = getattr(entry, 'title', '').strip()
                link = getattr(entry, 'link', '').strip()
                
                if not title or not link:
                    continue
                
                published = getattr(entry, 'published', datetime.now().strftime('%Y-%m-%d'))
                summary = getattr(entry, 'summary', '')[:500] if hasattr(entry, 'summary') else ''
                
                articles.append({
                    'title': title,
                    'link': link,
                    'published': published,
                    'source': source,
                    'summary': summary
                })
                
            except Exception:
                continue
        
        print(f"✅ Collected {len(articles)} from {source}")
        return articles
        
    except Exception as e:
        print(f"❌ Error collecting from {source}: {e}")
        return []

def save_articles_to_db(articles):
    """Save articles to database"""
    if not articles:
        return {'inserted': 0, 'skipped': 0}
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    stats = {'inserted': 0, 'skipped': 0}
    
    for article in articles:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO articles (title, link, published, source, summary)
                VALUES (?, ?, ?, ?, ?)
            """, (
                article['title'],
                article['link'],
                article['published'],
                article['source'],
                article['summary']
            ))
            
            if cursor.rowcount > 0:
                stats['inserted'] += 1
            else:
                stats['skipped'] += 1
                
        except Exception:
            stats['skipped'] += 1
    
    conn.commit()
    conn.close()
    return stats

def run_collection():
    """Run news collection from major sources"""
    
    # Try simple collector first (no pandas dependency)
    if USE_SIMPLE_COLLECTOR:
        try:
            print("Using simple news collector...")
            # Ensure DB is initialized
            ensure_db_initialized()
            
            # Import and use simple collector with current DB
            import simple_news_collector
            simple_news_collector.DB_PATH = DB_PATH  # Use the same DB path
            
            # Collect news from all feeds
            all_articles = []
            for feed in SIMPLE_FEEDS[:10]:  # Limit to first 10 feeds for quick collection
                articles = collect_from_feed(feed['feed_url'], feed['source'], max_items=5)
                all_articles.extend(articles)
            
            if all_articles:
                # Save to our database
                stats = save_articles_to_db(all_articles)
                return True, len(all_articles), stats
                
        except Exception as e:
            print(f"Error using simple collector: {e}")
    
    # Try full news_collector as second option
    if USE_NEWS_COLLECTOR:
        try:
            print("Using full news_collector...")
            collector_init_db()
            collect_all_news()
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM articles")
            total_count = cursor.fetchone()[0]
            conn.close()
            
            return True, total_count, {"message": "Collection completed using news_collector"}
        except Exception as e:
            print(f"Error using news_collector: {e}")
    
    # Fallback to basic RSS collection
    print("Using basic RSS collection...")
    feeds = [
        {"url": "https://it.donga.com/feeds/rss/", "source": "IT동아"},
        {"url": "https://rss.etnews.com/Section902.xml", "source": "전자신문"},
        {"url": "https://techcrunch.com/feed/", "source": "TechCrunch"},
        {"url": "https://www.theverge.com/rss/index.xml", "source": "The Verge"},
        {"url": "https://www.engadget.com/rss.xml", "source": "Engadget"},
    ]
    
    all_articles = []
    for feed in feeds:
        articles = collect_from_rss(feed["url"], feed["source"])
        all_articles.extend(articles)
    
    if all_articles:
        stats = save_articles_to_db(all_articles)
        return True, len(all_articles), stats
    
    return False, 0, {}

# Enhanced news collection API
@app.post("/api/collect-news")
async def collect_news(background_tasks: BackgroundTasks):
    """Start news collection in background"""
    try:
        await ensure_db_initialized()
        background_tasks.add_task(run_background_collection)
        return {
            "message": "뉴스 수집을 시작했습니다.", 
            "status": "started",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error starting news collection: {e}")
        return {"message": f"오류: {str(e)}", "status": "error"}

async def run_background_collection():
    """Background news collection task"""
    try:
        logger.info("🚀 Starting background news collection")
        
        if ENHANCED_MODULES_AVAILABLE:
            result = await collect_news_async(max_feeds=15)  # Limit feeds for background
            logger.info(f"✅ Background collection completed: {result}")
        else:
            # Fallback collection
            logger.info("Using fallback collector")
            # Implement basic collection here if needed
            
    except Exception as e:
        logger.error(f"❌ Background collection error: {e}")

@app.post("/api/collect-news-now")
async def collect_news_now(
    max_feeds: Optional[int] = Query(None, description="Maximum number of feeds to process"),
    use_hybrid: bool = Query(True, description="Use hybrid collection (JSON + RSS)")
):
    """하이브리드 뉴스 수집 (JSON 파일 + 최근 1주일 RSS)"""
    try:
        await ensure_db_initialized()
        
        if ENHANCED_MODULES_AVAILABLE:
            if use_hybrid:
                # NEW: Use hybrid collector
                logger.info("🚀 Starting HYBRID collection (JSON files + recent RSS)")
                result = await collect_hybrid_data_async()
                
                # Get updated statistics
                try:
                    stats_query = "SELECT COUNT(*) as count FROM articles"
                    sources_query = "SELECT source, COUNT(*) as count FROM articles GROUP BY source ORDER BY count DESC"
                    
                    stats_result = db.execute_query(stats_query)
                    total_articles = stats_result[0]['count'] if stats_result else 0
                    
                    sources_result = db.execute_query(sources_query)
                    by_source = {row['source']: row['count'] for row in sources_result}
                    
                    return {
                        "message": f"하이브리드 수집 완료: JSON {result['json_files']['inserted']}개 + RSS {result['rss_collection']['inserted']}개 = 총 {result['total_inserted']}개 추가",
                        "status": "success",
                        "collection_type": "hybrid",
                        "duration": result['duration'],
                        "json_files": result['json_files'],
                        "rss_collection": result['rss_collection'],
                        "total_inserted": result['total_inserted'],
                        "total_processed": result['total_processed'],
                        "total_articles_in_db": total_articles,
                        "by_source": by_source,
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as stats_e:
                    logger.warning(f"Error getting stats: {stats_e}")
                    return {
                        "message": f"하이브리드 수집 완료 (통계 오류): {result['total_inserted']}개 추가",
                        "status": "success",
                        "collection_result": result
                    }
            else:
                # LEGACY: Weekly RSS only
                logger.info("🚀 Starting weekly news collection (1주일 데이터 only)")
                result = await collect_weekly_news_async()
                
                # Get updated statistics
                try:
                    stats_query = "SELECT COUNT(*) as count FROM articles"
                    sources_query = "SELECT source, COUNT(*) as count FROM articles GROUP BY source ORDER BY count DESC"
                    
                    stats_result = db.execute_query(stats_query)
                    total_articles = stats_result[0]['count'] if stats_result else 0
                    
                    sources_result = db.execute_query(sources_query)
                    by_source = {row['source']: row['count'] for row in sources_result}
                    
                    return {
                        "message": f"1주일 뉴스 수집 완료: {result['stats']['total_inserted']}개 신규 기사 추가",
                        "status": "success",
                        "collection_type": "weekly_rss",
                        "collection_period": result['collection_period'],
                        "duration": result['duration'],
                        "processed": result['stats']['total_processed'],
                        "unique_articles": result['stats']['total_unique'],
                        "inserted": result['stats']['total_inserted'],
                        "updated": result['stats']['total_updated'],
                        "skipped": result['stats']['total_skipped'],
                        "total_articles_in_db": total_articles,
                        "by_source": by_source,
                        "successful_feeds": result['successful_feeds'],
                        "failed_feeds": result['failed_feeds'],
                        "total_feeds": result['total_feeds'],
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as stats_e:
                    logger.warning(f"Error getting stats: {stats_e}")
                    return {
                        "message": "1주일 뉴스 수집 완료 (통계 오류)",
                        "status": "success",
                        "collection_result": result
                    }
        else:
            # Fallback simple collection
            if SIMPLE_COLLECTOR_AVAILABLE:
                total_count, stats = collect_all_feeds()
                return {
                    "message": f"뉴스 수집 완료: {stats.get('inserted', 0)}개 신규 추가",
                    "status": "success",
                    "processed": total_count,
                    "inserted": stats.get('inserted', 0),
                    "skipped": stats.get('skipped', 0)
                }
            else:
                raise HTTPException(status_code=500, detail="No news collector available")
            
    except Exception as e:
        logger.error(f"❌ News collection error: {e}")
        raise HTTPException(status_code=500, detail=f"뉴스 수집 오류: {str(e)}")

@app.get("/api/collection-status")
async def get_collection_status():
    """Get current collection status and stats (including hybrid collector info)"""
    try:
        await ensure_db_initialized()
        
        if ENHANCED_MODULES_AVAILABLE:
            # Get database stats
            total_query = "SELECT COUNT(*) as count FROM articles"
            total_articles = db.execute_query(total_query)[0]['count']
            
            recent_query = """
                SELECT COUNT(*) as count FROM articles 
                WHERE created_at > %s
            """ if db.db_type == "postgresql" else """
                SELECT COUNT(*) as count FROM articles 
                WHERE created_at > datetime('now', '-1 day')
            """
            
            if db.db_type == "postgresql":
                params = (datetime.now() - timedelta(days=1),)
                recent_articles = db.execute_query(recent_query, params)[0]['count']
            else:
                recent_articles = db.execute_query(recent_query)[0]['count']
            
            sources_query = "SELECT source, COUNT(*) as count FROM articles GROUP BY source ORDER BY count DESC LIMIT 10"
            top_sources = db.execute_query(sources_query)
            
            # Get hybrid collector info
            try:
                hybrid_info = get_hybrid_collector_info()
            except Exception as e:
                logger.warning(f"Failed to get hybrid collector info: {e}")
                hybrid_info = None
            
            return {
                "status": "active",
                "total_articles": total_articles,
                "recent_articles_24h": recent_articles,
                "top_sources": top_sources,
                "database_type": db.db_type,
                "enhanced_features": True,
                "hybrid_collector": hybrid_info,
                "collection_modes": {
                    "hybrid": "JSON files + recent RSS (default)",
                    "weekly_rss": "RSS only (1 week limit)",
                    "json_only": "Historical JSON files only"
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "basic",
                "enhanced_features": False,
                "message": "기본 수집 모드"
            }
            
    except Exception as e:
        logger.error(f"Error getting collection status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 정적 파일 서빙 설정 (React 빌드 파일)
frontend_dist = Path(__file__).parent.parent / "frontend" / "news-app" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")
    
    @app.get("/")
    async def serve_frontend():
        index_path = frontend_dist / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        else:
            return {"message": "Frontend not built. Please run 'npm run build' in frontend/news-app directory"}
else:
    @app.get("/")
    async def root():
        return {"message": "News API Server is running. Frontend not found."}

# 컬렉션 관리 API
@app.get("/api/collections")
async def get_collections():
    """모든 컬렉션 목록을 반환합니다."""
    try:
        ensure_db_initialized()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all collections
        cursor.execute("""
            SELECT c.id, c.name, c.rules, c.created_at, 
                   COUNT(ca.article_id) as article_count
            FROM collections c
            LEFT JOIN collection_articles ca ON c.id = ca.collection_id
            GROUP BY c.id
        """)
        
        collections = []
        for row in cursor.fetchall():
            collection = dict(row)
            collection['rules'] = json.loads(collection['rules']) if collection['rules'] else {}
            collection['count'] = collection['article_count']
            collections.append(collection)
        
        conn.close()
        return collections
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"컬렉션 조회 실패: {str(e)}")

@app.post("/api/collections")
async def create_collection(request: CollectionRequest):
    """새로운 컬렉션을 생성합니다."""
    try:
        ensure_db_initialized()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create the collection
        cursor.execute("""
            INSERT INTO collections (name, rules) VALUES (?, ?)
        """, (request.name, json.dumps(request.rules) if request.rules else None))
        
        collection_id = cursor.lastrowid
        
        # Add articles based on rules
        if request.rules and 'include_keywords' in request.rules:
            keywords = request.rules['include_keywords']
            keyword_filter = ' OR '.join([f"keywords LIKE '%{kw}%'" for kw in keywords])
            
            cursor.execute(f"""
                INSERT INTO collection_articles (collection_id, article_id)
                SELECT ?, id FROM articles 
                WHERE {keyword_filter}
            """, (collection_id,))
            
            added_count = cursor.rowcount
        else:
            added_count = 0
        
        conn.commit()
        conn.close()
        
        return {"message": f"컬렉션 '{request.name}' 생성 완료", "added_articles": added_count, "collection_id": collection_id}
        
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail=f"컬렉션 '{request.name}'이 이미 존재합니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"컬렉션 생성 실패: {str(e)}")

# 키워드 추출 API  
@app.post("/api/extract-keywords/{article_id}")
async def extract_article_keywords(article_id: int):
    """특정 기사의 키워드를 추출합니다."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT title, summary FROM articles WHERE id = ?", (article_id,))
        article = cursor.fetchone()
        
        if not article:
            raise HTTPException(status_code=404, detail="기사를 찾을 수 없습니다.")
        
        text = f"{article['title']} {article['summary'] or ''}"
        keywords = extract_keywords(text)
        
        # 키워드 업데이트
        cursor.execute("UPDATE articles SET keywords = ? WHERE id = ?", 
                      (",".join(keywords), article_id))
        conn.commit()
        conn.close()
        
        return {"keywords": keywords, "message": "키워드 추출 완료"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"키워드 추출 실패: {str(e)}")

# 번역 API
@app.post("/api/translate/{article_id}")  
async def translate_article(article_id: int):
    """특정 기사를 번역합니다."""
    try:
        ensure_db_initialized()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
        article = cursor.fetchone()
        
        if not article:
            raise HTTPException(status_code=404, detail="기사를 찾을 수 없습니다.")
        
        article_dict = dict(article)
        
        # Simple translation using basic patterns (without external API)
        # This is a placeholder - in production, use proper translation API
        translated_title = article_dict['title']
        translated_summary = article_dict.get('summary', '')
        
        # Basic keyword-based translation hints
        translation_map = {
            'AI': '인공지능',
            'Machine Learning': '머신러닝',
            'Deep Learning': '딥러닝',
            'Cloud': '클라우드',
            'Security': '보안',
            'Data': '데이터',
            'API': 'API',
            'Web': '웹',
            'Mobile': '모바일',
            'Database': '데이터베이스'
        }
        
        # Check if article appears to be in English
        is_english = any(word in translated_title.lower() for word in ['the', 'and', 'or', 'is', 'to'])
        
        if is_english:
            # Apply basic translations for known terms
            for eng, kor in translation_map.items():
                if eng.lower() in translated_title.lower():
                    translated_title = f"{translated_title} ({kor} 관련)"
                    break
            
            article_dict['translated_title'] = translated_title
            article_dict['translated_summary'] = f"[자동 번역 미지원] {translated_summary[:100]}..."
            article_dict['is_translated'] = True
            message = "기본 번역 제공 (전문 번역 서비스는 API 키 설정 필요)"
        else:
            article_dict['is_translated'] = False
            message = "한국어 기사입니다"
        
        conn.close()
        
        return {"message": message, "article": article_dict}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"번역 실패: {str(e)}")

# ====== 워드클라우드 생성 API ======

@app.get("/api/wordcloud")
async def generate_wordcloud(
    limit: int = Query(100, description="키워드 제한 수"),
    width: int = Query(800, description="이미지 너비"),
    height: int = Query(400, description="이미지 높이")
):
    """파이썬 wordcloud 라이브러리를 사용한 워드클라우드 생성"""
    try:
        # WordCloud 라이브러리 임포트 (필요시 설치)
        try:
            from wordcloud import WordCloud
            import matplotlib.pyplot as plt
            from matplotlib import font_manager
        except ImportError:
            raise HTTPException(
                status_code=500, 
                detail="WordCloud 라이브러리가 설치되지 않았습니다. pip install wordcloud pillow matplotlib 실행 필요"
            )
        
        # 데이터베이스에서 키워드 수집
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 최근 기사들의 키워드 수집
        cursor.execute("""
            SELECT keywords FROM articles 
            WHERE keywords IS NOT NULL 
            AND created_at >= NOW() - INTERVAL '30 days'
            ORDER BY created_at DESC 
            LIMIT %s
        """, (limit * 2,))
        
        results = cursor.fetchall()
        conn.close()
        
        # 키워드 추출 및 빈도 계산
        keyword_freq = Counter()
        
        for (keywords_str,) in results:
            if keywords_str:
                if isinstance(keywords_str, str):
                    try:
                        # JSON 형태의 키워드 파싱
                        keywords = json.loads(keywords_str) if keywords_str.startswith('[') else keywords_str.split(',')
                    except:
                        keywords = keywords_str.split(',')
                else:
                    keywords = keywords_str
                
                for keyword in keywords:
                    keyword = str(keyword).strip()
                    if keyword and len(keyword) > 1:
                        keyword_freq[keyword] += 1
        
        if not keyword_freq:
            # 기본 키워드 제공
            keyword_freq = Counter({
                'AI': 50, '인공지능': 45, '딥러닝': 35, '머신러닝': 30,
                '블록체인': 25, '클라우드': 20, '보안': 18, '스타트업': 15,
                '투자': 12, '기술': 40, 'IT': 35, '개발': 22, '데이터': 28
            })
        
        # 상위 키워드만 선택
        top_keywords = dict(keyword_freq.most_common(limit))
        
        # 한글 폰트 설정 (시스템에서 사용 가능한 폰트 찾기)
        font_path = None
        korean_fonts = [
            '/System/Library/Fonts/AppleSDGothicNeo.ttc',  # macOS
            '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',  # Ubuntu
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',  # 기본 폰트
            'C:\\Windows\\Fonts\\malgun.ttf',  # Windows
            'NanumGothic',  # 시스템 폰트명
        ]
        
        for font in korean_fonts:
            if os.path.exists(font):
                font_path = font
                break
        
        # WordCloud 생성
        wordcloud = WordCloud(
            font_path=font_path,
            width=width,
            height=height,
            background_color='white',
            max_words=limit,
            relative_scaling=0.5,
            colormap='viridis',
            min_font_size=12,
            max_font_size=80,
            prefer_horizontal=0.7
        ).generate_from_frequencies(top_keywords)
        
        # 이미지를 바이트로 변환
        img_buffer = io.BytesIO()
        plt.figure(figsize=(width/100, height/100))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.tight_layout(pad=0)
        plt.savefig(img_buffer, format='PNG', bbox_inches='tight', dpi=100)
        plt.close()
        
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
        
        return {
            "wordcloud_image": f"data:image/png;base64,{img_base64}",
            "keyword_count": len(top_keywords),
            "top_keywords": list(top_keywords.keys())[:20]
        }
        
    except Exception as e:
        logger.error(f"워드클라우드 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"워드클라우드 생성 실패: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)