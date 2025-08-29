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
import re

# 대분류/소분류 카테고리 정의
CATEGORIES: Dict[str, Dict[str, List[str]]] = {
    "첨단 제조·기술 산업": {
        "반도체 분야": ["반도체", "메모리", "시스템 반도체", "파운드리", "소자", "웨이퍼", "노광", "EUV", "장비", "소재"],
        "자동차 분야": ["자동차", "내연기관", "전기차", "자율주행", "모빌리티", "현대차", "테슬라", "배터리카"],
        "이차전지 분야": ["이차전지", "배터리", "ESS", "양극재", "음극재", "전해질", "분리막"],
        "디스플레이 분야": ["디스플레이", "OLED", "QD", "마이크로 LED", "LCD"],
        "로봇·스마트팩토리 분야": ["로봇", "스마트팩토리", "산업자동화", "협동로봇"]
    },
    "에너지·환경 산업": {
        "에너지 분야": ["석유", "가스", "원자력", "태양광", "풍력", "수소", "신재생에너지"],
        "환경·탄소중립 분야": ["탄소중립", "폐기물", "친환경", "수처리", "CCUS", "재활용"]
    },
    "디지털·ICT 산업": {
        "AI 분야": ["AI", "인공지능", "머신러닝", "딥러닝", "생성형", "챗GPT", "로보틱스"],
        "ICT·통신 분야": ["5G", "6G", "통신", "네트워크", "인프라", "클라우드"],
        "소프트웨어·플랫폼": ["소프트웨어", "메타버스", "SaaS", "보안", "핀테크", "플랫폼"]
    },
    "바이오·헬스케어 산업": {
        "바이오·제약 분야": ["바이오", "제약", "신약", "바이오시밀러", "세포치료제", "유전자치료제"],
        "의료기기·헬스케어": ["의료기기", "헬스케어", "디지털 헬스", "웨어러블", "원격진료"]
    },
    "소재·화학 산업": {
        "첨단 소재": ["탄소소재", "나노소재", "고분자", "복합소재"],
        "정밀화학·석유화학": ["정밀화학", "석유화학", "케미컬", "특수가스", "반도체용 케미컬"]
    },
    "인프라·기반 산업": {
        "철강·조선·건설": ["철강", "조선", "건설", "스마트건설", "친환경 선박"],
        "물류·유통": ["물류", "유통", "전자상거래", "스마트 물류", "공급망"],
        "농업·식품": ["농업", "스마트팜", "대체식품", "식품"]
    }
}

# Regex for allowed characters in word cloud tokens  
_ALLOWED_TOKEN_RE = re.compile(r"^[\u1100-\u11FF\u3130-\u318F\uAC00-\uD7A3A-Za-z0-9\s\-\+\.\#_/·∙:()&%,]+$")

