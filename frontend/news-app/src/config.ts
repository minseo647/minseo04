export const API_BASE_URL = import.meta.env.VITE_API_URL || 
  (import.meta.env.DEV ? 'http://localhost:8000' : 'https://news-api-backend2.onrender.com');

export const categories = {
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
};

// 타입 정의
export type Categories = typeof categories;
export type MajorCategory = keyof Categories;
export type MinorCategory<T extends MajorCategory> = keyof Categories[T];
export type AllMinorCategories = {
  [K in MajorCategory]: keyof Categories[K]
}[MajorCategory];

// 유틸리티 함수들
export const getMajorCategories = (): MajorCategory[] => Object.keys(categories) as MajorCategory[];

export const getMinorCategories = (majorCategory?: MajorCategory): string[] => {
  if (!majorCategory) return [];
  return Object.keys(categories[majorCategory]);
};

export const getAllMinorCategories = (): { [key: string]: string[] } => {
  const result: { [key: string]: string[] } = {};
  Object.values(categories).forEach(majorCat => {
    Object.entries(majorCat).forEach(([minorCat, keywords]) => {
      result[minorCat] = keywords;
    });
  });
  return result;
};

export const getCategoryKeywords = (majorCategory?: MajorCategory, minorCategory?: string): string[] => {
  if (!majorCategory && !minorCategory) return [];
  
  if (minorCategory && majorCategory && categories[majorCategory][minorCategory]) {
    return categories[majorCategory][minorCategory];
  }
  
  if (minorCategory && !majorCategory) {
    // 소분류만 선택된 경우, 모든 대분류에서 찾기
    for (const major of Object.values(categories)) {
      if (major[minorCategory]) {
        return major[minorCategory];
      }
    }
  }
  
  if (majorCategory && !minorCategory) {
    // 대분류만 선택된 경우, 해당 대분류의 모든 키워드
    const allKeywords: string[] = [];
    Object.values(categories[majorCategory]).forEach(keywords => {
      allKeywords.push(...keywords);
    });
    return allKeywords;
  }
  
  return [];
};

// 불용어 목록 (제거할 의미없는 단어들)
export const STOPWORDS = new Set([
  // 한글 조사, 어미, 의미없는 단어들
  '이', '가', '을', '를', '에', '의', '와', '과', '도', '은', '는', '에서', '으로', '로', '에게', '한테',
  '하다', '되다', '있다', '없다', '같다', '다른', '새로운', '좋은', '나쁜', '크다', '작다', '많다', '적다',
  '그', '이', '저', '그런', '이런', '저런', '것', '들', '등', '및', '또한', '하지만', '그러나', '따라서',
  '때문에', '위해', '통해', '대해', '관한', '관련', '경우', '때', '중', '후', '전', '동안', '사이',
  '년', '월', '일', '시간', '분', '초', '오늘', '어제', '내일', '지금', '현재', '과거', '미래',
  '한국', '미국', '중국', '일본', '유럽', '아시아', '서울', '부산', '대구', '인천', '광주', '대전', '울산',
  '회사', '기업', '업체', '업계', '산업', '분야', '시장', '고객', '사용자', '이용자', '소비자',
  '발표', '공개', '출시', '런칭', '시작', '종료', '완료', '진행', '계획', '예정', '목표', '성과', '결과',
  // 영어 불용어
  'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from',
  'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'among',
  'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
  'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'they',
  'them', 'their', 'we', 'us', 'our', 'you', 'your', 'he', 'him', 'his', 'she', 'her', 'it', 'its',
  // 한 글자 단어들
  '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'G', 'K', 'M', 'B', 'T', 'P'
]);

