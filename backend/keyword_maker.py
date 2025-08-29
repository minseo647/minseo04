import openai
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 불용어 리스트
KOREAN_STOPWORDS = [
    '이', '가', '은', '는', '을', '를', '의', '에', '와', '과', '하고', '에게', '께', '에서', '으로', '로',
    '하다', '되다', '이다', '있다', '없다', '같다', '들', '등', '및', '그', '저', '이것', '저것', '그것',
    '수', '것', '있는', '없는', '위한', '통해', '대한', '때문', '그리고', '하지만', '그러나', '그리고',
    '또는', '만', '도', '뿐', '까지', '부터', '이라', '다', '요', '죠', '고', '기자', '뉴스', '사진',
    '따르면', '밝혔다', '전했다', '말했다', '지난', '올해', '내년', '위해', '통한', '관련', '최근'
]

ENGLISH_STOPWORDS = [
    'a', 'an', 'the', 'and', 'or', 'but', 'if', 'of', 'at', 'by', 'for', 'with', 'about', 'against',
    'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from',
    'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once',
    'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
    'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
    'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now', 'is', 'are', 'was',
    'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing'
]

STOPWORDS = KOREAN_STOPWORDS + ENGLISH_STOPWORDS


def def extract_keywords(text: str) -> List[str]:
    """텍스트에서 키워드를 추출하고 불용어를 제거합니다."""
    if not text or not OPENAI_API_KEY:
        return []
    
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        prompt = f"""
        다음 텍스트에서 IT/기술 분야의 핵심 전문용어 키워드를 추출해주세요.
        - 반드시 2글자 이상의 명사 형태의 키워드만 선택해주세요.
        - '및', '등', '위한', '통해' 같은 일반적인 단어나 조사, 접속사는 모두 제외해주세요.
        - 영어 키워드의 경우 'and', 'for', 'the'와 같은 불용어는 제외해주세요.
        - 가장 중요한 순서대로 최대 8개까지 쉼표로 구분하여 나열해주세요.
        - 만약 적절한 키워드가 없으면, 빈 리스트를 반환해주세요.

        텍스트: {text[:1000]}
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 IT/기술 뉴스의 키워드를 추출하는 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.3
        )
        
        keywords_text = response.choices[0].message.content.strip()
        keywords_list = [k.strip() for k in keywords_text.split(',') if k.strip()]
        
        # 불용어 및 한 글자 단어 필터링
        filtered_keywords = []
        for keyword in keywords_list:
            kw_lower = keyword.lower()
            if kw_lower not in STOPWORDS and len(keyword) > 1:
                if not keyword.isdigit():
                    filtered_keywords.append(keyword)
        
        return filtered_keywords[:8]
        
    except Exception as e:
        print(f"키워드 추출 오류: {e}")
        # 오류 시 기본 키워드 추출 로직 (간단한 방식)
        return extract_simple_keywords(text)

def extract_simple_keywords(text: str) -> List[str]:
    """간단한 키워드 추출 (백업 방식)"""
    keywords = []
    tech_terms = [
        'AI', '인공지능', '머신러닝', '딥러닝', '반도체', '5G', '6G',
        'IoT', '클라우드', '빅데이터', '블록체인', '메타버스', 'VR', 'AR',
        '로봇', '자동화', '스마트팩토리', '디지털전환', 'DX', '핀테크',
        '전기차', '자율주행', '배터리', '태양광', '풍력', '수소',
        '양자컴퓨팅', '사이버보안', '해킹', '랜섬웨어', '개인정보보호',
        '스타트업', '유니콘', '벤처캐피탈', 'IPO', 'M&A'
    ]
    
    text_lower = text.lower()
    for term in tech_terms:
        if term.lower() in text_lower:
            keywords.append(term)
    
    return keywords[:8]