# 불용어 (제거할 의미없는 단어들)
STOPWORDS = {
    # 한글 조사, 어미, 의미없는 단어들
    '이', '가', '을', '를', '에', '의', '와', '과', '도', '은', '는', '에서', '으로', '로', '에게', '한테',
    '하다', '되다', '있다', '없다', '같다', '다른', '새로운', '좋은', '나쁜', '크다', '작다', '많다', '적다',
    '그', '이', '저', '그런', '이런', '저런', '것', '들', '등', '및', '또한', '하지만', '그러나', '따라서',
    '때문에', '위해', '통해', '대해', '관한', '관련', '경우', '때', '중', '후', '전', '동안', '사이',
    '년', '월', '일', '시간', '분', '초', '오늘', '어제', '내일', '지금', '현재', '과거', '미래',
    '한국', '미국', '중국', '일본', '유럽', '아시아', '서울', '부산', '대구', '인천', '광주', '대전', '울산',
    '회사', '기업', '업체', '업계', '산업', '분야', '시장', '고객', '사용자', '이용자', '소비자',
    '발표', '공개', '출시', '런칭', '시작', '종료', '완료', '진행', '계획', '예정', '목표', '성과', '결과',
    
    # 영어 불용어 (대소문자 모두 포함)
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from',
    'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'among',
    'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
    'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'they',
    'them', 'their', 'we', 'us', 'our', 'you', 'your', 'he', 'him', 'his', 'she', 'her', 'it', 'its',
    'as', 'so', 'if', 'when', 'where', 'who', 'what', 'why', 'how', 'which', 'than', 'then', 'now',
    'here', 'there', 'more', 'most', 'some', 'any', 'all', 'each', 'every', 'other', 'another', 'such',
    'very', 'much', 'many', 'few', 'little', 'big', 'small', 'large', 'long', 'short', 'high', 'low',
    'new', 'old', 'first', 'last', 'next', 'previous', 'same', 'different', 'good', 'bad', 'best', 'better',
    'get', 'got', 'getting', 'make', 'made', 'making', 'take', 'took', 'taken', 'give', 'gave', 'given',
    'come', 'came', 'coming', 'go', 'went', 'going', 'see', 'saw', 'seen', 'know', 'knew', 'known',
    'think', 'thought', 'say', 'said', 'tell', 'told', 'ask', 'asked', 'work', 'worked', 'working',
    'use', 'used', 'using', 'find', 'found', 'look', 'looked', 'looking', 'seem', 'seemed', 'become',
    'became', 'part', 'over', 'back', 'after', 'use', 'her', 'man', 'day', 'get', 'use', 'man', 'new',
    'now', 'way', 'may', 'say', 'each', 'which', 'she', 'two', 'how', 'its', 'who', 'did', 'yes', 'his',
    'been', 'her', 'my', 'more', 'if', 'no', 'do', 'would', 'my', 'so', 'about', 'out', 'many', 'then',
    
    # URL/웹 관련
    'http', 'https', 'www', 'com', 'org', 'net', 'co', 'kr', 'html', 'url', 'link', 'site', 'web', 'page',
    
    # 기타 의미없는 단어들
    'google', 'microsoft', 'apple', 'facebook', 'twitter', 'instagram', 'youtube', 'amazon', 'netflix',
    'like', 'just', 'also', 'only', 'even', 'still', 'well', 'too', 'really', 'actually', 'probably',
    'maybe', 'perhaps', 'quite', 'rather', 'pretty', 'enough', 'almost', 'nearly', 'around', 'about',
    
    # 한 글자 단어들과 숫자
    '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'G', 'K', 'M', 'B', 'T', 'P', 'i', 'x', 'v', 'c'
}

# 공학/기술 관련 키워드 화이트리스트 (카테고리 키워드 포함)
TECH_KEYWORDS = set()

# 카테고리에서 키워드 추출
for major_category, subcategories in CATEGORIES.items():
    for subcategory, keywords in subcategories.items():
        TECH_KEYWORDS.update(keywords)

