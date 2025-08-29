import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  CircularProgress, 
  Alert,
  Slider,
  FormControl,
  InputLabel,
  MenuItem,
  Select
} from '@mui/material';
import { newsApi } from '../api/newsApi';

interface KeywordCloudProps {
  onError?: (error: string) => void;
}

export const KeywordCloud: React.FC<KeywordCloudProps> = ({ onError }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [wordcloudImage, setWordcloudImage] = useState<string | null>(null);
  const [topKeywords, setTopKeywords] = useState<string[]>([]);
  const [keywordCount, setKeywordCount] = useState(0);
  
  // 설정 상태
  const [settings, setSettings] = useState({
    limit: 50,
    width: 800,
    height: 400
  });

  const generateWordcloud = async () => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('🎨 파이썬 워드클라우드 생성 중...');
      
      const response = await newsApi.getWordcloud({
        limit: settings.limit,
        width: settings.width,
        height: settings.height
      });
      
      setWordcloudImage(response.wordcloud_image);
      setTopKeywords(response.top_keywords || []);
      setKeywordCount(response.keyword_count || 0);
      
      console.log(`✅ 워드클라우드 생성 완료: ${response.keyword_count}개 키워드`);
      
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || '워드클라우드 생성 실패';
      setError(errorMsg);
      onError?.(errorMsg);
      console.error('❌ 워드클라우드 생성 실패:', err);
    } finally {
      setLoading(false);
    }
  };

  // 컴포넌트 마운트시 자동 생성
  useEffect(() => {
    generateWordcloud();
  }, []);

  // 설정 변경시 재생성
  useEffect(() => {
    const debounce = setTimeout(() => {
      generateWordcloud();
    }, 1000);
    
    return () => clearTimeout(debounce);
  }, [settings]);

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        AI 생성 워드클라우드 ({keywordCount}개 키워드)
      </Typography>
      
      {/* 설정 컨트롤 */}
      <Box sx={{ mb: 2, display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>키워드 수</InputLabel>
          <Select
            value={settings.limit}
            label="키워드 수"
            onChange={(e) => setSettings(prev => ({ ...prev, limit: Number(e.target.value) }))}
          >
            <MenuItem value={30}>30개</MenuItem>
            <MenuItem value={50}>50개</MenuItem>
            <MenuItem value={100}>100개</MenuItem>
          </Select>
        </FormControl>
        
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>크기</InputLabel>
          <Select
            value={`${settings.width}x${settings.height}`}
            label="크기"
            onChange={(e) => {
              const [width, height] = e.target.value.split('x').map(Number);
              setSettings(prev => ({ ...prev, width, height }));
            }}
          >
            <MenuItem value="600x300">Small</MenuItem>
            <MenuItem value="800x400">Medium</MenuItem>
            <MenuItem value="1000x500">Large</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* 로딩 상태 */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
          <Typography sx={{ ml: 2 }}>파이썬에서 워드클라우드 생성 중...</Typography>
        </Box>
      )}

      {/* 에러 상태 */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          워드클라우드 생성 실패: {error}
        </Alert>
      )}

      {/* 워드클라우드 이미지 */}
      {wordcloudImage && !loading && (
        <Box sx={{ textAlign: 'center', mb: 2 }}>
          <img 
            src={wordcloudImage} 
            alt="AI Generated Wordcloud"
            style={{ 
              maxWidth: '100%', 
              height: 'auto',
              border: '1px solid #ddd',
              borderRadius: '8px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
            }}
          />
        </Box>
      )}

      {/* 상위 키워드 표시 */}
      {topKeywords.length > 0 && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            주요 키워드 Top 20:
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {topKeywords.slice(0, 20).map((keyword, index) => (
              <Typography
                key={index}
                variant="caption"
                sx={{
                  px: 1,
                  py: 0.5,
                  bgcolor: 'primary.main',
                  color: 'white',
                  borderRadius: 1,
                  fontSize: '0.75rem'
                }}
              >
                {keyword}
              </Typography>
            ))}
          </Box>
        </Box>
      )}
    </Paper>
  );
};