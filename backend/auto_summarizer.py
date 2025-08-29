"""
Auto Summarizer
뉴스 기사 자동 요약 생성 시스템
"""

import requests
from bs4 import BeautifulSoup
import logging
from typing import Optional, Dict, Any
import re
from datetime import datetime
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoSummarizer:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def generate_summary_from_title(self, title: str, source: str = "") -> str:
        """
        제목에서 핵심 키워드를 추출하여 간단한 요약 생성
        """
        try:
            # HTML 태그 제거
            clean_title = re.sub(r'<[^>]+>', '', title)
            # 특수문자 정리
            clean_title = re.sub(r'[^\w\s가-힣]', ' ', clean_title)
            
            # 한국어/영어별 처리
            if self._is_korean(clean_title):
                # 한국어 요약 생성
                summary = self._generate_korean_summary(clean_title, source)
            else:
                # 영어 요약 생성
                summary = self._generate_english_summary(clean_title, source)
            
            return summary
            
        except Exception as e:
            logger.error(f"제목 기반 요약 생성 오류: {e}")
            return f"{title[:100]}..." if len(title) > 100 else title
    
    def _is_korean(self, text: str) -> bool:
        """한국어 텍스트 여부 판단"""
        korean_count = len(re.findall(r'[가-힣]', text))
        return korean_count > len(text) * 0.1
    
    def _generate_korean_summary(self, title: str, source: str = "") -> str:
        """한국어 제목에서 요약 생성"""
        # 핵심 키워드 추출
        keywords = self._extract_korean_keywords(title)
        
        # 뉴스 유형 분류
        news_type = self._classify_korean_news(title)
        
        # 요약 템플릿
        if "기업" in news_type or "투자" in news_type:
            summary = f"{', '.join(keywords[:3])} 관련 비즈니스 소식입니다. "
        elif "기술" in news_type or "AI" in keywords:
            summary = f"{', '.join(keywords[:3])} 기술 발전 및 동향에 관한 분석입니다. "
        elif "정책" in news_type or "규제" in news_type:
            summary = f"{', '.join(keywords[:2])} 정책 및 규제 변화에 대한 보도입니다. "
        else:
            summary = f"{', '.join(keywords[:2])} 관련 최신 뉴스입니다. "
        
        # 소스 정보 추가
        if source:
            summary += f"({source} 보도)"
        
        return summary
    
    def _generate_english_summary(self, title: str, source: str = "") -> str:
        """영어 제목에서 요약 생성"""
        # 핵심 키워드 추출
        keywords = self._extract_english_keywords(title)
        
        # 뉴스 유형 분류
        if any(word in title.lower() for word in ['launch', 'release', 'announce', 'unveil']):
            summary = f"New {', '.join(keywords[:2])} announcement and launch details. "
        elif any(word in title.lower() for word in ['invest', 'funding', 'raise', 'acquire']):
            summary = f"Investment and business developments involving {', '.join(keywords[:2])}. "
        elif any(word in title.lower() for word in ['ai', 'machine learning', 'tech', 'innovation']):
            summary = f"Latest technology trends and innovations in {', '.join(keywords[:2])}. "
        else:
            summary = f"Latest news and updates on {', '.join(keywords[:2])}. "
        
        # 소스 정보 추가
        if source:
            summary += f"(Reported by {source})"
        
        return summary
    
    def _extract_korean_keywords(self, title: str) -> list:
        """한국어 제목에서 키워드 추출"""
        # 불용어 제거
        stop_words = ['이', '가', '을', '를', '의', '에', '와', '과', '으로', '로', '에서', '하고', '하는', '한', '할', '함', '및', '등']
        
        # 단어 분리 (간단한 공백 기반)
        words = title.split()
        keywords = []
        
        for word in words:
            # 특수문자 제거
            clean_word = re.sub(r'[^\w가-힣]', '', word)
            # 길이 체크 및 불용어 제거
            if len(clean_word) > 1 and clean_word not in stop_words:
                keywords.append(clean_word)
        
        return keywords[:5]
    
    def _extract_english_keywords(self, title: str) -> list:
        """영어 제목에서 키워드 추출"""
        # 불용어
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'will', 'would', 'could', 'should', 'may', 'might', 'can'}
        
        # 단어 추출
        words = re.findall(r'\b[a-zA-Z]+\b', title.lower())
        keywords = []
        
        for word in words:
            if len(word) > 2 and word not in stop_words:
                keywords.append(word.capitalize())
        
        return keywords[:5]
    
    def _classify_korean_news(self, title: str) -> str:
        """한국어 뉴스 유형 분류"""
        if any(keyword in title for keyword in ['기업', '회사', '상장', '투자', '인수', '합병']):
            return "기업"
        elif any(keyword in title for keyword in ['AI', '인공지능', '기술', '혁신', '개발']):
            return "기술"
        elif any(keyword in title for keyword in ['정부', '정책', '규제', '법안', '제도']):
            return "정책"
        elif any(keyword in title for keyword in ['시장', '주가', '경제', '산업']):
            return "경제"
        else:
            return "일반"
    
    def scrape_and_summarize(self, url: str, max_length: int = 200) -> Optional[str]:
        """
        웹페이지에서 본문을 스크래핑하여 요약 생성
        """
        try:
            logger.info(f"웹페이지 스크래핑 시작: {url}")
            
            # 요청 제한 (일부 사이트 차단 방지)
            time.sleep(1)
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 본문 추출 시도 (다양한 선택자)
            content_selectors = [
                'article',
                '.article-content', 
                '.content', 
                '.post-content',
                '.entry-content',
                '.article-body',
                '.news-content',
                'main p',
                '.container p'
            ]
            
            content_text = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content_text = ' '.join([elem.get_text().strip() for elem in elements])
                    break
            
            # 본문이 없으면 모든 p 태그에서 추출
            if not content_text:
                paragraphs = soup.find_all('p')
                content_text = ' '.join([p.get_text().strip() for p in paragraphs])
            
            # 텍스트 정리
            content_text = re.sub(r'\s+', ' ', content_text).strip()
            
            if len(content_text) > 50:
                # 간단한 문장 기반 요약
                summary = self._extract_key_sentences(content_text, max_length)
                logger.info(f"스크래핑 요약 생성 성공: {len(summary)} 문자")
                return summary
            else:
                logger.warning(f"스크래핑한 본문이 너무 짧음: {len(content_text)} 문자")
                return None
                
        except requests.RequestException as e:
            logger.warning(f"웹페이지 접근 실패: {e}")
            return None
        except Exception as e:
            logger.error(f"스크래핑 오류: {e}")
            return None
    
    def _extract_key_sentences(self, text: str, max_length: int) -> str:
        """핵심 문장 추출하여 요약 생성"""
        # 문장 분리
        sentences = re.split(r'[.!?]\s+', text)
        
        # 너무 짧거나 긴 문장 제외
        valid_sentences = [s.strip() for s in sentences if 20 <= len(s.strip()) <= 200]
        
        if not valid_sentences:
            return text[:max_length] + "..." if len(text) > max_length else text
        
        # 첫 번째 유효한 문장들로 요약 구성
        summary = ""
        for sentence in valid_sentences[:3]:  # 최대 3문장
            if len(summary + sentence) <= max_length:
                summary += sentence + ". "
            else:
                break
        
        return summary.strip() if summary else text[:max_length] + "..."