# 추가 기술 키워드
ADDITIONAL_TECH_KEYWORDS = {
    # AI/머신러닝
    'AI', '인공지능', '머신러닝', '딥러닝', '신경망', 'CNN', 'RNN', 'LSTM', 'GAN', 'GPT', 'ChatGPT', 'OpenAI',
    '자연어처리', 'NLP', '컴퓨터비전', '패턴인식', '강화학습', '지도학습', '비지도학습', '트랜스포머', 'BERT',
    'LLM', '대화형AI', '생성AI', '멀티모달', '파인튜닝', 'RAG', '프롬프트엔지니어링',
    
    # 소프트웨어/프로그래밍
    'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Go', 'Rust', 'Swift', 'Kotlin', 'React', 'Vue', 'Angular',
    'Node.js', 'Django', 'Flask', 'Spring', '프레임워크', '라이브러리', 'API', 'REST', 'GraphQL', 'SDK',
    '오픈소스', '깃허브', 'GitHub', '버전관리', 'Git', '코딩', '프로그래밍', '개발자', '소프트웨어',
    'DevOps', 'CI/CD', '마이크로서비스', '컨테이너', 'Docker', 'Kubernetes',
    
    # 클라우드/인프라  
    'AWS', 'Azure', 'GCP', '구글클라우드', '클라우드', '서버리스', '가상화', 'VM', '하이브리드클라우드', '멀티클라우드',
    
    # 데이터/빅데이터
    '빅데이터', '데이터사이언스', '데이터분석', '데이터마이닝', '데이터베이스', 'SQL', 'NoSQL', 'MongoDB',
    'PostgreSQL', 'MySQL', '데이터웨어하우스', '데이터레이크', 'ETL', 'ELT', 'Apache', 'Hadoop', 'Spark',
    '비즈니스인텔리전스', 'BI', '시각화', 'Tableau', '파워BI',
    
    # 네트워크/통신
    '5G', '6G', 'LTE', 'WiFi', '블루투스', 'IoT', '사물인터넷', '무선통신', '네트워크', '라우터', '스위치',
    'VPN', '방화벽', 'CDN', '엣지컴퓨팅', '엣지', '네트워킹', '프로토콜', 'TCP', 'UDP', 'HTTP', 'HTTPS',
    
    # 보안/사이버보안
    '사이버보안', '보안', '암호화', '해킹', '피싱', '랜섬웨어', '멀웨어', '바이러스', '취약점', 'CISO',
    '인증', '권한', 'SSO', '다중인증', 'MFA', '블록체인', '스마트컨트랙트', '비트코인', '이더리움',
    '제로트러스트', '침입탐지', '보안운영센터', 'SOC',
    
    # 하드웨어/반도체
    '반도체', '칩', '프로세서', 'CPU', 'GPU', 'NPU', 'TPU', '메모리', 'RAM', 'SSD', 'HDD',
    '웨이퍼', '파운드리', 'TSMC', '삼성전자', 'SK하이닉스', '인텔', 'AMD', 'NVIDIA', '퀄컴',
    'OLED', '디스플레이', 'LCD', '마이크로LED', '센서', '카메라모듈',
    
    # 자동차/모빌리티
    '전기차', 'EV', '자율주행', '테슬라', '현대차', '기아', '모빌리티', '배터리', '리튬배터리',
    'LiDAR', '레이더', '커넥티드카', 'V2X', '충전인프라', '급속충전',
    
    # 로봇/자동화
    '로봇', '로보틱스', '자동화', 'RPA', '스마트팩토리', '산업자동화', '협동로봇', '드론', 'UAV',
    '3D프린팅', '적층제조', 'CNC', '스마트제조',
    
    # 바이오/헬스케어
    '바이오', '바이오테크', '제약', '신약개발', '유전자', 'DNA', 'RNA', 'mRNA', '백신', '항체',
    '의료기기', '디지털헬스', '헬스케어', '원격의료', '텔레헬스', '웨어러블', '바이오센서',
    '정밀의학', '개인맞춤의료', 'AI진단', '의료AI',
    
    # 에너지/환경
    '태양광', '풍력', '수소', '연료전지', '에너지저장장치', 'ESS', '스마트그리드', '신재생에너지',
    '탄소중립', '탄소포집', 'CCUS', '친환경', '그린테크', '청정기술',
    
    # 게임/엔터테인먼트
    '게임엔진', 'Unity', 'Unreal', 'VR', '가상현실', 'AR', '증강현실', 'MR', '혼합현실', '메타버스',
    'NFT', 'P2E', '게임개발', '모바일게임', 'PC게임', '콘솔게임',
    
    # 핀테크/금융기술
    '핀테크', '디지털뱅킹', '모바일페이', '간편결제', 'CBDC', '디지털화폐', '크라우드펀딩',
    '로보어드바이저', '인슈어테크', 'RegTech', '디지털금융',
    
    # 신기술
    '양자컴퓨팅', '양자', '나노기술', '신소재', '탄소나노튜브', '그래핀', '슈퍼컴퓨터', 'HPC',
    '엣지AI', '온디바이스AI', 'TinyML', '디지털트윈', 'API경제', 'SaaS', 'PaaS', 'IaaS'
}

# 모든 기술 키워드 합치기
TECH_KEYWORDS.update(ADDITIONAL_TECH_KEYWORDS)

def is_meaningful_token(token: str) -> bool:
    """의미있는 토큰인지 확인"""
    token = str(token).strip()
    
    # 길이 체크 (1글자 제외, 단 영문 약어는 허용)
    if len(token) <= 1:
        return False
    
    # 한글 1글자는 제외
    if len(token) == 1 and '\uAC00' <= token <= '\uD7A3':
        return False
    
    # 불용어 체크
    if token.lower() in STOPWORDS:
        return False
    
    # 숫자만으로 구성된 경우 제외 (단, 기술 관련 숫자는 허용)
    if token.isdigit() and token not in TECH_KEYWORDS:
        return False
    
    return True

def is_tech_term(token: str) -> bool:
    """기술 관련 용어인지 확인"""
    token = str(token).strip()
    
    # 화이트리스트에 있는 경우
    if token in TECH_KEYWORDS:
        return True
    
    # 대소문자 무시하고 체크
    if token.lower() in {kw.lower() for kw in TECH_KEYWORDS}:
        return True
    
    # 부분 매칭 (기술 키워드가 포함된 경우)
    for tech_kw in TECH_KEYWORDS:
        if tech_kw.lower() in token.lower() or token.lower() in tech_kw.lower():
            return True
    
    return False

