"""
Weekly News Collector
1주일간의 최신 뉴스만 수집하는 경량화된 수집기
"""

import os
import json
import time
import logging
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio

import requests
import feedparser
from bs4 import BeautifulSoup

# Database import
from database import db

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration for 1-week collection (더 제한적으로)
MAX_RESULTS = int(os.getenv("WEEKLY_MAX_RESULTS", "3"))  # 각 소스당 최대 3개로 축소
MAX_TOTAL_PER_SOURCE = int(os.getenv("WEEKLY_MAX_TOTAL_PER_SOURCE", "5"))  # 소스당 총 5개로 축소
COLLECT_DAYS = int(os.getenv("WEEKLY_COLLECT_DAYS", "7"))  # 1주일 유지

CONNECT_TIMEOUT = float(os.getenv("CONNECT_TIMEOUT", "10.0"))
READ_TIMEOUT = float(os.getenv("READ_TIMEOUT", "15.0"))
PARALLEL_MAX_WORKERS = int(os.getenv("PARALLEL_MAX_WORKERS", "4"))  # 줄여서 부하 감소

# 핵심 RSS 피드만 선별 (기존 30개에서 15개로 축소)
WEEKLY_FEEDS = [
    # Korean Tech News (핵심 소스만)
    {"feed_url": "https://it.donga.com/feeds/rss/", "source": "IT동아", "category": "IT", "lang": "ko"},
    {"feed_url": "https://rss.etnews.com/Section902.xml", "source": "전자신문_속보", "category": "IT", "lang": "ko"},
    {"feed_url": "https://zdnet.co.kr/news/news_xml.asp", "source": "ZDNet Korea", "category": "IT", "lang": "ko"},
    {"feed_url": "https://www.itworld.co.kr/rss/all.xml", "source": "ITWorld Korea", "category": "IT", "lang": "ko"},
    {"feed_url": "https://www.bloter.net/feed", "source": "Bloter", "category": "IT", "lang": "ko"},
    {"feed_url": "https://platum.kr/feed", "source": "Platum", "category": "Startup", "lang": "ko"},
    {"feed_url": "https://www.boannews.com/media/news_rss.xml", "source": "보안뉴스", "category": "Security", "lang": "ko"},
    {"feed_url": "https://it.chosun.com/rss.xml", "source": "IT조선", "category": "IT", "lang": "ko"},
    
    # Global Tech News (핵심 소스만)
    {"feed_url": "https://techcrunch.com/feed/", "source": "TechCrunch", "category": "Tech", "lang": "en"},
    {"feed_url": "https://www.theverge.com/rss/index.xml", "source": "The Verge", "category": "Tech", "lang": "en"},
    {"feed_url": "https://www.wired.com/feed/rss", "source": "WIRED", "category": "Tech", "lang": "en"},
    {"feed_url": "https://www.engadget.com/rss.xml", "source": "Engadget", "category": "Tech", "lang": "en"},
    {"feed_url": "https://venturebeat.com/category/ai/feed/", "source": "VentureBeat AI", "category": "AI", "lang": "en"},
    {"feed_url": "https://arstechnica.com/feed/", "source": "Ars Technica", "category": "Tech", "lang": "en"},
    {"feed_url": "https://spectrum.ieee.org/rss/fulltext", "source": "IEEE Spectrum", "category": "Engineering", "lang": "en"},
]

# HTTP Session
HEADERS = {"User-Agent": "Mozilla/5.0 (WeeklyNewsBot/1.0)"}
session = requests.Session()
session.headers.update(HEADERS)