# 전역 인스턴스
auto_summarizer = AutoSummarizer()

def generate_auto_summary(title: str, url: str = "", source: str = "") -> str:
    """
    자동 요약 생성 메인 함수
    """
    try:
        # 1차: 웹 스크래핑 시도
        if url and url.startswith('http'):
            scraped_summary = auto_summarizer.scrape_and_summarize(url)
            if scraped_summary and len(scraped_summary) > 30:
                return scraped_summary
        
        # 2차: 제목 기반 요약 생성
        title_summary = auto_summarizer.generate_summary_from_title(title, source)
        return title_summary
        
    except Exception as e:
        logger.error(f"자동 요약 생성 실패: {e}")
        return f"{title[:100]}..." if len(title) > 100 else title

# CLI 테스트
if __name__ == "__main__":
    test_cases = [
        {
            "title": "삼성전자, AI 반도체 신기술 발표",
            "source": "전자신문",
            "url": ""
        },
        {
            "title": "OpenAI launches new GPT-5 model with enhanced capabilities",
            "source": "TechCrunch", 
            "url": ""
        }
    ]
    
    print("🧪 자동 요약 생성 테스트")
    print("="*50)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. 제목: {case['title']}")
        print(f"   소스: {case['source']}")
        
        summary = generate_auto_summary(case['title'], case['url'], case['source'])
        print(f"   요약: {summary}")