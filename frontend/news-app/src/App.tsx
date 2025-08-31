import React, { useState, useEffect, useRef } from 'react';
import {
  Typography,
  Box,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  CircularProgress,
  Paper,
  Chip,
  Card,
  CardContent,
  Stack,
  Divider,
  Button,
  Tabs,
  Tab,
  IconButton,
  Grid,
  Container,
  AppBar,
  Toolbar,
  Drawer,
  Switch,
  FormControlLabel,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Pagination,
  Tooltip,
  Badge,
} from '@mui/material';
import {
  Article as ArticleIcon,
  Favorite,
  FavoriteBorder,
  Analytics,
  Cloud,
  Search,
  Refresh,
  FilterList,
  TrendingUp,
  OpenInNew,
  DarkMode,
  LightMode,
  AccessTime,
  Keyboard,
  Visibility,
} from '@mui/icons-material';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

import { newsApi } from './api/newsApi';
import { newsService } from './services/newsService';
import type { Article, KeywordStats } from './api/newsApi';
import { KeywordCloud } from './components/KeywordCloud';
import { KeywordNetwork } from './components/KeywordNetwork';
import { ColorPalette } from './components/ColorPalette';
import { InsightsCharts } from './components/InsightsCharts';
import { useThemeProvider } from './hooks/useTheme';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';
import { calculateReadingTime, formatReadingTime } from './utils/readingTime';
import { categories, getMajorCategories, getMinorCategories, getAllMinorCategories, type MajorCategory, STOPWORDS, TECH_KEYWORDS, isMeaningfulToken, isTechTerm } from './config';


interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index } = props;
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

// 개별 기사 카드 컴포넌트 (개선된 디자인)
interface ArticleCardProps {
  article: Article;
  onToggleFavorite: (id: number) => void;
  onExtractKeywords?: (id: number) => void;
  onTranslate?: (id: number) => void;
}

