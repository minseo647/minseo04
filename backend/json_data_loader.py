"""
JSON Data Loader for Historical News Data
1년치 미리 수집된 뉴스 데이터를 로딩하는 모듈
"""

import json
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

# Database import
try:
    from database import db
except (ImportError, ModuleNotFoundError):
    db = None
    logging.warning("Database module not available. DB operations will be skipped.")


logger = logging.getLogger(__name__)

class JSONDataLoader:
    def __init__(self, json_file_path: str = None):
        """
        Initialize JSON data loader
        
        Args:
            json_file_path: JSON 파일 경로. None이면 기본 경로 사용
        """
        if json_file_path is None:
            # 기본 경로: backend/../news_data.json
            current_dir = Path(__file__).parent
            self.json_file_path = current_dir.parent / "news_data.json"
        else:
            self.json_file_path = Path(json_file_path)
            
        self.articles_data = []
        self.loaded = False
        
    def load_data(self) -> bool:
        """
        JSON 파일에서 뉴스 데이터 로딩
        
        Returns:
            bool: 로딩 성공 여부
        """
        try:
            if not self.json_file_path.exists():
                logger.warning(f"JSON 파일을 찾을 수 없습니다: {self.json_file_path}")
                return False
                
            logger.info(f"JSON 데이터 로딩 중: {self.json_file_path}")
            
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                # Handle potential empty file
                content = f.read()
                if not content:
                    logger.warning(f"JSON 파일이 비어있습니다: {self.json_file_path}")
                    self.articles_data = []
                    self.loaded = True
                    return True
                data = json.loads(content)
                
            # 데이터 형식 확인 및 정규화
            if isinstance(data, list):
                self.articles_data = data
            elif isinstance(data, dict) and 'articles' in data:
                self.articles_data = data['articles']
            else:
                logger.error("JSON 파일 형식이 올바르지 않습니다.")
                return False
                
            logger.info(f"✅ {len(self.articles_data)}개의 기사 데이터를 로딩했습니다.")
            self.loaded = True
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {e} in {self.json_file_path}")
            return False
        except Exception as e:
            logger.error(f"데이터 로딩 실패: {e}")
            return False

    def save_articles_to_db(self) -> Dict[str, int]:
        """
        Loaded articles to the database (checking for duplicates).
        """
        if not self.loaded:
            if not self.load_data():
                return {'inserted': 0, 'skipped': 0, 'failed': 0}
        
        if db is None:
            logger.error("Database module not available. Cannot save to DB.")
            return {'inserted': 0, 'skipped': 0, 'failed': len(self.articles_data)}

        stats = {'inserted': 0, 'skipped': 0, 'failed': 0}
        
        logger.info(f"💾 Saving {len(self.articles_data)} articles from {self.json_file_path.name} to database...")

        for article in self.articles_data:
            try:
                link = article.get('link')
                if not link:
                    stats['failed'] += 1
                    continue

                # Check for duplicates (by link)
                existing = db.execute_query(
                    "SELECT id FROM articles WHERE link = %s" if db.db_type == "postgresql" else "SELECT id FROM articles WHERE link = ?",
                    [link]
                )
                
                if existing:
                    stats['skipped'] += 1
                    continue
                
                # Insert new article
                title = article.get('title', 'No Title')
                published = article.get('published', datetime.now().isoformat())
                source = article.get('source', 'Unknown Source')
                summary = article.get('summary', '')
                raw_text = article.get('raw_text', article.get('content', ''))
                keywords = json.dumps(article.get('keywords', []), ensure_ascii=False)

                if db.db_type == "postgresql":
                    query = """
                        INSERT INTO articles (title, link, published, source, summary, raw_text, keywords, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    """
                else: # sqlite
                    query = """
                        INSERT INTO articles (title, link, published, source, summary, raw_text, keywords, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                    """
                
                db.execute_query(query, [
                    title,
                    link, 
                    published,
                    source,
                    summary,
                    raw_text,
                    keywords
                ])
                
                stats['inserted'] += 1
                
            except Exception as e:
                logger.debug(f"Article saving error: {e} - Article: {article.get('title')}")
                stats['failed'] += 1
        
        logger.info(f"✅ Finished saving from {self.json_file_path.name} - Inserted: {stats['inserted']}, Skipped: {stats['skipped']}, Failed: {stats['failed']}")
        return stats

    def get_articles(self, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """
        기사 데이터 반환
        
        Args:
            limit: 반환할 기사 수 제한
            offset: 시작 인덱스
            
        Returns:
            List[Dict]: 기사 데이터 리스트
        """
        if not self.loaded:
            if not self.load_data():
                return []
        
        start_idx = offset
        end_idx = None if limit is None else offset + limit
        
        return self.articles_data[start_idx:end_idx]
    
    def get_articles_by_date_range(self, days_back: int = 365) -> List[Dict[str, Any]]:
        """
        특정 기간의 기사 반환
        
        Args:
            days_back: 현재로부터 며칠 전까지의 기사
            
        Returns:
            List[Dict]: 필터링된 기사 리스트
        """
        if not self.loaded:
            if not self.load_data():
                return []
                
        cutoff_date = datetime.now() - timedelta(days=days_back)
        filtered_articles = []
        
        for article in self.articles_data:
            try:
                # 다양한 날짜 형식 지원
                published = article.get('published', '')
                if published:
                    # ISO 형식 시도
                    try:
                        article_date = datetime.fromisoformat(published.replace('Z', '+00:00'))
                    except:
                        # 다른 형식들 시도
                        from dateutil import parser
                        article_date = parser.parse(published)
                    
                    if article_date >= cutoff_date:
                        filtered_articles.append(article)
            except Exception as e:
                logger.debug(f"날짜 파싱 실패: {article.get('title', 'Unknown')}, {e}")
                continue
                
        logger.info(f"📅 최근 {days_back}일간 기사 {len(filtered_articles)}개 반환")
        return filtered_articles
    
    def get_sources(self) -> List[str]:
        """
        뉴스 소스 목록 반환
        
        Returns:
            List[str]: 중복 제거된 소스 목록
        """
        if not self.loaded:
            if not self.load_data():
                return []
                
        sources = set()
        for article in self.articles_data:
            source = article.get('source', '')
            if source:
                sources.add(source)
                
        return sorted(list(sources))
    
    def search_articles(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        키워드로 기사 검색
        
        Args:
            query: 검색 키워드
            limit: 결과 개수 제한
            
        Returns:
            List[Dict]: 검색 결과
        """
        if not self.loaded:
            if not self.load_data():
                return []
                
        query_lower = query.lower()
        results = []
        
        for article in self.articles_data:
            title = article.get('title', '').lower()
            summary = article.get('summary', '').lower()
            keywords = article.get('keywords', '')
            
            # keywords가 문자열인 경우 소문자로 변환
            if isinstance(keywords, str):
                keywords = keywords.lower()
            elif isinstance(keywords, list):
                keywords = ' '.join(keywords).lower()
            else:
                keywords = ''
            
            if (query_lower in title or 
                query_lower in summary or 
                query_lower in keywords):
                results.append(article)
                
                if len(results) >= limit:
                    break
                    
        logger.info(f"🔍 '{query}' 검색 결과: {len(results)}개")
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """
        데이터 통계 반환
        
        Returns:
            Dict: 통계 정보
        """
        if not self.loaded:
            if not self.load_data():
                return {}
                
        sources = self.get_sources()
        
        # 날짜별 기사 수 계산 (최근 7일)
        daily_counts = []
        for i in range(7):
            target_date = datetime.now() - timedelta(days=i)
            count = 0
            
            for article in self.articles_data:
                try:
                    published = article.get('published', '')
                    if published:
                        article_date = datetime.fromisoformat(published.replace('Z', '+00:00'))
                        if article_date.date() == target_date.date():
                            count += 1
                except:
                    continue
                    
            daily_counts.append({
                'date': target_date.strftime('%Y-%m-%d'),
                'count': count
            })
        
        daily_counts.reverse()  # 오래된 날짜부터 정렬
        
        return {
            'total_articles': len(self.articles_data),
            'total_sources': len(sources),
            'total_favorites': 0,  # JSON 데이터에는 즐겨찾기 정보 없음
            'daily_counts': daily_counts,
            'data_source': 'json_file',
            'file_path': str(self.json_file_path)
        }

# 전역 인스턴스
json_loader = JSONDataLoader()