class WeeklyNewsCollector:
    def __init__(self):
        self.session = session
        self.cutoff_date = datetime.now() - timedelta(days=COLLECT_DAYS)
        
    def collect_from_feed(self, feed_config: Dict) -> List[Dict]:
        """
        단일 RSS 피드에서 1주일치 기사 수집
        """
        feed_url = feed_config["feed_url"]
        source = feed_config["source"]
        
        try:
            logger.info(f"📡 주간 수집 시작: {source}")
            
            # RSS 피드 파싱
            response = self.session.get(
                feed_url, 
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT)
            )
            
            if response.status_code != 200:
                logger.warning(f"❌ {source}: HTTP {response.status_code}")
                return []
                
            feed = feedparser.parse(response.content)
            
            if not hasattr(feed, 'entries') or not feed.entries:
                logger.warning(f"❌ {source}: 피드 엔트리 없음")
                return []
            
            articles = []
            processed_links = set()
            
            for entry in feed.entries[:MAX_RESULTS]:  # 각 소스당 최대 3개만
                try:
                    title = getattr(entry, 'title', '').strip()
                    link = getattr(entry, 'link', '').strip()
                    
                    if not title or not link or link in processed_links:
                        continue
                        
                    processed_links.add(link)
                    
                    # 날짜 파싱 및 1주일 필터
                    published_str = getattr(entry, 'published', '')
                    if published_str:
                        try:
                            published = datetime(*entry.published_parsed[:6])
                            if published < self.cutoff_date:
                                continue  # 1주일 이전 기사는 건너뜀
                        except:
                            published = datetime.now()  # 날짜 파싱 실패시 현재 시간
                    else:
                        published = datetime.now()
                    
                    # 요약 생성
                    summary = getattr(entry, 'summary', '')
                    if summary:
                        # HTML 태그 제거
                        soup = BeautifulSoup(summary, 'html.parser')
                        summary = soup.get_text()[:500]  # 500자 제한
                    
                    article = {
                        'title': title,
                        'link': link,
                        'published': published.isoformat(),
                        'source': source,
                        'summary': summary,
                        'category': feed_config.get('category', ''),
                        'language': feed_config.get('lang', ''),
                        'collected_at': datetime.now().isoformat()
                    }
                    
                    articles.append(article)
                    
                except Exception as e:
                    logger.debug(f"기사 처리 오류 ({source}): {e}")
                    continue
            
            logger.info(f"✅ {source}: {len(articles)}개 수집 완료")
            return articles
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ {source} 요청 실패: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ {source} 수집 실패: {e}")
            return []
    
    def save_articles_to_db(self, articles: List[Dict]) -> Dict[str, int]:
        """
        수집한 기사를 데이터베이스에 저장 (중복 제거)
        """
        if not articles:
            return {'inserted': 0, 'skipped': 0}
        
        stats = {'inserted': 0, 'skipped': 0, 'updated': 0}
        
        try:
            for article in articles:
                try:
                    # 중복 체크 (link 기준)
                    existing = db.execute_query(
                        "SELECT id FROM articles WHERE link = %s" 
                        if db.db_type == "postgresql" 
                        else "SELECT id FROM articles WHERE link = ?",
                        [article['link']]
                    )
                    
                    if existing:
                        stats['skipped'] += 1
                        continue
                    
                    # 새 기사 삽입
                    if db.db_type == "postgresql":
                        query = """
                            INSERT INTO articles (title, link, published, source, summary, created_at)
                            VALUES (%s, %s, %s, %s, %s, NOW())
                        """
                    else:
                        query = """
                            INSERT INTO articles (title, link, published, source, summary, created_at)
                            VALUES (?, ?, ?, ?, ?, datetime('now'))
                        """
                    
                    db.execute_query(query, [
                        article['title'],
                        article['link'], 
                        article['published'],
                        article['source'],
                        article['summary']
                    ])
                    
                    stats['inserted'] += 1
                    
                except Exception as e:
                    logger.debug(f"기사 저장 오류: {e}")
                    stats['skipped'] += 1
            
            logger.info(f"💾 저장 완료 - 신규: {stats['inserted']}, 중복: {stats['skipped']}")
            return stats
            
        except Exception as e:
            logger.error(f"데이터베이스 저장 실패: {e}")
            return stats
    
    async def collect_weekly_news(self) -> Dict:
        """
        1주일치 뉴스 수집 (비동기)
        """
        start_time = time.time()
        all_articles = []
        successful_feeds = 0
        failed_feeds = 0
        
        logger.info(f"🚀 1주일 뉴스 수집 시작 ({len(WEEKLY_FEEDS)}개 소스)")
        
        # 병렬 수집
        with ThreadPoolExecutor(max_workers=PARALLEL_MAX_WORKERS) as executor:
            futures = {
                executor.submit(self.collect_from_feed, feed): feed 
                for feed in WEEKLY_FEEDS
            }
            
            for future in as_completed(futures):
                feed = futures[future]
                try:
                    articles = future.result(timeout=30)  # 30초 타임아웃
                    if articles:
                        all_articles.extend(articles)
                        successful_feeds += 1
                    else:
                        failed_feeds += 1
                except Exception as e:
                    logger.error(f"❌ {feed['source']} 수집 실패: {e}")
                    failed_feeds += 1
        
        # 중복 제거 (링크 기준)
        unique_articles = []
        seen_links = set()
        
        for article in all_articles:
            if article['link'] not in seen_links:
                seen_links.add(article['link'])
                unique_articles.append(article)
        
        # 데이터베이스 저장
        save_stats = self.save_articles_to_db(unique_articles)
        
        duration = time.time() - start_time
        
        result = {
            'status': 'success',
            'duration': f"{duration:.2f}초",
            'stats': {
                'total_processed': len(all_articles),
                'total_unique': len(unique_articles),
                'total_inserted': save_stats['inserted'],
                'total_updated': save_stats.get('updated', 0),
                'total_skipped': save_stats['skipped']
            },
            'successful_feeds': successful_feeds,
            'failed_feeds': failed_feeds,
            'total_feeds': len(WEEKLY_FEEDS),
            'collection_period': f"{COLLECT_DAYS}일",
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"🎉 1주일 뉴스 수집 완료! 신규 {save_stats['inserted']}개 기사")
        return result

# 전역 인스턴스
weekly_collector = WeeklyNewsCollector()

async def collect_weekly_news_async() -> Dict:
    """
    1주일치 뉴스 수집 (외부 인터페이스)
    """
    return await weekly_collector.collect_weekly_news()