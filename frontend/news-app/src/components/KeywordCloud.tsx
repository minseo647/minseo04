import React, { useState, useEffect } from 'react';
import { 
  Box, Paper, Typography, CircularProgress, Alert, 
  Slider, FormControlLabel, Switch, Select, MenuItem, FormControl, InputLabel,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Accordion, AccordionSummary, AccordionDetails, Chip
} from '@mui/material';
import { ExpandMore } from '@mui/icons-material';

interface KeywordCloudProps {
  data: { keyword: string; count: number }[];
  onError?: (error: string) => void;
}

interface WordCloudResult {
  success: boolean;
  image_base64?: string;
  total_keywords?: number;
  used_keywords?: number;
  keyword_table?: { keyword: string; frequency: number }[];
  settings?: {
    max_words: number;
    colormap: string;
    auto_korean_font: boolean;
    font_detected: boolean;
    font_path: string | null;
    filter_unrenderables: boolean;
  };
  error?: string; // 에러 케이스를 위한 속성 추가
}

export const KeywordCloud: React.FC<KeywordCloudProps> = ({ data, onError }) => {
  const [imageUrl, setImageUrl] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [wordCloudData, setWordCloudData] = useState<WordCloudResult | null>(null);
  
  // Streamlit-style controls
  const [maxWords, setMaxWords] = useState(100);
  const [autoKoreanFont, setAutoKoreanFont] = useState(true);
  const [filterUnrenderables, setFilterUnrenderables] = useState(true);
  const [colormap, setColormap] = useState('viridis');

  useEffect(() => {
    const generateWordcloud = async () => {
      try {
        setLoading(true);
        setError('');
        
        // 백엔드 API 시도
        try {
          const params = new URLSearchParams({
            width: '800',
            height: '400',
            background_color: 'white',
            max_words: maxWords.toString(),
            colormap: colormap,
            auto_korean_font: autoKoreanFont.toString(),
            filter_unrenderables: filterUnrenderables.toString()
          });
          
          const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/wordcloud?${params}`);
          
          if (response.ok) {
            const result: WordCloudResult = await response.json();
            
            if (result.success) {
              setImageUrl(`data:image/png;base64,${result.image_base64}`);
              setWordCloudData(result);
              return;
            }
          }
        } catch (backendErr) {
          console.warn('Backend wordcloud failed, falling back to client-side:', backendErr);
        }
        
        // 백엔드 실패시 클라이언트 사이드 워드클라우드 생성
        const clientSideResult = generateClientSideWordcloud(data, maxWords);
        setWordCloudData(clientSideResult);
        setImageUrl(''); // 클라이언트 사이드는 이미지 대신 HTML 렌더링
        
      } catch (err) {
        const errorMsg = '워드클라우드 생성 실패';
        setError(errorMsg);
        onError?.(errorMsg);
      } finally {
        setLoading(false);
      }
    };

    generateWordcloud();
  }, [data, onError, maxWords, autoKoreanFont, filterUnrenderables, colormap]);

  // 클라이언트 사이드 워드클라우드 생성
  const generateClientSideWordcloud = (keywordData: { keyword: string; count: number }[], maxWords: number): WordCloudResult => {
    const sortedData = keywordData.slice(0, maxWords);
    const maxCount = Math.max(...sortedData.map(item => item.count));
    
    return {
      success: true,
      total_keywords: keywordData.length,
      used_keywords: sortedData.length,
      keyword_table: sortedData.map(item => ({ keyword: item.keyword, frequency: item.count })),
      settings: {
        max_words: maxWords,
        colormap: colormap,
        auto_korean_font: autoKoreanFont,
        font_detected: true,
        font_path: null,
        filter_unrenderables: filterUnrenderables
      }
    };
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Python 워드클라우드 생성 중...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        {error}
        <br />
        <Typography variant="body2" sx={{ mt: 1 }}>
          백엔드에서 Python wordcloud 라이브러리를 사용하여 생성합니다.
        </Typography>
      </Alert>
    );
  }

  return (
    <Box>
      {/* Streamlit-style Controls */}
      <Paper sx={{ p: 3, mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          🐍 Python 워드클라우드 설정
        </Typography>
        
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3, mb: 3 }}>
          {/* Max Words Slider */}
          <Box>
            <Typography gutterBottom>최대 키워드 수: {maxWords}</Typography>
            <Slider
              value={maxWords}
              onChange={(_, value) => setMaxWords(value as number)}
              min={20}
              max={200}
              step={10}
              marks
              valueLabelDisplay="auto"
            />
          </Box>
          
          {/* Color Scheme */}
          <FormControl>
            <InputLabel>색상 스키마</InputLabel>
            <Select
              value={colormap}
              label="색상 스키마"
              onChange={(e) => setColormap(e.target.value)}
            >
              <MenuItem value="viridis">Viridis</MenuItem>
              <MenuItem value="plasma">Plasma</MenuItem>
              <MenuItem value="rainbow">Rainbow</MenuItem>
              <MenuItem value="cool">Cool</MenuItem>
              <MenuItem value="hot">Hot</MenuItem>
            </Select>
          </FormControl>
        </Box>
        
        {/* Toggle Controls */}
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <FormControlLabel
            control={<Switch checked={autoKoreanFont} onChange={(e) => setAutoKoreanFont(e.target.checked)} />}
            label="한글 폰트 자동 적용"
          />
          <FormControlLabel
            control={<Switch checked={filterUnrenderables} onChange={(e) => setFilterUnrenderables(e.target.checked)} />}
            label="이모지/비지원 문자 제외"
          />
        </Box>
        
        {/* Settings Display */}
        {wordCloudData?.settings && (
          <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Chip size="small" label={`${wordCloudData.used_keywords}/${wordCloudData.total_keywords} 키워드`} />
            <Chip size="small" label={wordCloudData.settings.colormap} />
            {wordCloudData.settings.font_detected && (
              <Chip size="small" label="한글 폰트" color="primary" />
            )}
          </Box>
        )}
      </Paper>

      {/* WordCloud Visualization */}
      <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: 'white', mb: 2 }}>
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center',
          minHeight: 400,
          border: '1px solid #ddd',
          borderRadius: 2,
          backgroundColor: '#f9f9f9'
        }}>
          {imageUrl ? (
            // 백엔드에서 생성된 이미지
            <img 
              src={imageUrl} 
              alt="Keyword WordCloud" 
              style={{ 
                maxWidth: '100%', 
                maxHeight: '400px',
                objectFit: 'contain'
              }}
            />
          ) : wordCloudData?.keyword_table ? (
            // 클라이언트 사이드 워드클라우드
            <Box sx={{ 
              display: 'flex', 
              flexWrap: 'wrap', 
              justifyContent: 'center', 
              alignItems: 'center',
              gap: 2,
              p: 2,
              maxHeight: 400,
              overflow: 'hidden'
            }}>
              {wordCloudData.keyword_table.slice(0, maxWords).map((item, index) => {
                const maxFreq = wordCloudData.keyword_table![0].frequency;
                const normalizedSize = Math.max(0.8, (item.frequency / maxFreq) * 2.5);
                const hue = (index * 137.5) % 360; // 골든 앵글로 색상 분산
                const saturation = 60 + (item.frequency / maxFreq) * 40;
                const lightness = 40 + (index % 2) * 20;
                
                return (
                  <Box
                    key={item.keyword}
                    sx={{
                      fontSize: `${normalizedSize}rem`,
                      fontWeight: 'bold',
                      color: `hsl(${hue}, ${saturation}%, ${lightness}%)`,
                      textShadow: '1px 1px 2px rgba(0,0,0,0.1)',
                      cursor: 'default',
                      transition: 'all 0.2s ease',
                      '&:hover': {
                        transform: 'scale(1.1)',
                        filter: 'brightness(1.2)'
                      }
                    }}
                    title={`${item.keyword}: ${item.frequency}회`}
                  >
                    {item.keyword}
                  </Box>
                );
              })}
            </Box>
          ) : (
            <Typography color="text.secondary">
              워드클라우드 데이터가 없습니다.
            </Typography>
          )}
        </Box>
      </Paper>

      {/* Keyword Frequency Table */}
      {wordCloudData?.keyword_table && (
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Typography variant="h6">📊 키워드 빈도 상위표</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>순위</TableCell>
                    <TableCell>키워드</TableCell>
                    <TableCell align="right">빈도</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {wordCloudData.keyword_table.slice(0, 20).map((row, index) => (
                    <TableRow key={row.keyword}>
                      <TableCell>{index + 1}</TableCell>
                      <TableCell>{row.keyword}</TableCell>
                      <TableCell align="right">{row.frequency}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </AccordionDetails>
        </Accordion>
      )}
    </Box>
  );
};