// 키워드 네트워크 컨테이너 컴포넌트
function KeywordNetworkContainer({ articles }: { articles: Article[] }) {
  const [networkData, setNetworkData] = useState<any>({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const generateNetworkData = () => {
      try {
        // 키워드 공통 출현 분석으로 네트워크 생성
        const keywordCounts: Record<string, number> = {};
        const keywordPairs: Record<string, number> = {};
        
        articles.forEach(article => {
          const keywords: string[] = [];
          
          // 키워드 추출
          if (Array.isArray(article.keywords)) {
            keywords.push(...article.keywords);
          } else if (typeof article.keywords === 'string' && article.keywords) {
            try {
              const parsed = article.keywords.startsWith('[') 
                ? JSON.parse(article.keywords) 
                : article.keywords.split(',');
              keywords.push(...parsed.map(k => k.trim()));
            } catch (e) {
              keywords.push(...article.keywords.split(',').map(k => k.trim()));
            }
          }
          
          // 키워드 카운트
          keywords.forEach(keyword => {
            const cleanKeyword = keyword.trim().replace(/['"]/g, '');
            if (cleanKeyword && isMeaningfulToken(cleanKeyword) && isTechTerm(cleanKeyword)) {
              keywordCounts[cleanKeyword] = (keywordCounts[cleanKeyword] || 0) + 1;
            }
          });
          
          // 키워드 쌍 분석 (같은 기사에 등장하는 키워드들)
          const uniqueKeywords = [...new Set(keywords.map(k => k.trim().replace(/['"]/g, '')))];
          for (let i = 0; i < uniqueKeywords.length; i++) {
            for (let j = i + 1; j < uniqueKeywords.length; j++) {
              const k1 = uniqueKeywords[i];
              const k2 = uniqueKeywords[j];
              if (k1 && k2 && isMeaningfulToken(k1) && isMeaningfulToken(k2) && isTechTerm(k1) && isTechTerm(k2)) {
                const pairKey = [k1, k2].sort().join('|');
                keywordPairs[pairKey] = (keywordPairs[pairKey] || 0) + 1;
              }
            }
          }
        });
        
        // 상위 키워드만 선택 (노드)
        const topKeywords = Object.entries(keywordCounts)
          .sort(([,a], [,b]) => b - a)
          .slice(0, 15)
          .map(([keyword, count]) => ({ keyword, count }));
          
        const keywordSet = new Set(topKeywords.map(k => k.keyword));
        
        // 노드 생성
        const nodes = topKeywords.map(({ keyword, count }, index) => ({
          id: index,
          label: keyword,
          value: count,
          color: `hsl(${(index * 360) / topKeywords.length}, 70%, 50%)`
        }));
        
        // 엣지 생성 (상위 키워드 간의 연결만)
        const edges: any[] = [];
        Object.entries(keywordPairs).forEach(([pairKey, count]) => {
          const [k1, k2] = pairKey.split('|');
          if (keywordSet.has(k1) && keywordSet.has(k2) && count >= 2) { // 2회 이상 공통 출현
            const from = nodes.find(n => n.label === k1)?.id;
            const to = nodes.find(n => n.label === k2)?.id;
            if (from !== undefined && to !== undefined) {
              edges.push({ from, to, value: count });
            }
          }
        });
        
        console.log('🕸️ 키워드 네트워크 생성:', { nodes: nodes.length, edges: edges.length });
        setNetworkData({ nodes, edges });
      } catch (error) {
        console.error('Failed to generate network data:', error);
        setNetworkData({ nodes: [], edges: [] });
      } finally {
        setLoading(false);
      }
    };

    generateNetworkData();
  }, [articles]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  return <KeywordNetwork data={networkData} />;
}

function ArticleCard({ article, onToggleFavorite, onExtractKeywords, onTranslate }: ArticleCardProps) {
  const readingTime = calculateReadingTime((article.title || '') + (article.summary || ''));
  
  return (
    <Card sx={{ 
      mb: 2.5, 
      transition: 'all 0.3s ease-in-out', 
      '&:hover': { 
        transform: 'translateY(-2px)',
        boxShadow: '0 8px 25px rgba(0, 0, 0, 0.15)'
      },
      borderRadius: 3,
      overflow: 'hidden'
    }}>
      <CardContent sx={{ p: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={11}>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5, mb: 2 }}>
              <Box sx={{ flex: 1 }}>
                <Typography variant="h6" sx={{ 
                  fontWeight: 700, 
                  mb: 1.5,
                  lineHeight: 1.4,
                  fontSize: { xs: '1.05rem', md: '1.15rem' }
                }}>
                  <a href={article.link} target="_blank" rel="noopener noreferrer" 
                     style={{ 
                       textDecoration: 'none', 
                       color: 'inherit'
                     }}>
                    {article.title}
                    <OpenInNew fontSize="small" sx={{ ml: 1, verticalAlign: 'middle', opacity: 0.7 }} />
                  </a>
                </Typography>
              </Box>
            </Box>
            
            <Stack direction="row" spacing={{ xs: 1, md: 2 }} sx={{ mb: 2, flexWrap: 'wrap', gap: 1 }}>
              <Chip
                icon={<ArticleIcon fontSize="small" />}
                label={article.source}
                variant="outlined"
                size="small"
                color="primary"
              />
              <Chip
                icon={<AccessTime fontSize="small" />}
                label={new Date(article.published).toLocaleDateString('ko-KR')}
                variant="outlined"
                size="small"
              />
              <Chip
                icon={<Visibility fontSize="small" />}
                label={formatReadingTime(readingTime)}
                variant="outlined"
                size="small"
                color="secondary"
              />
            </Stack>

            {article.summary && (
              <Typography variant="body1" sx={{ 
                mb: 2, 
                lineHeight: 1.7,
                color: 'text.secondary',
                fontSize: '0.95rem'
              }}>
                {article.summary.length > 200 
                  ? `${article.summary.substring(0, 200)}...` 
                  : article.summary}
              </Typography>
            )}

            {article.keywords && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" component="div" sx={{ mb: 1, fontWeight: 600 }}>
                  🏷️ 키워드
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {typeof article.keywords === 'string' 
                    ? article.keywords.split(',').slice(0, 8).map((keyword: string, index: number) => (
                        <Chip 
                          key={index} 
                          label={keyword.trim()} 
                          size="small"
                          variant="outlined"
                          sx={{ 
                            fontSize: '0.75rem',
                            height: 24,
                            borderRadius: 3,
                            '&:hover': {
                              backgroundColor: 'primary.main',
                              color: 'primary.contrastText',
                              borderColor: 'primary.main'
                            }
                          }} 
                        />
                      ))
                    : Array.isArray(article.keywords) 
                      ? article.keywords.slice(0, 8).map((keyword: string, index: number) => (
                          <Chip 
                            key={index} 
                            label={keyword} 
                            size="small"
                            variant="outlined"
                            sx={{ 
                              fontSize: '0.75rem',
                              height: 24,
                              borderRadius: 3,
                              '&:hover': {
                                backgroundColor: 'primary.main',
                                color: 'primary.contrastText',
                                borderColor: 'primary.main'
                              }
                            }} 
                          />
                        ))
                      : null
                  }
                </Box>
              </Box>
            )}
          </Grid>
          
          <Grid item xs={12} sm={1} sx={{ display: 'flex', justifyContent: { xs: 'flex-end', sm: 'center' } }}>
            <Stack spacing={1} alignItems="center">
              <Tooltip title={article.is_favorite ? '즐겨찾기 해제' : '즐겨찾기 추가'}>
                <IconButton 
                  onClick={() => onToggleFavorite(article.id)}
                  color={article.is_favorite ? "secondary" : "default"}
                  sx={{
                    transition: 'all 0.2s',
                    '&:hover': {
                      transform: 'scale(1.1)'
                    }
                  }}
                >
                  {article.is_favorite ? <Favorite /> : <FavoriteBorder />}
                </IconButton>
              </Tooltip>
              {onExtractKeywords && (
                <Tooltip title="키워드 추출">
                  <IconButton 
                    onClick={() => onExtractKeywords(article.id)}
                    size="small"
                  >
                    <TrendingUp fontSize="small" />
                  </IconButton>
                </Tooltip>
              )}
              {onTranslate && (
                <Tooltip title="번역">
                  <IconButton 
                    onClick={() => onTranslate(article.id)}
                    size="small"
                  >
                    🌐
                  </IconButton>
                </Tooltip>
              )}
              <Typography variant="caption" color="text.secondary">
                #{article.id}
              </Typography>
            </Stack>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
}

// 키보드 단축키 도움말 컴포넌트
function KeyboardShortcutsHelp() {
  return (
    <Paper sx={{ p: 2, mb: 2, bgcolor: 'action.hover' }}>
      <Typography variant="body2" sx={{ mb: 1, fontWeight: 600 }}>
        ⌨️ 키보드 단축키
      </Typography>
      <Stack spacing={0.5}>
        <Typography variant="body2">• Ctrl/Cmd + R: 뉴스 새로고침</Typography>
        <Typography variant="body2">• Ctrl/Cmd + D: 다크모드 토글</Typography>
        <Typography variant="body2">• Ctrl/Cmd + K: 검색 포커스</Typography>
        <Typography variant="body2">• Ctrl/Cmd + ←/→: 탭 전환</Typography>
      </Stack>
    </Paper>
  );
}

// 메인 App 컴포넌트
export default function App() {
  const { isDarkMode, toggleTheme, theme, colors, ThemeContext } = useThemeProvider();
  const [tabValue, setTabValue] = useState(0);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const [articles, setArticles] = useState<Article[]>([]);
  const [filteredArticles, setFilteredArticles] = useState<Article[]>([]);
  const [keywordStats, setKeywordStats] = useState<KeywordStats[]>([]);
  const [loading, setLoading] = useState(false);
  const [collecting, setCollecting] = useState(false);
  const [collections, setCollections] = useState<any[]>([]);
  
  // 필터 상태
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSource, setSelectedSource] = useState('all');
  const [dateFrom, setDateFrom] = useState(() => {
    const date = new Date();
    date.setDate(date.getDate() - 7);
    return date.toISOString().split('T')[0];
  });
  const [dateTo, setDateTo] = useState(() => new Date().toISOString().split('T')[0]);
  const [favoritesOnly, setFavoritesOnly] = useState(false);
  const [selectedMajorCategory, setSelectedMajorCategory] = useState<MajorCategory | null>(null);
  const [selectedMinorCategory, setSelectedMinorCategory] = useState<string | null>(null);
  
  // 페이지네이션
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;
  
  // 사이드바 - 데스크톱에서는 항상 고정
  const [drawerOpen, setDrawerOpen] = useState(true);
  const [showShortcutsHelp] = useState(false);
  const [isDesktop, setIsDesktop] = useState(window.innerWidth >= 1024);

  // 화면 크기 감지
  useEffect(() => {
    const handleResize = () => {
      const desktop = window.innerWidth >= 1024;
      setIsDesktop(desktop);
      // 초기화 시에만 데스크톱 기본값 설정
    };

    window.addEventListener('resize', handleResize);
    handleResize(); // 초기 실행

    return () => window.removeEventListener('resize', handleResize);
  }, []); // drawerOpen 의존성 제거

  // 초기 데이터 로드 - 백엔드 API 우선 사용
  useEffect(() => {
    const loadInitialData = async () => {
      setLoading(true);
      try {
        console.log('🔄 백엔드에서 데이터 로딩 중...');
        
        // 백엔드 API에서 JSON 데이터 로드
        try {
          const params = new URLSearchParams({
            limit: '1000',
            use_json: 'true'
          });
          
          const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/articles?${params}`);
          if (response.ok) {
            const backendArticles = await response.json();
            console.log(`✅ 백엔드에서 ${backendArticles.length}개 기사 로드 성공`);
            
            // 백엔드 데이터를 프론트엔드 형식으로 변환
            const formattedArticles = backendArticles.map((article: any, index: number) => ({
              id: article.id || index + 1,
              title: article.title || '제목 없음',
              link: article.link || '#',
              published: article.published || new Date().toISOString(),
              source: article.source || '알 수 없음',
              summary: article.summary || '',
              keywords: Array.isArray(article.keywords) ? article.keywords :
                        typeof article.keywords === 'string' ? 
                        (article.keywords.startsWith('[') ? JSON.parse(article.keywords) : article.keywords.split(',').map(k => k.trim())) : 
                        [],
              is_favorite: article.is_favorite || false
            }));
            
            setArticles(formattedArticles);
            
            // 키워드 통계 생성 (필터링 적용)
            const keywordCounter: Record<string, number> = {};
            formattedArticles.forEach((article: any) => {
              if (article.keywords && Array.isArray(article.keywords)) {
                article.keywords.forEach((keyword: string) => {
                  const cleanKeyword = keyword.trim();
                  if (cleanKeyword && isMeaningfulToken(cleanKeyword) && isTechTerm(cleanKeyword)) {
                    keywordCounter[cleanKeyword] = (keywordCounter[cleanKeyword] || 0) + 1;
                  }
                });
              } else if (typeof article.keywords === 'string' && article.keywords) {
                // JSON 문자열이나 쉼표로 구분된 키워드 처리
                try {
                  const keywords = article.keywords.startsWith('[') 
                    ? JSON.parse(article.keywords) 
                    : article.keywords.split(',');
                  
                  keywords.forEach((keyword: string) => {
                    const cleanKeyword = keyword.trim().replace(/['"]/g, '');
                    if (cleanKeyword && isMeaningfulToken(cleanKeyword) && isTechTerm(cleanKeyword)) {
                      keywordCounter[cleanKeyword] = (keywordCounter[cleanKeyword] || 0) + 1;
                    }
                  });
                } catch (e) {
                  console.debug('키워드 파싱 오류:', e);
                }
              }
            });
            
            const keywordStats = Object.entries(keywordCounter)
              .sort(([,a], [,b]) => b - a)
              .slice(0, 50)
              .map(([keyword, count]) => ({ keyword, count }));
            
            setKeywordStats(keywordStats);
            console.log(`✅ 키워드 통계 생성: ${keywordStats.length}개`);
            
            setCollections([]);
            return; // 백엔드 데이터 로드 성공시 여기서 종료
          }
        } catch (backendError) {
          console.warn('⚠️ 백엔드 API 연결 실패, 프론트엔드 캐시 확인 중...', backendError);
        }
        
        // 백엔드 실패시 프론트엔드 캐시 확인
        if (newsService.isCacheValid()) {
          console.log('📂 프론트엔드 캐시에서 로딩...');
          const cachedArticles = newsService.getFilteredArticles({});
          setArticles(cachedArticles);
          const keywordStats = newsService.getKeywordStats();
          setKeywordStats(keywordStats);
        } else {
          console.log('🔄 캐시도 없음, 경량 뉴스 수집...');
          // 백엔드도 실패하고 캐시도 없으면 경량 수집
          const freshArticles = await newsService.collectNews(5); // 매우 적은 수량만
          setArticles(freshArticles);
          const keywordStats = newsService.getKeywordStats();
          setKeywordStats(keywordStats);
        }
        
        setCollections([]);
        
      } catch (error) {
        console.error('❌ 데이터 로딩 실패:', error);
        // 완전 실패시 빈 상태
        setArticles([]);
        setKeywordStats([]);
        setCollections([]);
      } finally {
        setLoading(false);
      }
    };

    loadInitialData();
  }, []);

  // 필터 적용 - 백엔드 API 호출로 변경
  useEffect(() => {
    const applyFilters = async () => {
      console.log('🔍 Filter useEffect triggered - searchTerm:', searchTerm, 'selectedSource:', selectedSource, 'categories:', selectedMajorCategory, selectedMinorCategory);
      
      try {
        const params = new URLSearchParams({
          limit: '1000',
          offset: '0',
          use_json: 'true'
        });
        
        if (searchTerm) params.set('search', searchTerm);
        if (selectedSource && selectedSource !== 'all') params.set('source', selectedSource);
        if (dateFrom) params.set('date_from', dateFrom);
        if (dateTo) params.set('date_to', dateTo);
        if (favoritesOnly) params.set('favorites_only', 'true');
        if (selectedMajorCategory) params.set('major_category', selectedMajorCategory);
        if (selectedMinorCategory) params.set('minor_category', selectedMinorCategory);

        const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/articles?${params}`);
        
        if (response.ok) {
          const backendArticles = await response.json();
          
          // 백엔드 데이터를 프론트엔드 형식으로 변환
          const formattedArticles = backendArticles.map((article: any, index: number) => ({
            id: article.id || index + 1,
            title: article.title || '제목 없음',
            link: article.link || '#',
            published: article.published || new Date().toISOString(),
            source: article.source || '알 수 없음',
            summary: article.summary || '',
            keywords: Array.isArray(article.keywords) ? article.keywords :
                      typeof article.keywords === 'string' ? 
                      (article.keywords.startsWith('[') ? JSON.parse(article.keywords) : article.keywords.split(',').map(k => k.trim())) : 
                      [],
            is_favorite: article.is_favorite || false
          }));
          
          console.log('🔍 Filtered articles from backend:', formattedArticles.length);
          setFilteredArticles(formattedArticles);
        } else {
          // 백엔드 실패시 프론트엔드 필터링으로 폴백
          console.log('⚠️ Backend filtering failed, using frontend filtering');
          let filtered = [...articles];

          if (searchTerm) {
            const searchLower = searchTerm.toLowerCase();
            filtered = filtered.filter(article => 
              article.title?.toLowerCase().includes(searchLower) ||
              article.summary?.toLowerCase().includes(searchLower) ||
              (typeof article.keywords === 'string' 
                ? article.keywords.toLowerCase().includes(searchLower)
                : Array.isArray(article.keywords) 
                  ? article.keywords.some(k => k.toLowerCase().includes(searchLower))
                  : false)
            );
          }

          if (selectedSource && selectedSource !== 'all') {
            filtered = filtered.filter(article => article.source === selectedSource);
          }

          if (dateFrom) {
            filtered = filtered.filter(article => 
              new Date(article.published) >= new Date(dateFrom)
            );
          }

          if (dateTo) {
            filtered = filtered.filter(article => 
              new Date(article.published) <= new Date(dateTo)
            );
          }

          if (favoritesOnly) {
            filtered = filtered.filter(article => article.is_favorite);
          }

          filtered.sort((a, b) => 
            new Date(b.published).getTime() - new Date(a.published).getTime()
          );
          
          setFilteredArticles(filtered);
        }
        
        // 필터링된 데이터 기준으로 키워드 통계 재계산
        updateKeywordStatsFromFiltered();
        
      } catch (error) {
        console.error('Error applying filters:', error);
        setFilteredArticles(articles); // 오류시 전체 기사 표시
      }
      
      setCurrentPage(1);
    };

    applyFilters();
  }, [articles, searchTerm, selectedSource, dateFrom, dateTo, favoritesOnly, selectedMajorCategory, selectedMinorCategory]);

  // 필터링된 데이터 기준으로 키워드 통계 업데이트
  const updateKeywordStatsFromFiltered = () => {
    const keywordCounter: Record<string, number> = {};
    filteredArticles.forEach((article: any) => {
      if (article.keywords && Array.isArray(article.keywords)) {
        article.keywords.forEach((keyword: string) => {
          const cleanKeyword = keyword.trim();
          if (cleanKeyword && isMeaningfulToken(cleanKeyword) && isTechTerm(cleanKeyword)) {
            keywordCounter[cleanKeyword] = (keywordCounter[cleanKeyword] || 0) + 1;
          }
        });
      } else if (typeof article.keywords === 'string' && article.keywords) {
        try {
          const keywords = article.keywords.startsWith('[') 
            ? JSON.parse(article.keywords) 
            : article.keywords.split(',');
          
          keywords.forEach((keyword: string) => {
            const cleanKeyword = keyword.trim().replace(/['"]/g, '');
            if (cleanKeyword && isMeaningfulToken(cleanKeyword) && isTechTerm(cleanKeyword)) {
              keywordCounter[cleanKeyword] = (keywordCounter[cleanKeyword] || 0) + 1;
            }
          });
        } catch (e) {
          console.debug('키워드 파싱 오류:', e);
        }
      }
    });
    
    const keywordStats = Object.entries(keywordCounter)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 50)
      .map(([keyword, count]) => ({ keyword, count }));
    
    setKeywordStats(keywordStats);
  };

  // Enhanced news collection using backend API
  const collectNews = async () => {
    setCollecting(true);
    
    try {
      console.log('🚀 [데이터 수집 현황] 백엔드 API를 통한 뉴스 수집 시작...');
      
      const startTime = Date.now();
      
      // 백엔드 경량 수집 API 호출 (서버 안정성 우선)
      try {
        const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/collect-news-light`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          const result = await response.json();
          const duration = (Date.now() - startTime) / 1000;
          
          console.log('✅ [데이터 수집 현황] 백엔드 수집 완료:', result);
          
          // 성공 메시지
          const message = `✅ ${result.message || '경량 뉴스 수집 완료'} (${Math.round(duration)}초)\n` +
            `• 수집 방식: ${result.method || '경량 RSS'}\n` +
            `• 신규 기사: ${result.collected || 0}개\n` +
            `• 서버 부하 최소화로 안정성 우선 수집`;
          
          alert(message);
          
          // 백엔드에서 업데이트된 데이터 다시 로드
          console.log('🔄 [데이터 수집 현황] 업데이트된 데이터 로딩 중...');
          const articlesResponse = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/articles?limit=1000&use_json=true`);
          if (articlesResponse.ok) {
            const updatedArticles = await articlesResponse.json();
            
            const formattedArticles = updatedArticles.map((article: any, index: number) => ({
              id: article.id || index + 1,
              title: article.title || '제목 없음',
              link: article.link || '#',
              published: article.published || new Date().toISOString(),
              source: article.source || '알 수 없음',
              summary: article.summary || '',
              keywords: Array.isArray(article.keywords) ? article.keywords :
                        typeof article.keywords === 'string' ? 
                        (article.keywords.startsWith('[') ? JSON.parse(article.keywords) : article.keywords.split(',').map(k => k.trim())) : 
                        [],
              is_favorite: article.is_favorite || false
            }));
            
            // 기존 데이터와 새로 수집된 데이터 통합
            setArticles(prevArticles => {
              const combined = [...prevArticles];
              let newCount = 0;
              
              formattedArticles.forEach(newArticle => {
                // 중복 체크 (link 기준)
                const exists = combined.find(existing => existing.link === newArticle.link);
                if (!exists) {
                  combined.push(newArticle);
                  newCount++;
                }
              });
              
              console.log(`✅ [데이터 수집 현황] 총 ${combined.length}개 기사 (${newCount}개 신규 추가)`);
              return combined;
            });
            
            // 키워드 통계 재생성 (필터링 적용)
            const keywordCounter: Record<string, number> = {};
            formattedArticles.forEach((article: any) => {
              if (article.keywords && Array.isArray(article.keywords)) {
                article.keywords.forEach((keyword: string) => {
                  const cleanKeyword = keyword.trim();
                  if (cleanKeyword && isMeaningfulToken(cleanKeyword) && isTechTerm(cleanKeyword)) {
                    keywordCounter[cleanKeyword] = (keywordCounter[cleanKeyword] || 0) + 1;
                  }
                });
              } else if (typeof article.keywords === 'string' && article.keywords) {
                try {
                  const keywords = article.keywords.startsWith('[') 
                    ? JSON.parse(article.keywords) 
                    : article.keywords.split(',');
                  
                  keywords.forEach((keyword: string) => {
                    const cleanKeyword = keyword.trim().replace(/['"]/g, '');
                    if (cleanKeyword && isMeaningfulToken(cleanKeyword) && isTechTerm(cleanKeyword)) {
                      keywordCounter[cleanKeyword] = (keywordCounter[cleanKeyword] || 0) + 1;
                    }
                  });
                } catch (e) {
                  console.debug('키워드 파싱 오류:', e);
                }
              }
            });
            
            const keywordStats = Object.entries(keywordCounter)
              .sort(([,a], [,b]) => b - a)
              .slice(0, 50)
              .map(([keyword, count]) => ({ keyword, count }));
            
            setKeywordStats(keywordStats);
            
            // 필터 초기화
            setSearchTerm('');
            setSelectedSource('all');
            setDateFrom('');
            setDateTo('');
            setFavoritesOnly(false);
            setSelectedMajorCategory(null);
            setSelectedMinorCategory(null);
            
            return; // 백엔드 수집 성공시 여기서 종료
          }
        }
      } catch (backendError) {
        console.warn('⚠️ [데이터 수집 현황] 백엔드 수집 실패, 프론트엔드 수집으로 폴백:', backendError);
      }
      
      // 백엔드 실패시 프론트엔드 경량 수집
      console.log('🔄 [데이터 수집 현황] 프론트엔드 경량 수집으로 폴백...');
      localStorage.removeItem('news_articles');
      localStorage.removeItem('news_last_update');
      
      const collectedArticles = await newsService.collectNews(5); // 매우 제한적으로
      const duration = (Date.now() - startTime) / 1000;
      
      const validArticles = collectedArticles?.filter(article => 
        article && article.id && article.title && article.title.length > 0
      ) || [];

      if (validArticles && validArticles.length > 0) {
        const message = `✅ 경량 뉴스 수집 완료 (${Math.round(duration)}초)\n` +
          `• 수집된 기사: ${validArticles.length}개\n` + 
          `• 백엔드 연결 실패로 제한적 수집`;
        
        alert(message);
        setArticles(validArticles);
        
        const stats = newsService.getKeywordStats();
        setKeywordStats(stats);
        
        setSearchTerm('');
        setSelectedSource('all');
        setDateFrom('');
        setDateTo('');
        setFavoritesOnly(false);
        setSelectedMajorCategory(null);
        setSelectedMinorCategory(null);
      } else {
        alert('⚠️ 뉴스 수집에 실패했습니다. 네트워크 연결을 확인해주세요.');
      }
      
    } catch (error) {
      console.error('❌ [데이터 수집 현황] 뉴스 수집 최종 실패:', error);
      
      let errorMessage = '뉴스 수집 중 오류가 발생했습니다.';
      if (error instanceof Error) {
        if (error.message.includes('fetch')) {
          errorMessage += '\n네트워크 연결을 확인해주세요.';
        } else if (error.message.includes('timeout')) {
          errorMessage += '\n요청 시간이 초과되었습니다.';
        } else {
          errorMessage += `\n오류 내용: ${error.message}`;
        }
      }
      errorMessage += '\n\n다시 시도해주세요.';
      alert(`❌ ${errorMessage}`);
      
    } finally {
      setCollecting(false);
      console.log('📝 [데이터 수집 현황] 모든 수집 프로세스 완료');
    }
  };

  // 즐겨찾기 토글 - newsService 사용
  const handleToggleFavorite = async (articleId: number) => {
    try {
      const article = articles.find(a => a.id === articleId);
      if (!article) return;

      // Use newsService for local favorite management
      newsService.toggleFavorite(articleId);

      // 로컬 상태 업데이트
      setArticles(prev => prev.map(a => 
        a.id === articleId ? { ...a, is_favorite: !a.is_favorite } : a
      ));

      // Try to sync with backend (optional, non-blocking)
      try {
        if (article.is_favorite) {
          await newsApi.addFavorite(articleId);
        } else {
          await newsApi.removeFavorite(articleId);
        }
      } catch (backendError) {
        console.warn('Backend sync failed for favorite:', backendError);
      }
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
    }
  };

  // 컬렉션 생성
  const handleCreateCollection = async () => {
    const name = prompt('새 컬렉션 이름을 입력하세요:');
    if (!name) return;
    
    const keywords = prompt('관련 키워드를 쉼표로 구분하여 입력하세요 (예: AI, 클라우드, 보안):');
    const rules = keywords ? { include_keywords: keywords.split(',').map(k => k.trim()) } : {};
    
    try {
      // Collections feature disabled (backend not available)
      alert(`컬렉션 기능은 현재 사용할 수 없습니다 (백엔드 연결 필요).`);
    } catch (error) {
      console.error('Failed to create collection:', error);
      alert('컬렉션 생성에 실패했습니다.');
    }
  };

  // 키워드 추출 (백엔드 기능 비활성화)
  const handleExtractKeywords = async (articleId: number) => {
    alert('키워드 추출 기능은 현재 사용할 수 없습니다 (백엔드 연결 필요).');
  };

  // 번역 (백엔드 기능 비활성화)
  const handleTranslate = async (articleId: number) => {
    alert('번역 기능은 현재 사용할 수 없습니다 (백엔드 연결 필요).');
  };

  // 요약 자동 생성
  const handleEnhanceSummaries = async () => {
    if (collecting) return;
    
    setCollecting(true);
    
    try {
      console.log('🤖 요약 자동 생성 시작...');
      
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/enhance-summaries?limit=50`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const result = await response.json();
        
        console.log('✅ 요약 생성 완료:', result);
        
        const message = `✅ 요약 자동 생성 완료!\n` +
          `• 처리된 기사: ${result.total}개\n` +
          `• 새로 생성된 요약: ${result.enhanced}개\n` + 
          `• 실패: ${result.failed}개`;
        
        alert(message);
        
        // 데이터 새로고침
        const articlesResponse = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/articles?limit=1000&use_json=true`);
        if (articlesResponse.ok) {
          const updatedArticles = await articlesResponse.json();
          
          const formattedArticles = updatedArticles.map((article: any, index: number) => ({
            id: article.id || index + 1,
            title: article.title || '제목 없음',
            link: article.link || '#',
            published: article.published || new Date().toISOString(),
            source: article.source || '알 수 없음',
            summary: article.summary || '',
            keywords: Array.isArray(article.keywords) ? article.keywords :
                      typeof article.keywords === 'string' ? 
                      (article.keywords.startsWith('[') ? JSON.parse(article.keywords) : article.keywords.split(',').map(k => k.trim())) : 
                      [],
            is_favorite: article.is_favorite || false
          }));
          
          setArticles(formattedArticles);
          console.log(`✅ 요약이 개선된 ${formattedArticles.length}개 기사로 업데이트됨`);
        }
        
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'API 요청 실패');
      }
      
    } catch (error) {
      console.error('❌ 요약 생성 실패:', error);
      
      let errorMessage = '요약 자동 생성 중 오류가 발생했습니다.';
      if (error instanceof Error) {
        errorMessage += `\n오류 내용: ${error.message}`;
      }
      
      alert(`❌ ${errorMessage}`);
      
    } finally {
      setCollecting(false);
      console.log('📝 요약 생성 프로세스 완료');
    }
  };

  // 탭 변경
  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };


  // 키보드 단축키 설정
  useKeyboardShortcuts({
    onRefresh: collectNews,
    onToggleTheme: toggleTheme,
    onSearch: () => searchInputRef.current?.focus(),
    onNextTab: () => setTabValue(prev => (prev + 1) % 6),
    onPrevTab: () => setTabValue(prev => (prev - 1 + 6) % 6),
  });

  // 페이지네이션 계산
  const totalPages = Math.ceil(filteredArticles.length / itemsPerPage);
  const currentArticles = filteredArticles.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  // 소스 목록 (전체 articles에서 추출 - 필터링과 무관)
  const sources = [...new Set(articles.map(a => a.source))].sort();
  
  // 통계 (전체 데이터 기준)
  const stats = {
    totalArticles: articles.length,
    totalSources: sources.length,
    totalFavorites: articles.filter(a => a.is_favorite).length,
    recentArticles: articles.filter(a => {
      const weekAgo = new Date();
      weekAgo.setDate(weekAgo.getDate() - 7);
      return new Date(a.published) >= weekAgo;
    }).length,
    filteredArticles: filteredArticles.length
  };

  return (
    <ThemeContext.Provider value={{ isDarkMode, toggleTheme, theme, colors }}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
      
      {/* 상단 앱바 */}
      <AppBar position="fixed" sx={{ zIndex: theme => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <Typography variant="h5" component="div" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
            🗞️ 뉴스있슈~(News IT's Issue)
          </Typography>
          
          <Stack direction="row" spacing={1} sx={{ display: { xs: 'none', sm: 'flex' } }}>
            <Tooltip title={isDarkMode ? '라이트 모드' : '다크 모드'}>
              <IconButton color="inherit" onClick={toggleTheme}>
                {isDarkMode ? <LightMode /> : <DarkMode />}
              </IconButton>
            </Tooltip>
            
            <Tooltip title="새로고침">
              <IconButton 
                color="inherit" 
                onClick={collectNews}
                disabled={collecting}
              >
                <Refresh />
              </IconButton>
            </Tooltip>
            
            <Tooltip title={isDesktop ? "사이드바 토글" : "필터 메뉴"}>
              <IconButton color="inherit" onClick={() => setDrawerOpen(!drawerOpen)}>
                <FilterList />
              </IconButton>
            </Tooltip>
          </Stack>
          
          {/* 모바일용 축약 버튼 */}
          <Stack direction="row" spacing={1} sx={{ display: { xs: 'flex', sm: 'none' } }}>
            <Tooltip title={isDarkMode ? '라이트 모드' : '다크 모드'}>
              <IconButton color="inherit" onClick={toggleTheme}>
                {isDarkMode ? <LightMode /> : <DarkMode />}
              </IconButton>
            </Tooltip>
            
            <Tooltip title="새로고침">
              <IconButton 
                color="inherit" 
                onClick={collectNews}
                disabled={collecting}
              >
                <Refresh />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="필터 메뉴">
              <IconButton color="inherit" onClick={() => setDrawerOpen(!drawerOpen)}>
                <FilterList />
              </IconButton>
            </Tooltip>
          </Stack>
        </Toolbar>
      </AppBar>
      
      {/* 사이드바 (필터) */}
      <Drawer
        variant={isDesktop ? "persistent" : "temporary"}
        open={drawerOpen}
        onClose={() => !isDesktop && setDrawerOpen(false)}
        sx={{
          width: 300,
          flexShrink: 0,
          '& .MuiDrawer-paper': { 
            width: 300, 
            boxSizing: 'border-box', 
            pt: 8,
            ...(isDesktop && {
              position: 'fixed',
              height: '100vh',
            })
          },
        }}
      >
        <Box sx={{ p: 2 }}>
          {showShortcutsHelp && <KeyboardShortcutsHelp />}
          
          <Typography variant="h6" gutterBottom>🔧 필터링</Typography>

          {/* 대분류/소분류 필터 */}
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
              대분류 필터
            </Typography>
            
            {/* 대분류 선택 */}
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>대분류</InputLabel>
              <Select
                value={selectedMajorCategory || ''}
                onChange={(e) => {
                  const value = e.target.value as MajorCategory;
                  setSelectedMajorCategory(value || null);
                  setSelectedMinorCategory(null); // 대분류 변경시 소분류 초기화
                }}
                label="대분류"
              >
                <MenuItem value="">전체</MenuItem>
                {getMajorCategories().map((majorCat) => (
                  <MenuItem key={majorCat} value={majorCat}>
                    {majorCat}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* 소분류 선택 */}
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>소분류</InputLabel>
              <Select
                value={selectedMinorCategory || ''}
                onChange={(e) => {
                  setSelectedMinorCategory(e.target.value || null);
                }}
                label="소분류"
              >
                <MenuItem value="">전체</MenuItem>
                {/* 대분류가 선택된 경우 해당 소분류만, 아니면 모든 소분류 */}
                {(selectedMajorCategory 
                  ? getMinorCategories(selectedMajorCategory)
                  : Object.keys(getAllMinorCategories())
                ).map((minorCat) => (
                  <MenuItem key={minorCat} value={minorCat}>
                    {minorCat}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* 선택된 카테고리 표시 */}
            {(selectedMajorCategory || selectedMinorCategory) && (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                {selectedMajorCategory && (
                  <Chip
                    label={`대분류: ${selectedMajorCategory}`}
                    onDelete={() => {
                      setSelectedMajorCategory(null);
                      setSelectedMinorCategory(null);
                    }}
                    color="primary"
                    size="small"
                  />
                )}
                {selectedMinorCategory && (
                  <Chip
                    label={`소분류: ${selectedMinorCategory}`}
                    onDelete={() => setSelectedMinorCategory(null)}
                    color="secondary"
                    size="small"
                  />
                )}
              </Box>
            )}
          </Box>
          
          <Divider sx={{ my: 2 }} />
          
          {/* 뉴스 소스 */}
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>뉴스 소스</InputLabel>
            <Select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              label="뉴스 소스"
            >
              <MenuItem value="all">전체</MenuItem>
              {sources.map(source => (
                <MenuItem key={source} value={source}>{source}</MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* 키워드 검색 */}
          <TextField
            fullWidth
            inputRef={searchInputRef}
            label="키워드 검색"
            placeholder="예: AI, 반도체, 5G (Ctrl+K)"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            sx={{ mb: 2 }}
            InputProps={{ 
              startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />
            }}
          />

          {/* 기간 필터 */}
          <TextField
            fullWidth
            type="date"
            label="시작일"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            sx={{ mb: 2 }}
            InputLabelProps={{ shrink: true }}
          />
          
          <TextField
            fullWidth
            type="date"
            label="종료일"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            sx={{ mb: 2 }}
            InputLabelProps={{ shrink: true }}
          />

          {/* 즐겨찾기만 보기 */}
          <FormControlLabel
            control={
              <Switch
                checked={favoritesOnly}
                onChange={(e) => setFavoritesOnly(e.target.checked)}
              />
            }
            label="즐겨찾기만 보기"
            sx={{ mb: 2 }}
          />

          <Divider sx={{ my: 2 }} />
          
          {/* 데이터 관리 */}
          <Typography variant="h6" gutterBottom>📊 데이터 관리</Typography>
          
          <Button
            variant="contained"
            fullWidth
            startIcon={collecting ? <CircularProgress size={20} /> : <Refresh />}
            onClick={collectNews}
            disabled={collecting}
            sx={{ mb: 2 }}
          >
            {collecting ? '수집 중...' : '🔄 뉴스 수집'}
          </Button>

          {/* 컬렉션 관리 버튼 추가 */}
          <Button
            variant="outlined"
            fullWidth
            onClick={() => handleCreateCollection()}
            sx={{ mb: 2 }}
          >
            📁 새 컬렉션 만들기
          </Button>

          <Button
            variant="outlined"
            fullWidth
            onClick={handleEnhanceSummaries}
            sx={{ mb: 2 }}
            disabled={collecting}
          >
            🤖 요약 자동 생성
          </Button>

          {/* 통계 */}
          <Paper sx={{ 
            p: 2, 
            bgcolor: theme => theme.palette.mode === 'dark' ? 'grey.800' : 'grey.50',
            border: theme => theme.palette.mode === 'dark' ? '1px solid rgba(255, 255, 255, 0.12)' : 'none',
            mb: 2
          }}>
            <Typography variant="body2" sx={{ 
              color: theme => theme.palette.mode === 'dark' ? 'grey.300' : 'text.primary'
            }}>
              📊 총 {stats.totalArticles}건의 뉴스<br/>
              🔍 필터링된 {stats.filteredArticles}건<br/>
              📰 {stats.totalSources}개 소스<br/>
              ⭐ {stats.totalFavorites}개 즐겨찾기<br/>
              📅 최근 7일: {stats.recentArticles}건
            </Typography>
          </Paper>

          {/* 컬렉션 목록 */}
          {collections.length > 0 && (
            <>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>📁 컬렉션</Typography>
              <Stack spacing={1}>
                {collections.map((collection, index) => (
                  <Chip
                    key={index}
                    label={`${collection.name} (${collection.count})`}
                    variant="outlined"
                    size="small"
                  />
                ))}
              </Stack>
            </>
          )}
        </Box>
      </Drawer>

      {/* 메인 컨텐츠 */}
      <Box sx={{ 
        flexGrow: 1, 
        p: { xs: 2, md: 3 }, 
        pt: { xs: 10, md: 12 },
        ml: (isDesktop && drawerOpen) ? '300px' : 0,
        transition: 'margin-left 0.3s',
        minHeight: '100vh'
      }}>
        <Typography variant="body1" sx={{ mb: 2, color: 'text.secondary' }}>
          **IT/공학 뉴스 수집, 분석, 시각화 대시보드**
        </Typography>

        {/* 탭 */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
          <Tabs 
            value={tabValue} 
            onChange={handleTabChange}
            variant={isDesktop ? "standard" : "scrollable"}
            scrollButtons={isDesktop ? false : "auto"}
            sx={{
              '& .MuiTab-root': {
                minWidth: isDesktop ? 120 : 80,
                fontSize: { xs: '0.8rem', md: '0.875rem' }
              }
            }}
          >
            <Tab icon={<ArticleIcon />} label={isDesktop ? "📰 뉴스 목록" : "뉴스"} />
            <Tab icon={<TrendingUp />} label={isDesktop ? "📈 인사이트" : "인사이트"} />
            <Tab icon={<Analytics />} label={isDesktop ? "📊 키워드 분석" : "분석"} />
            <Tab icon={<Cloud />} label={isDesktop ? "☁️ 워드클라우드" : "워드클라우드"} />
            <Tab icon={<Favorite />} label={isDesktop ? "⭐ 즐겨찾기" : "즐겨찾기"} />
            <Tab icon={<DarkMode />} label={isDesktop ? "🎨 테마/컬러" : "테마"} />
          </Tabs>
        </Box>

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        )}

        {/* 뉴스 목록 탭 */}
        <TabPanel value={tabValue} index={0}>
          <Typography variant="h5" gutterBottom>📰 뉴스 목록</Typography>
          <Typography variant="body1" sx={{ mb: 2, fontWeight: 'bold' }}>
            **총 {filteredArticles.length}건의 뉴스**
          </Typography>

          {filteredArticles.length === 0 ? (
            <Alert severity="info">
              {articles.length === 0 ? 
                '데이터가 없습니다. 사이드바에서 "뉴스 수집" 버튼을 클릭하여 데이터를 수집하세요.' :
                '필터 조건에 맞는 뉴스가 없습니다.'
              }
            </Alert>
          ) : (
            <>
              {currentArticles.map(article => (
                <ArticleCard
                  key={article.id}
                  article={article}
                  onToggleFavorite={handleToggleFavorite}
                  onExtractKeywords={handleExtractKeywords}
                  onTranslate={handleTranslate}
                />
              ))}
              
              {totalPages > 1 && (
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
                  <Pagination
                    count={totalPages}
                    page={currentPage}
                    onChange={(_, page) => setCurrentPage(page)}
                    color="primary"
                  />
                </Box>
              )}
            </>
          )}
        </TabPanel>

        {/* 인사이트 탭 */}
        <TabPanel value={tabValue} index={1}>
          <Typography variant="h5" gutterBottom>📈 인사이트</Typography>
          <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
            전체 {articles.length}개 기사 기준 분석 (필터링과 독립적)
          </Typography>
          <InsightsCharts />
        </TabPanel>

        {/* 키워드 분석 탭 */}
        <TabPanel value={tabValue} index={2}>
          <Typography variant="h5" gutterBottom>📊 키워드 네트워크 분석</Typography>
          <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
            현재 필터링된 {filteredArticles.length}개 기사 기준 키워드 분석
          </Typography>
          
          {keywordStats.length === 0 ? (
            <Alert severity="info">분석할 데이터가 없습니다.</Alert>
          ) : (
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <Typography variant="h6" gutterBottom>🔥 인기 키워드 TOP 20</Typography>
                <Paper sx={{ p: 2, maxHeight: 400, overflow: 'auto' }}>
                  <List dense>
                    {keywordStats.slice(0, 20).map((stat, index) => (
                      <ListItem key={stat.keyword}>
                        <ListItemText
                          primary={`${index + 1}. ${stat.keyword}`}
                          secondary={`${stat.count}회`}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Paper>
              </Grid>

              <Grid item xs={12} md={8}>
                <Typography variant="h6" gutterBottom>🕸️ 키워드 관계 네트워크</Typography>
                <Paper sx={{ p: 2, height: 500 }}>
                  <KeywordNetworkContainer articles={filteredArticles} />
                </Paper>
              </Grid>
            </Grid>
          )}
        </TabPanel>

        {/* 워드클라우드 탭 */}
        <TabPanel value={tabValue} index={3}>
          <Typography variant="h5" gutterBottom>☁️ 워드클라우드</Typography>
          
          {keywordStats.length === 0 ? (
            <Alert severity="info">워드클라우드를 생성할 데이터가 없습니다.</Alert>
          ) : (
            <Paper sx={{ p: 2, height: 600 }}>
              <KeywordCloud data={keywordStats} onError={(error) => console.error('워드클라우드 오류:', error)} />
            </Paper>
          )}
        </TabPanel>

        {/* 즐겨찾기 탭 */}
        <TabPanel value={tabValue} index={4}>
          <Typography variant="h5" gutterBottom>⭐ 즐겨찾기</Typography>
          
          {(() => {
            const favorites = articles.filter(a => a.is_favorite);
            return favorites.length === 0 ? (
              <Alert severity="info">즐겨찾기한 뉴스가 없습니다.</Alert>
            ) : (
              <>
                <Typography variant="body1" sx={{ mb: 2, fontWeight: 'bold' }}>
                  **총 {favorites.length}건의 즐겨찾기**
                </Typography>
                {favorites.map(article => (
                  <ArticleCard
                    key={article.id}
                    article={article}
                    onToggleFavorite={handleToggleFavorite}
                    onExtractKeywords={handleExtractKeywords}
                    onTranslate={handleTranslate}
                  />
                ))}
              </>
            );
          })()}
        </TabPanel>

        {/* 테마/컬러 팔레트 탭 */}
        <TabPanel value={tabValue} index={5}>
          <Typography variant="h5" gutterBottom>🎨 테마 & 컬러 팔레트</Typography>
          <ColorPalette />
        </TabPanel>
      </Box>
      </ThemeProvider>
    </ThemeContext.Provider>
  );
}
