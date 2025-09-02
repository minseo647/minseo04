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
  '아','휴','아이구','아이쿠','아이고','어','나','우리','저희','따라',
              '의해','을','를','에','의','가','으로','로','에게','뿐이다','의거하여',
              '근거하여','입각하여','기준으로','예하면','예를','들자면','저', '소인',
              '소생', '저희', '지말고', '하지마', '하지마라', '다른', '물론', '또한',
              '그리고', '비길수', '없다', '해서는', '안된다', '뿐만', '아니라',
              '만이', '아니다', '만은', '막론하고', '관계없이', '그치지', '않다',
              '그러나', '그런데', '하지만', '든간에', '논하지', '따지지', '설사',
              '비록', '더라도', '아니면', '만', '못하다', '하는', '편이', '낫다',
              '불문하고', '향하여', '향해서', '향하다', '쪽으로', '틈타', '이용하여',
              '타다', '오르다', '제외하고', '이', '외에', '밖에', '하여야', '비로소',
              '한다면', '몰라도', '외에도', '이곳', '여기', '부터', '기점으로',
              '따라서', '할', '생각이다', '하려고하다', '이리하여', '그리하여',
              '그렇게', '함으로써', '일때', '할때', '앞에서', '중에서', '보는데서',
              '으로써', '로써', '까지', '해야한다', '일것이다', '반드시', '할줄알다',
              '할수있다', '할수있어', '임에', '틀림없다', '등', '등등', '제', '겨우',
              '단지', '다만', '할뿐', '딩동', '댕그', '대해서', '대하여', '대하면',
              '훨씬', '얼마나', '얼마만큼', '얼마큼', '남짓', '여', '얼마간', '약간',
              '다소', '좀', '조금', '다수', '몇', '얼마', '지만', '하물며', '그렇지만',
              '이외에도', '대해', '말하자면', '뿐이다', '다음에', '반대로', '이와',
              '바꾸어서', '말하면', '만약', '그렇지않으면', '까악', '툭', '딱',
              '삐걱거리다', '보드득', '비걱거리다', '꽈당', '응당', '에', '가서',
              '각', '각각', '여러분', '각종', '각자', '제각기', '하도록하다', '와',
              '과', '그러므로', '그래서', '고로', '한', '까닭에', '하기', '때문에',
              '거니와', '이지만', '관하여', '관한', '과연', '실로', '아니나다를가',
              '생각한대로', '진짜로', '한적이있다', '하곤하였다', '하', '하하',
              '허허', '아하', '거바', '오', '왜', '어째서', '무엇때문에', '어찌',
              '하겠는가', '무슨', '어디', '어느곳', '더군다나', '더욱이는', '어느때',
              '언제', '야', '이봐', '어이', '여보시오', '흐흐', '흥', '휴', '헉헉',
              '헐떡헐떡', '영차', '여차', '어기여차', '끙끙', '아야', '앗', '콸콸',
              '졸졸', '좍좍', '뚝뚝', '주룩주룩', '솨', '우르르', '그래도', '또',
              '바꾸어말하면', '바꾸어말하자면', '혹은', '혹시', '답다', '및', '그에',
              '따르는', '때가', '되어', '즉', '지든지', '설령', '가령', '하더라도',
              '할지라도', '일지라도', '거의', '하마터면', '인젠', '이젠', '된바에야',
              '된이상', '만큼', '어찌됏든', '그위에', '게다가', '점에서', '보아',
              '비추어', '고려하면', '하게될것이다', '비교적', '보다더', '비하면',
              '시키다', '하게하다', '할만하다', '의해서', '연이서', '이어서', '잇따라',
              '뒤따라', '뒤이어', '결국', '의지하여', '기대여', '통하여', '자마자',
              '더욱더', '불구하고', '얼마든지', '마음대로', '주저하지', '않고',
              '곧', '즉시', '바로', '당장', '하자마자', '하면된다', '그래', '그렇지',
              '요컨대', '다시', '바꿔', '구체적으로', '시작하여', '시초에', '이상',
              '허', '헉', '허걱', '바와같이', '해도좋다', '해도된다', '더구나',
              '와르르', '팍', '퍽', '펄렁', '동안', '이래', '하고있었다', '이었다',
              '에서', '로부터', '예하면', '했어요', '해요', '함께', '같이', '더불어',
              '마저', '마저도', '양자', '모두', '습니다', '가까스로', '즈음하여',
              '방면으로', '해봐요', '습니까', '말할것도', '없고', '무릎쓰고', '개의치않고',
              '하는것만', '하는것이', '매', '매번', '들', '모', '어느것', '어느',
              '갖고말하자면', '어느쪽', '어느해', '년도', '라', '해도', '언젠가',
              '어떤것', '저기', '저쪽', '저것', '그때', '그럼', '그러면', '요만한걸',
              '저것만큼', '그저', '이르기까지', '줄', '안다', '힘이', '있다', '너',
              '너희', '당신', '설마', '차라리', '할지언정', '할망정', '구토하다',
              '게우다', '토하다', '메쓰겁다', '옆사람', '퉤', '쳇', '의거하여',
              '근거하여', '의해', '따라', '힘입어', '그', '다음', '버금', '두번째로',
              '기타', '첫번째로', '나머지는', '그중에서', '견지에서', '형식으로',
              '쓰여', '입장에서', '위해서', '의해되다', '하도록시키다', '뿐만아니라',
              '전후', '전자', '앞의것', '잠시', '잠깐', '하면서', '그러한즉', '그런즉',
              '남들', '아무거나', '어찌하든지', '같다', '비슷하다', '예컨대', '이럴정도로',
              '어떻게', '만일', '위에서', '서술한바와같이', '인', '듯하다', '하지',
              '않는다면', '만약에', '무엇', '어떤', '아래윗', '조차', '한데', '그럼에도',
              '여전히', '심지어', '까지도', '조차도', '않도록', '않기', '위하여',
              '때', '시각', '무렵', '시간', '어때', '어떠한', '하여금', '네', '예',
              '우선', '누구', '누가', '알겠는가', '아무도', '줄은모른다', '몰랏다',
              '김에', '겸사겸사', '하는바', '그런', '이유는', '그러니', '그러니까',
              '그들', '너희들', '타인', '것', '것들', '공동으로', '동시에', '어찌하여',
              '붕붕', '윙윙', '나', '우리', '엉엉', '휘익', '오호', '어쨋든', '하기보다는',
              '놀라다', '상대적으로', '마치', '아니라면', '쉿', '않으면', '않다면',
              '안', '아니었다면', '하든지', '이라면', '좋아', '알았어', '하는것도',
              '그만이다', '어쩔수', '하나', '일', '일반적으로', '일단', '한켠으로는',
              '오자마자', '이렇게되면', '이와같다면', '전부', '한마디', '한항목',
              '근거로', '하기에', '아울러', '위해서', '되다', '로', '인하여', '까닭으로',
              '이유만으로', '이로', '결론을', '낼', '수', '으로', '관계가', '관련이',
              '연관되다', '여부', '하느니', '하면', '할수록', '운운', '이러이러하다',
              '하구나', '하도다', '다시말하면', '다음으로', '달려', '우리들', '오히려',
              '하기는한데', '어떻해', '어찌됏어', '본대로', '자', '이쪽', '이것',
              '이번', '이렇게말하자면', '이런', '이러한', '같은', '요만큼', '요만한',
              '되는', '정도의', '이렇게', '많은', '이때', '이렇구나', '것과', '사람들',
              '부류의', '왜냐하면', '중의하나', '오직', '오로지', '한하다', '하기만',
              '도착하다', '미치다', '도달하다', '정도에', '이르다', '지경이다',
              '결과에', '관해서는', '하고', '후', '혼자', '자기', '자기집', '자신',
              '우에', '종합한것과같이', '총적으로', '대로', '하다', '으로서', '참',
              '따름이다', '쿵', '탕탕', '쾅쾅', '둥둥', '봐', '봐라', '아이야',
              '와아', '응', '아이', '참나', '년', '월', '령', '영', '삼', '사',
              '육', '륙', '칠', '팔', '구', '이천육', '이천칠', '이천팔', '이천구',
              '둘', '셋', '넷', '다섯', '여섯', '일곱', '여덟', '아홉',
  // 영어 불용어 (확장)
  'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from',
  'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'among',
  'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
  'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'they',
  'them', 'their', 'we', 'us', 'our', 'you', 'your', 'he', 'him', 'his', 'she', 'her', 'it', 'its',
  'as', 'if', 'then', 'than', 'so', 'no', 'not', 'only', 'own', 'same', 'such', 'too', 'very', 'just',
  'now', 'here', 'there', 'where', 'when', 'what', 'who', 'which', 'why', 'how', 'all', 'any', 'both',
  'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
  'so', 'than', 'too', 'very', 'can', 'will', 'just', 'don', 'should', 'now', 'daily', 'weekly',
  'monthly', 'yearly', 'new', 'old', 'first', 'last', 'next', 'previous', 'big', 'small', 'large',
  'little', 'long', 'short', 'high', 'low', 'right', 'left', 'good', 'bad', 'better', 'best', 'worse',
  'worst', 'early', 'late', 'today', 'tomorrow', 'yesterday', 'week', 'month', 'year', 'day', 'time',
  'way', 'use', 'get', 'make', 'go', 'know', 'take', 'see', 'come', 'think', 'look', 'want', 'give',
  'work', 'find', 'become', 'tell', 'ask', 'try', 'call', 'need', 'feel', 'leave', 'put', 'mean',
  'keep', 'let', 'begin', 'seem', 'help', 'talk', 'turn', 'start', 'show', 'hear', 'play', 'run',
  'move', 'live', 'believe', 'hold', 'bring', 'happen', 'write', 'provide', 'sit', 'stand', 'lose',
  'pay', 'meet', 'include', 'continue', 'set', 'learn', 'change', 'lead', 'understand', 'watch',
  'follow', 'stop', 'create', 'speak', 'read', 'allow', 'add', 'spend', 'grow', 'open', 'walk',
  'win', 'offer', 'remember', 'love', 'consider', 'appear', 'buy', 'wait', 'serve', 'die', 'send',
  'expect', 'build', 'stay', 'fall', 'cut', 'reach', 'kill', 'remain', 'suggest', 'raise', 'pass',
  'sell', 'require', 'report', 'decide', 'pull', 'break', 'pick', 'wear', 'paper', 'system',
  'program', 'question', 'work', 'government', 'number', 'night', 'point', 'home', 'water', 'room',
  'mother', 'area', 'money', 'story', 'fact', 'month', 'lot', 'right', 'study', 'book', 'eye',
  'job', 'word', 'business', 'issue', 'side', 'kind', 'head', 'house', 'service', 'friend',
  'father', 'power', 'hour', 'game', 'line', 'end', 'member', 'law', 'car', 'city', 'community',
  'name', 'president', 'university', 'public', 'country', 'american', 'human', 'woman', 'man',
  'child', 'life', 'person', 'student', 'group', 'part', 'place', 'case', 'week', 'company',
  'where', 'party', 'education', 'real', 'run', 'thing', 'never', 'world', 'information',
  'over', 'think', 'also', 'its', 'after', 'use', 'two', 'how', 'our', 'work', 'life',
  'only', 'can', 'still', 'should', 'after', 'being', 'now', 'made', 'before', 'here',
  'through', 'when', 'much', 'go', 'see', 'no', 'way', 'could', 'my', 'than', 'first',
  'been', 'call', 'who', 'oil', 'sit', 'but', 'now', 'back', 'each', 'came', 'right',
  'took', 'set', 'until', 'away', 'always', 'music', 'close', 'night', 'real', 'almost',
  'enough', 'far', 'took', 'head', 'yet', 'government', 'system', 'better', 'told', 'nothing',
  'end', 'why', 'called', 'didn', 'look', 'find', 'come', 'made', 'may', 'part', 'over',
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