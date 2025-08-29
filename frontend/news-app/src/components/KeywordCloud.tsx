import React from 'react';
import { Box, Paper, Typography } from '@mui/material';

interface KeywordCloudProps {
  data: { keyword: string; count: number }[];
  onError?: (error: string) => void; // Keep onError for consistency
}

export const KeywordCloud: React.FC<KeywordCloudProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return <Typography>워드클라우드를 생성할 키워드가 없습니다.</Typography>;
  }

  const maxCount = Math.max(...data.map(d => d.count), 0);

  const getFontSize = (count: number) => {
    if (maxCount === 0) return '1rem';
    const size = 12 + (count / maxCount) * 32; // Base size 12px, max additional size 32px
    return `${size}px`;
  };

  const getFontWeight = (count: number) => {
    if (maxCount === 0) return 400;
    const weight = 400 + Math.round((count / maxCount) * 3) * 100; // 400, 500, 600, 700
    return weight;
  };

  return (
    <Paper sx={{ p: 3, textAlign: 'center' }}>
      <Typography variant="h6" gutterBottom>
        키워드 워드클라우드
      </Typography>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', alignItems: 'center', gap: 2, pt: 2 }}>
        {data.map(({ keyword, count }) => (
          <Typography
            key={keyword}
            style={{
              fontSize: getFontSize(count),
              fontWeight: getFontWeight(count),
              lineHeight: 1,
              padding: '4px 8px',
              borderRadius: '4px',
              // backgroundColor: '#f0f0f0' // Optional background color
            }}
          >
            {keyword}
          </Typography>
        ))}
      </Box>
    </Paper>
  );
};