// 기술 키워드 화이트리스트 (카테고리에서 추출 + 추가 기술 용어)
export const TECH_KEYWORDS = new Set([
  // 카테고리에서 추출한 모든 키워드들
  ...Object.values(categories).flatMap(majorCat => 
    Object.values(majorCat).flatMap(keywords => keywords)
  ),
  
  // 추가 AI/ML 키워드
  'AI', '인공지능', '머신러닝', '딥러닝', '신경망', 'CNN', 'RNN', 'LSTM', 'GAN', 'GPT', 'ChatGPT', 'OpenAI',
  '자연어처리', 'NLP', '컴퓨터비전', '패턴인식', '강화학습', '지도학습', '비지도학습', '트랜스포머', 'BERT',
  'LLM', '대화형AI', '생성AI', '멀티모달', '파인튜닝', 'RAG', '프롬프트엔지니어링',
  
  // 추가 소프트웨어/프로그래밍
  'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Go', 'Rust', 'Swift', 'Kotlin', 'React', 'Vue', 'Angular',
  'Node.js', 'Django', 'Flask', 'Spring', '프레임워크', '라이브러리', 'API', 'REST', 'GraphQL', 'SDK',
  '오픈소스', '깃허브', 'GitHub', '버전관리', 'Git', '코딩', '프로그래밍', '개발자', '소프트웨어',
  'DevOps', 'CI/CD', '마이크로서비스', '컨테이너', 'Docker', 'Kubernetes',
  
  // 추가 클라우드/인프라
  'AWS', 'Azure', 'GCP', '구글클라우드', '클라우드', '서버리스', '가상화', 'VM', '하이브리드클라우드', '멀티클라우드',
  
  // 추가 데이터/빅데이터
  '빅데이터', '데이터사이언스', '데이터분석', '데이터마이닝', '데이터베이스', 'SQL', 'NoSQL', 'MongoDB',
  'PostgreSQL', 'MySQL', '데이터웨어하우스', '데이터레이크', 'ETL', 'ELT', 'Apache', 'Hadoop', 'Spark',
  '비즈니스인텔리전스', 'BI', '시각화', 'Tableau', '파워BI',
  
  // 추가 네트워크/통신
  '5G', '6G', 'LTE', 'WiFi', '블루투스', 'IoT', '사물인터넷', '무선통신', '네트워크', '라우터', '스위치',
  'VPN', '방화벽', 'CDN', '엣지컴퓨팅', '엣지', '네트워킹', '프로토콜', 'TCP', 'UDP', 'HTTP', 'HTTPS',
  
  // 추가 보안/사이버보안
  '사이버보안', '보안', '암호화', '해킹', '피싱', '랜섬웨어', '멀웨어', '바이러스', '취약점', 'CISO',
  '인증', '권한', 'SSO', '다중인증', 'MFA', '블록체인', '스마트컨트랙트', '비트코인', '이더리움',
  '제로트러스트', '침입탐지', '보안운영센터', 'SOC',
  
  // 추가 하드웨어/반도체
  '반도체', '칩', '프로세서', 'CPU', 'GPU', 'NPU', 'TPU', '메모리', 'RAM', 'SSD', 'HDD',
  '웨이퍼', '파운드리', 'TSMC', '삼성전자', 'SK하이닉스', '인텔', 'AMD', 'NVIDIA', '퀄컴',
  'OLED', '디스플레이', 'LCD', '마이크로LED', '센서', '카메라모듈',
  
  // 추가 자동차/모빌리티
  '전기차', 'EV', '자율주행', '테슬라', '현대차', '기아', '모빌리티', '배터리', '리튬배터리',
  'LiDAR', '레이더', '커넥티드카', 'V2X', '충전인프라', '급속충전',
  
  // 추가 로봇/자동화
  '로봇', '로보틱스', '자동화', 'RPA', '스마트팩토리', '산업자동화', '협동로봇', '드론', 'UAV',
  '3D프린팅', '적층제조', 'CNC', '스마트제조',
  
  // 추가 바이오/헬스케어
  '바이오', '바이오테크', '제약', '신약개발', '유전자', 'DNA', 'RNA', 'mRNA', '백신', '항체',
  '의료기기', '디지털헬스', '헬스케어', '원격의료', '텔레헬스', '웨어러블', '바이오센서',
  '정밀의학', '개인맞춤의료', 'AI진단', '의료AI',
  
  // 추가 에너지/환경
  '태양광', '풍력', '수소', '연료전지', '에너지저장장치', 'ESS', '스마트그리드', '신재생에너지',
  '탄소중립', '탄소포집', 'CCUS', '친환경', '그린테크', '청정기술',
  
  // 추가 게임/엔터테인먼트
  '게임엔진', 'Unity', 'Unreal', 'VR', '가상현실', 'AR', '증강현실', 'MR', '혼합현실', '메타버스',
  'NFT', 'P2E', '게임개발', '모바일게임', 'PC게임', '콘솔게임',
  
  // 추가 핀테크/금융기술
  '핀테크', '디지털뱅킹', '모바일페이', '간편결제', 'CBDC', '디지털화폐', '크라우드펀딩',
  '로보어드바이저', '인슈어테크', 'RegTech', '디지털금융',
  
  // 추가 신기술
  '양자컴퓨팅', '양자', '나노기술', '신소재', '탄소나노튜브', '그래핀', '슈퍼컴퓨터', 'HPC',
  '엣지AI', '온디바이스AI', 'TinyML', '디지털트윈', 'API경제', 'SaaS', 'PaaS', 'IaaS'
]);

// 의미있는 토큰인지 확인하는 함수
export const isMeaningfulToken = (token: string): boolean => {
  const cleanToken = token.trim();
  
  // 길이 체크 (1글자 제외, 단 영문 약어는 허용)
  if (cleanToken.length <= 1) {
    return false;
  }
  
  // 한글 1글자는 제외
  if (cleanToken.length === 1 && /[\uAC00-\uD7A3]/.test(cleanToken)) {
    return false;
  }
  
  // 불용어 체크
  if (STOPWORDS.has(cleanToken.toLowerCase())) {
    return false;
  }
  
  // 숫자만으로 구성된 경우 제외 (단, 기술 관련 숫자는 허용)
  if (/^\d+$/.test(cleanToken) && !TECH_KEYWORDS.has(cleanToken)) {
    return false;
  }
  
  return true;
};

// 기술 관련 용어인지 확인하는 함수
export const isTechTerm = (token: string): boolean => {
  const cleanToken = token.trim();
  
  // 화이트리스트에 있는 경우
  if (TECH_KEYWORDS.has(cleanToken)) {
    return true;
  }
  
  // 대소문자 무시하고 체크
  for (const techKeyword of TECH_KEYWORDS) {
    if (techKeyword.toLowerCase() === cleanToken.toLowerCase()) {
      return true;
    }
  }
  
  // 부분 매칭 (기술 키워드가 포함된 경우)
  for (const techKeyword of TECH_KEYWORDS) {
    if (techKeyword.toLowerCase().includes(cleanToken.toLowerCase()) || 
        cleanToken.toLowerCase().includes(techKeyword.toLowerCase())) {
      return true;
    }
  }
  
  return false;
};