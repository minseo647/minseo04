import React, { useState, useEffect } from 'react';
import { Box, Paper, Typography, CircularProgress, Alert } from '@mui/material';

interface KeywordCloudProps {
  data: { keyword: string; count: number }[];
  onError?: (error: string) => void;
}

export const KeywordCloud: React.FC<KeywordCloudProps> = ({ data, onError }) => {
  const [imageUrl, setImageUrl] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    const generateWordcloud = async () => {
      try {
        setLoading(true);
        setError('');
        
        const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/wordcloud?width=800&height=400&background_color=white&max_words=100`);
        const result = await response.json();
        
        if (result.success) {
          setImageUrl(`data:image/png;base64,${result.image_base64}`);
        } else {
          const errorMsg = result.error || '워드클라우드 생성 실패';
          setError(errorMsg);
          onError?.(errorMsg);
        }
      } catch (err) {
        const errorMsg = '워드클라우드 API 연결 실패';
        setError(errorMsg);
        onError?.(errorMsg);
      } finally {
        setLoading(false);
      }
    };

    generateWordcloud();
  }, [data, onError]);

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
    <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: 'white' }}>
      <Typography variant="h6" gutterBottom>
        🐍 Python 워드클라우드 (wordcloud 라이브러리)
      </Typography>
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
          <img 
            src={imageUrl} 
            alt="Keyword WordCloud" 
            style={{ 
              maxWidth: '100%', 
              maxHeight: '400px',
              objectFit: 'contain'
            }}
          />
        ) : (
          <Typography color="text.secondary">
            워드클라우드를 불러올 수 없습니다.
          </Typography>
        )}
      </Box>
      <Typography variant="caption" sx={{ mt: 1, display: 'block', color: 'text.secondary' }}>
        총 {data.length}개 키워드 • Python wordcloud 라이브러리로 생성
      </Typography>
    </Paper>
  );
};