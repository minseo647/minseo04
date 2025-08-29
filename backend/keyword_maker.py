import openai
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 공학/기술 관련 주요 키워드 (Whitelist)
TECH_KEYWORDS = [
    # 첨단 제조·기술 산업
    "반도체", "메모리", "시스템 반도체", "파운드리", "소자", "웨이퍼", "노광", "EUV", "장비", "소재",
    "자동차", "내연기관", "전기차", "자율주행", "모빌리티", "현대차", "테슬라", "배터리카",
    "이차전지", "배터리", "ESS", "양극재", "음극재", "전해질", "분리막",
    "디스플레이", "OLED", "QD", "마이크로 LED", "LCD",
    "로봇", "스마트팩토리", "산업자동화", "협동로봇",

    # 에너지·환경 산업
    "석유", "가스", "원자력", "태양광", "풍력", "수소", "신재생에너지",
    "탄소중립", "폐기물", "친환경", "수처리", "CCUS", "재활용",

    # 디지털·ICT 산업
    "AI", "인공지능", "머신러닝", "딥러닝", "생성형", "챗GPT", "로보틱스",
    "5G", "6G", "통신", "네트워크", "인프라", "클라우드", "SaaS",
    "소프트웨어", "메타버스", "보안", "핀테크", "플랫폼", "빅데이터", "블록체인",
    "VR", "AR", "가상현실", "증강현실", "디지털전환", "DX",

    # 바이오·헬스케어 산업
    "바이오", "제약", "신약", "바이오시밀러", "세포치료제", "유전자치료제",
    "의료기기", "헬스케어", "디지털 헬스", "웨어러블", "원격진료",

    # 소재·화학 산업
    "탄소소재", "나노소재", "고분자", "복합소재",
    "정밀화학", "석유화학", "케미컬", "특수가스", "반도체용 케미컬",

    # 인프라·기반 산업
    "철강", "조선", "건설", "스마트건설", "친환경 선박",
    "물류", "유통", "전자상거래", "스마트 물류", "공급망",
    "농업", "스마트팜", "대체식품", "식품", "푸드테크",

    # 기타 주요 기술 용어
    "IoT", "사물인터넷", "양자컴퓨팅", "사이버보안", "해킹", "랜섬웨어", "개인정보보호",
    "스타트업", "유니콘", "벤처캐피탈", "IPO", "M&A"
]

# 소문자로 변환하여 검색 용이하게
TECH_KEYWORDS_LOWER = [k.lower() for k in TECH_KEYWORDS]

def extract_keywords(text: str) -> List[str]:
    """텍스트에서 키워드를 추출하고, 정의된 기술 키워드 목록(Whitelist)으로 필터링합니다."""
    if not text:
        return []

    # 1. 텍스트에서 기술 키워드 직접 찾기 (기본)
    found_keywords = set()
    text_lower = text.lower()
    for keyword in TECH_KEYWORDS:
        if keyword.lower() in text_lower:
            found_keywords.add(keyword)

    # 2. OpenAI를 사용하여 추가 키워드 제안 받기 (선택적)
    if OPENAI_API_KEY:
        try:
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            prompt = f"""
            다음 텍스트에서 IT/기술 관련 핵심 키워드를 쉼표로 구분하여 10개만 추천해주세요.
            추천된 키워드는 다음 목록에 있는 단어와 유사해야 합니다: {', '.join(TECH_KEYWORDS[:20])}

            텍스트: {text[:1000]}
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 IT/기술 뉴스 키워드 추출 전문가입니다. 반드시 2글자 이상의 명사만 추천해주세요."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.2
            )
            
            gpt_keywords = response.choices[0].message.content.strip()
            gpt_keywords_list = [k.strip() for k in gpt_keywords.split(',') if k.strip()]

            # GPT가 제안한 키워드 중 Whitelist에 있는 것만 추가
            for kw in gpt_keywords_list:
                if kw.lower() in TECH_KEYWORDS_LOWER:
                    # Whitelist에 있는 원본 키워드를 추가 (대소문자 유지)
                    original_keyword_index = TECH_KEYWORDS_LOWER.index(kw.lower())
                    found_keywords.add(TECH_KEYWORDS[original_keyword_index])

        except Exception as e:
            print(f"OpenAI 키워드 추출 중 오류 발생 (기본 추출은 진행됨): {e}")

    # 최종적으로 찾은 키워드들을 리스트로 변환하여 반환
    return sorted(list(found_keywords))[:8]

def extract_simple_keywords(text: str) -> List[str]:
    """간단한 키워드 추출 (백업 방식) - Whitelist 기반"""
    keywords = set()
    text_lower = text.lower()
    for keyword in TECH_KEYWORDS:
        if keyword.lower() in text_lower:
            keywords.add(keyword)
    
    return sorted(list(keywords))[:8]