def _guess_korean_font_path(user_font_path: Optional[str] = None) -> Optional[str]:
    """한글 폰트 경로를 찾는 함수 - 다양한 환경 지원"""
    if user_font_path and os.path.exists(user_font_path): 
        return user_font_path
    
    # 한글 폰트 후보들 (우선순위대로)
    candidates = [
        # Windows 폰트
        r"C:\Windows\Fonts\malgun.ttf",
        r"C:\Windows\Fonts\malgunbd.ttf", 
        r"C:\Windows\Fonts\NanumGothic.ttf",
        r"C:\Windows\Fonts\NanumBarunGothic.ttf",
        r"C:\Windows\Fonts\NotoSansKR-Regular.otf",
        r"C:\Windows\Fonts\NotoSansCJKkr-Regular.otf",
        r"C:\Windows\Fonts\gulim.ttc",
        r"C:\Windows\Fonts\batang.ttc",
        
        # macOS 폰트
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/AppleGothic.ttf",
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/Library/Fonts/AppleGothic.ttf",
        "/Library/Fonts/NanumGothic.otf",
        "/Library/Fonts/NanumGothic.ttf",
        "/Library/Fonts/NotoSansKR-Regular.otf",
        "/System/Library/Fonts/Helvetica.ttc",
        
        # Linux/Ubuntu 폰트
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf", 
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansKR-Regular.otf",
        "/usr/share/fonts/truetype/noto/NotoSansKR-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        
        # 추가 Linux 경로들
        "/usr/share/fonts/TTF/NanumGothic.ttf",
        "/usr/share/fonts/OTF/NotoSansKR-Regular.otf",
        "/usr/local/share/fonts/NanumGothic.ttf", 
        "/home/fonts/NanumGothic.ttf",
        
        # Docker/컨테이너 환경
        "/fonts/NanumGothic.ttf",
        "/app/fonts/NanumGothic.ttf",
        "./fonts/NanumGothic.ttf",
        
        # Google Fonts (웹 환경)
        "/tmp/NanumGothic.ttf",
        "/var/tmp/NanumGothic.ttf"
    ]
    
    for path in candidates:
        if os.path.exists(path): 
            logger.info(f"✅ 한글 폰트 발견: {path}")
            return path
    
    # 시스템에서 폰트 검색 시도
    try:
        import subprocess
        
        # Linux/Unix 시스템에서 fc-list를 사용하여 한글 폰트 찾기
        result = subprocess.run(['fc-list', ':lang=ko'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout:
            for line in result.stdout.split('\n'):
                if line and '.ttf' in line.lower():
                    font_path = line.split(':')[0].strip()
                    if os.path.exists(font_path):
                        logger.info(f"✅ fc-list로 한글 폰트 발견: {font_path}")
                        return font_path
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
        logger.debug(f"fc-list 실행 실패: {e}")
    
    # 마지막으로 matplotlib 기본 폰트 시도
    try:
        import matplotlib.font_manager as fm
        font_list = fm.findSystemFonts(fontpaths=None, fontext='ttf')
        korean_fonts = []
        
        for font_path in font_list:
            font_name = os.path.basename(font_path).lower()
            if any(keyword in font_name for keyword in ['nanum', 'malgun', 'gothic', 'noto']):
                korean_fonts.append(font_path)
        
        if korean_fonts:
            selected_font = korean_fonts[0]
            logger.info(f"✅ matplotlib으로 한글 폰트 발견: {selected_font}")
            return selected_font
            
    except Exception as e:
        logger.debug(f"matplotlib 폰트 검색 실패: {e}")
    
    logger.warning("❌ 한글 폰트를 찾을 수 없습니다. 워드클라우드에서 한글이 깨져 보일 수 있습니다.")
    return None

def _filter_wc_tokens(keywords_freq: List[tuple], strict_filter: bool = True) -> List[tuple]:
    """Filter wordcloud tokens based on allowed patterns and meaningfulness"""
    if not keywords_freq: return []
    cleaned = []
    for k, v in keywords_freq:
        ks = str(k).strip()
        if not ks: continue
        if _ALLOWED_TOKEN_RE.match(ks) is None: continue
        if not is_meaningful_token(ks): continue
        if strict_filter and not is_tech_term(ks): continue
        cleaned.append((ks, int(v)))
    return cleaned

def render_wordcloud_wc(keywords_freq: List[tuple], font_path: Optional[str] = None, 
                       auto_korean_font: bool = True, filter_unrenderables: bool = True):
    """Render wordcloud with Korean font support"""
    if not keywords_freq:
        return None
        
    filtered = _filter_wc_tokens(keywords_freq, strict_filter=filter_unrenderables)
    if not filtered:
        return None
        
    fp = None
    if auto_korean_font:
        fp = _guess_korean_font_path(font_path)
        
        # 폰트를 찾지 못한 경우 다운로드 시도
        if fp is None:
            fp = _download_korean_font()
    else:
        fp = font_path
    
    try:
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt
        
        # 한글 폰트 지원을 위한 matplotlib 설정
        if fp:
            try:
                import matplotlib.font_manager as fm
                fm.fontManager.addfont(fp)
                plt.rcParams['font.family'] = [fp]
            except Exception as e:
                logger.debug(f"matplotlib 폰트 설정 실패: {e}")
        
        wc = WordCloud(
            width=1000, height=500,
            background_color="white",
            collocations=False,
            font_path=fp,
            max_words=200,
            relative_scaling=0.5,
            colormap='viridis'
        )
        wc.generate_from_frequencies({k: int(v) for k, v in filtered})
        
        # Return the wordcloud object for further processing
        return wc, fp
        
    except ImportError:
        logger.error("WordCloud library not available")
        return None

def _download_korean_font() -> Optional[str]:
    """나눔고딕 폰트를 다운로드하여 임시 디렉터리에 저장"""
    try:
        import urllib.request
        
        # 폰트 저장할 임시 디렉터리 생성
        font_dir = "/tmp/fonts"
        os.makedirs(font_dir, exist_ok=True)
        font_path = os.path.join(font_dir, "NanumGothic.ttf")
        
        # 이미 다운로드된 경우
        if os.path.exists(font_path):
            logger.info(f"✅ 기존 다운로드된 한글 폰트 사용: {font_path}")
            return font_path
        
        # 나눔고딕 폰트 다운로드 (Google Fonts)
        font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
        
        logger.info("📥 한글 폰트 다운로드 중...")
        urllib.request.urlretrieve(font_url, font_path)
        
        if os.path.exists(font_path) and os.path.getsize(font_path) > 1000:  # 1KB 이상
            logger.info(f"✅ 한글 폰트 다운로드 성공: {font_path}")
            return font_path
        else:
            logger.error("❌ 다운로드된 폰트 파일이 유효하지 않습니다")
            if os.path.exists(font_path):
                os.remove(font_path)
            return None
            
    except Exception as e:
        logger.error(f"❌ 한글 폰트 다운로드 실패: {e}")
        return None

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

# Import enhanced modules (updated to include hybrid collector and auto summarizer)
try:
    from database import db, init_db, get_db_connection
    from enhanced_news_collector import collector, collect_news_async
    from weekly_news_collector import collect_weekly_news_async
    from hybrid_data_collector import collect_hybrid_data_async, get_hybrid_collector_info
    from json_data_loader import json_loader
    from auto_summarizer import generate_auto_summary
    ENHANCED_MODULES_AVAILABLE = True
    logger.info("✅ Enhanced modules loaded successfully (including auto summarizer)")
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
    major_category: Optional[str] = None,
    minor_category: Optional[str] = None,
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
            
            # 카테고리 필터링
            if major_category or minor_category:
                def article_matches_category(article):
                    article_text = f"{article.get('title', '')} {article.get('summary', '')} {article.get('keywords', '')}".lower()
                    
                    # 소분류가 선택된 경우
                    if minor_category and minor_category in CATEGORIES.get(major_category or '', {}):
                        # 대분류와 소분류 모두 선택된 경우
                        keywords = CATEGORIES[major_category][minor_category]
                    elif minor_category:
                        # 소분류만 선택된 경우 (모든 대분류에서 찾기)
                        keywords = []
                        for major_cat in CATEGORIES.values():
                            if minor_category in major_cat:
                                keywords = major_cat[minor_category]
                                break
                    elif major_category:
                        # 대분류만 선택된 경우 (해당 대분류의 모든 키워드)
                        keywords = []
                        for minor_cat in CATEGORIES[major_category].values():
                            keywords.extend(minor_cat)
                    else:
                        return True
                    
                    # 키워드 매칭
                    return any(keyword.lower() in article_text for keyword in keywords)
                
                articles = [a for a in articles if article_matches_category(a)]
            
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

@app.get("/api/categories")
async def get_categories():
    """Get available categories (major and minor categories)"""
    try:
        return {
            "categories": CATEGORIES,
            "major_categories": list(CATEGORIES.keys()),
            "all_minor_categories": {
                minor_cat: keywords 
                for major_cat in CATEGORIES.values() 
                for minor_cat, keywords in major_cat.items()
            }
        }
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        return {"categories": {}, "major_categories": [], "all_minor_categories": {}}

@app.get("/api/insights")
async def get_insights(
    period: str = Query("daily", description="Time period: daily, weekly, monthly"),
    days_back: int = Query(30, description="Number of days to look back"),
    use_json: bool = Query(True, description="Use JSON data as default")
):
    """Get insights data for charts"""
    try:
        from datetime import datetime, timedelta
        from collections import defaultdict
        
        # 기본적으로 JSON 데이터 사용
        if use_json:
            articles = json_loader.get_articles(limit=10000)  # 충분한 양의 데이터
            
            if not articles:
                return {
                    "time_series": [],
                    "category_counts": {},
                    "total_articles": 0,
                    "period": period
                }
            
            # 날짜별 기사 수 계산
            time_series_data = defaultdict(int)
            category_counts = defaultdict(int)
            
            from datetime import timezone
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days_back)
            
            for article in articles:
                try:
                    # 기사 날짜 파싱
                    article_date = datetime.fromisoformat(article.get('published', '').replace('Z', '+00:00'))
                    
                    # 지정된 기간 내의 기사만 처리
                    if start_date <= article_date <= end_date:
                        # 시간 단위별 그룹핑
                        if period == "daily":
                            date_key = article_date.strftime('%Y-%m-%d')
                        elif period == "weekly":
                            # 주 시작일 (월요일)로 그룹핑
                            week_start = article_date - timedelta(days=article_date.weekday())
                            date_key = week_start.strftime('%Y-%m-%d')
                        elif period == "monthly":
                            date_key = article_date.strftime('%Y-%m')
                        else:
                            date_key = article_date.strftime('%Y-%m-%d')
                        
                        time_series_data[date_key] += 1
                        
                        # 카테고리별 분류
                        article_text = f"{article.get('title', '')} {article.get('summary', '')} {article.get('keywords', '')}".lower()
                        
                        # 각 대분류에 대해 매칭 확인
                        matched_category = None
                        for major_category, subcategories in CATEGORIES.items():
                            for subcategory, keywords in subcategories.items():
                                if any(keyword.lower() in article_text for keyword in keywords):
                                    matched_category = major_category
                                    break
                            if matched_category:
                                break
                        
                        if matched_category:
                            category_counts[matched_category] += 1
                        else:
                            category_counts["기타"] += 1
                            
                except Exception as e:
                    logger.debug(f"Error processing article date: {e}")
                    continue
            
            # 시계열 데이터 정렬
            sorted_time_series = []
            if time_series_data:
                sorted_dates = sorted(time_series_data.keys())
                for date_key in sorted_dates:
                    sorted_time_series.append({
                        "date": date_key,
                        "count": time_series_data[date_key]
                    })
            
            return {
                "time_series": sorted_time_series,
                "category_counts": dict(category_counts),
                "total_articles": sum(time_series_data.values()),
                "period": period,
                "date_range": {
                    "start": start_date.strftime('%Y-%m-%d'),
                    "end": end_date.strftime('%Y-%m-%d')
                }
            }
        
        else:
            # DB 데이터 사용
            await ensure_db_initialized()
            
            if not ENHANCED_MODULES_AVAILABLE:
                return {"time_series": [], "category_counts": {}, "total_articles": 0, "period": period}
            
            # DB에서 최근 기사들 가져오기
            if db.db_type == "postgresql":
                query = """
                    SELECT title, summary, keywords, published, created_at 
                    FROM articles 
                    WHERE created_at >= %s 
                    ORDER BY created_at DESC
                """
                params = (datetime.now(timezone.utc) - timedelta(days=days_back),)
            else:
                query = """
                    SELECT title, summary, keywords, published, created_at 
                    FROM articles 
                    WHERE created_at >= datetime('now', '-{} days') 
                    ORDER BY created_at DESC
                """.format(days_back)
                params = ()
            
            articles = db.execute_query(query, params)
            
            time_series_data = defaultdict(int)
            category_counts = defaultdict(int)
            
            for article in articles:
                try:
                    # created_at 또는 published 사용
                    date_str = article.get('created_at') or article.get('published')
                    if date_str:
                        article_date = datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
                        
                        # 시간 단위별 그룹핑
                        if period == "daily":
                            date_key = article_date.strftime('%Y-%m-%d')
                        elif period == "weekly":
                            week_start = article_date - timedelta(days=article_date.weekday())
                            date_key = week_start.strftime('%Y-%m-%d')
                        elif period == "monthly":
                            date_key = article_date.strftime('%Y-%m')
                        else:
                            date_key = article_date.strftime('%Y-%m-%d')
                        
                        time_series_data[date_key] += 1
                        
                        # 카테고리별 분류
                        article_text = f"{article.get('title', '')} {article.get('summary', '')} {article.get('keywords', '')}".lower()
                        
                        matched_category = None
                        for major_category, subcategories in CATEGORIES.items():
                            for subcategory, keywords in subcategories.items():
                                if any(keyword.lower() in article_text for keyword in keywords):
                                    matched_category = major_category
                                    break
                            if matched_category:
                                break
                        
                        if matched_category:
                            category_counts[matched_category] += 1
                        else:
                            category_counts["기타"] += 1
                            
                except Exception as e:
                    logger.debug(f"Error processing article: {e}")
                    continue
            
            # 결과 정렬
            sorted_time_series = []
            if time_series_data:
                sorted_dates = sorted(time_series_data.keys())
                for date_key in sorted_dates:
                    sorted_time_series.append({
                        "date": date_key,
                        "count": time_series_data[date_key]
                    })
            
            return {
                "time_series": sorted_time_series,
                "category_counts": dict(category_counts),
                "total_articles": sum(time_series_data.values()),
                "period": period,
                "date_range": {
                    "start": (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime('%Y-%m-%d'),
                    "end": datetime.now(timezone.utc).strftime('%Y-%m-%d')
                }
            }
            
    except Exception as e:
        logger.error(f"Error getting insights: {e}")
        return {
            "time_series": [],
            "category_counts": {},
            "total_articles": 0,
            "period": period,
            "error": str(e)
        }

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
                            if kw and is_meaningful_token(kw) and is_tech_term(kw):
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
                                if kw and is_meaningful_token(kw) and is_tech_term(kw):
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
        if row[0]:
            try:
                # JSON 형태의 키워드 파싱
                if row[0].startswith('['):
                    keywords = json.loads(row[0])
                else:
                    keywords = row[0].split(',')
                    
                # 필터링된 키워드만 선택
                filtered_keywords = []
                for kw in keywords:
                    kw = str(kw).strip().strip('"').strip("'")
                    if kw and is_meaningful_token(kw) and is_tech_term(kw):
                        filtered_keywords.append(kw)
                        
                if filtered_keywords:
                    keyword_docs.append(filtered_keywords)
            except:
                # 기본 분할 방식으로 폴백
                keywords = row[0].split(',')
                filtered_keywords = []
                for kw in keywords:
                    kw = kw.strip()
                    if kw and is_meaningful_token(kw) and is_tech_term(kw):
                        filtered_keywords.append(kw)
                if filtered_keywords:
                    keyword_docs.append(filtered_keywords)
    
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
            edges.append({
                "from": kw1, 
                "to": kw2, 
                "value": weight,
                "label": f"{kw1} ↔ {kw2}",
                "title": f"{kw1}와(과) {kw2}가 함께 나타난 횟수: {weight}회"
            })
    
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
                logger.info("📊 Step 1/3: Initializing hybrid collector...")
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

# ====== 자동 요약 생성 API ======

@app.post("/api/enhance-summaries")
async def enhance_summaries(
    limit: int = Query(50, description="Number of articles to enhance"),
    force: bool = Query(False, description="Force re-enhancement of all summaries")
):
    """Enhance summaries for articles that lack proper summaries"""
    try:
        await ensure_db_initialized()
        
        if not ENHANCED_MODULES_AVAILABLE:
            raise HTTPException(status_code=503, detail="Auto summarizer not available")
        
        # Get articles that need summary enhancement from JSON data
        if json_loader.load_data():
            articles_data = json_loader.articles_data[:limit] if limit else json_loader.articles_data
            
            enhanced_count = 0
            failed_count = 0
            
            logger.info(f"🤖 Starting summary enhancement for {len(articles_data)} articles")
            
            for article in articles_data:
                try:
                    original_summary = article.get('summary', '')
                    
                    # Check if summary needs enhancement
                    needs_summary = (
                        not original_summary or 
                        len(original_summary.strip()) < 20 or
                        '[&#8230;]' in original_summary or
                        '...' in original_summary[-10:] or
                        force
                    )
                    
                    if needs_summary:
                        # Generate enhanced summary
                        enhanced_summary = generate_auto_summary(
                            title=article.get('title', ''),
                            url=article.get('link', ''),
                            source=article.get('source', '')
                        )
                        
                        # Update the article data (in memory)
                        article['summary'] = enhanced_summary
                        article['enhanced'] = True
                        enhanced_count += 1
                        
                        logger.debug(f"✅ Enhanced summary for: {article.get('title', '')[:50]}...")
                    
                except Exception as e:
                    logger.warning(f"❌ Failed to enhance summary: {e}")
                    failed_count += 1
            
            logger.info(f"🎉 Summary enhancement completed: {enhanced_count} enhanced, {failed_count} failed")
            
            return {
                "message": f"Summary enhancement completed: {enhanced_count} articles enhanced",
                "enhanced": enhanced_count,
                "failed": failed_count,
                "total": len(articles_data)
            }
        else:
            raise HTTPException(status_code=404, detail="No JSON data loaded")
        
    except Exception as e:
        logger.error(f"❌ Summary enhancement error: {e}")
        raise HTTPException(status_code=500, detail=f"Summary enhancement failed: {str(e)}")

@app.post("/api/generate-summary")
async def generate_summary(
    title: str,
    url: str = "",
    source: str = ""
):
    """Generate a summary for a given title and URL"""
    try:
        if not ENHANCED_MODULES_AVAILABLE:
            raise HTTPException(status_code=503, detail="Auto summarizer not available")
        
        enhanced_summary = generate_auto_summary(title=title, url=url, source=source)
        
        return {
            "title": title,
            "summary": enhanced_summary,
            "source": source,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"❌ Summary generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")

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
        if db.db_type == "postgresql":
            query = """
                SELECT keywords FROM articles 
                WHERE keywords IS NOT NULL 
                AND created_at >= NOW() - INTERVAL '30 days'
                ORDER BY created_at DESC 
                LIMIT %s
            """
            params = (limit * 2,)
        else: # sqlite
            query = """
                SELECT keywords FROM articles 
                WHERE keywords IS NOT NULL 
                AND created_at >= datetime('now', '-30 days')
                ORDER BY created_at DESC 
                LIMIT ?
            """
            params = (limit * 2,)

        cursor.execute(query, params)
        
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
                    if keyword and is_meaningful_token(keyword) and is_tech_term(keyword):
                        keyword_freq[keyword] += 1
        
        if not keyword_freq:
            # 기본 기술 키워드 제공 (기술 관련 단어만)
            keyword_freq = Counter({
                'AI': 50, '인공지능': 45, '딥러닝': 35, '머신러닝': 30,
                '블록체인': 25, '클라우드': 20, '보안': 18, '소프트웨어': 15,
                '데이터베이스': 12, '프로그래밍': 40, '개발자': 35, 'API': 22, 
                '빅데이터': 28, '5G': 25, 'IoT': 20, '반도체': 30, '전기차': 25
            })
        
        # 상위 키워드만 선택하고 튜플 형태로 변환
        top_keywords_list = list(keyword_freq.most_common(limit))
        
        # 새로운 한글 지원 워드클라우드 생성 함수 사용
        wc_result = render_wordcloud_wc(
            top_keywords_list, 
            auto_korean_font=True, 
            filter_unrenderables=True
        )
        
        if wc_result is None:
            raise HTTPException(status_code=500, detail="워드클라우드 생성 실패")
            
        wordcloud, font_path = wc_result
        
        # 크기 조정을 위해 다시 설정
        wordcloud.width = width
        wordcloud.height = height
        wordcloud.max_words = limit
        wordcloud.relative_scaling = 0.5
        wordcloud.colormap = 'viridis'
        wordcloud.min_font_size = 12
        wordcloud.max_font_size = 80
        wordcloud.prefer_horizontal = 0.7
        
        logger.info(f"✅ 워드클라우드 생성 완료 - 폰트: {font_path or '기본(한글 미지원일 수 있음)'}")
        
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
            "keyword_count": len(top_keywords_list),
            "top_keywords": [k for k, _ in top_keywords_list[:20]],
            "font_path": font_path,
            "korean_support": font_path is not None
        }
        
    except Exception as e:
        logger.error(f"워드클라우드 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"워드클라우드 생성 실패: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)