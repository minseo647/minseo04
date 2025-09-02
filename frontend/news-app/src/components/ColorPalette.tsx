import React from 'react';
import {
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  Chip,
  Stack,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';

interface ColorPaletteProps {
  onColorChange?: (colorKey: string, color: string) => void;
}

export const ColorPalette: React.FC<ColorPaletteProps> = ({ onColorChange }) => {
  const theme = useTheme();

  const ColorCard = ({ title, colors, description, colorKey }: {
    title: string;
    colors: { name: string; value: string; textColor?: string; colorKey?: string }[];
    description?: string;
    colorKey?: string;
  }) => (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>
        {description && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {description}
          </Typography>
        )}
        <Grid container spacing={1}>
          {colors.map((color) => (
            <Grid item xs={6} sm={4} md={3} key={color.name}>
              <Box
                sx={{
                  backgroundColor: color.value,
                  height: 80,
                  borderRadius: 2,
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                  alignItems: 'center',
                  border: '1px solid',
                  borderColor: 'divider',
                  position: 'relative',
                  cursor: color.colorKey && onColorChange ? 'pointer' : 'default',
                  transition: 'all 0.2s ease',
                  '&:hover': color.colorKey && onColorChange ? {
                    transform: 'scale(1.05)',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                    borderColor: 'primary.main'
                  } : {},
                }}
                onClick={() => {
                  if (color.colorKey && onColorChange) {
                    onColorChange(color.colorKey, color.value);
                  }
                }}
              >
                <Typography
                  variant="caption"
                  sx={{
                    color: color.textColor || (theme.palette.mode === 'dark' ? '#fff' : '#000'),
                    fontWeight: 600,
                    textAlign: 'center',
                  }}
                >
                  {color.name}
                </Typography>
                <Typography
                  variant="caption"
                  sx={{
                    color: color.textColor || (theme.palette.mode === 'dark' ? '#fff' : '#000'),
                    fontSize: '0.6rem',
                    opacity: 0.8,
                  }}
                >
                  {color.value}
                </Typography>
                {color.colorKey && onColorChange && (
                  <Typography
                    variant="caption"
                    sx={{
                      position: 'absolute',
                      top: 4,
                      right: 4,
                      backgroundColor: 'rgba(0,0,0,0.5)',
                      color: 'white',
                      padding: '1px 4px',
                      borderRadius: 1,
                      fontSize: '0.5rem'
                    }}
                  >
                    클릭
                  </Typography>
                )}
              </Box>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );

  const primaryColors = [
    { name: 'Current Primary', value: theme.palette.primary.main, textColor: '#fff' },
    { name: 'Primary Light', value: theme.palette.primary.light, textColor: '#fff' },
    { name: 'Primary Dark', value: theme.palette.primary.dark, textColor: '#fff' },
  ];

  const secondaryColors = [
    { name: 'Current Secondary', value: theme.palette.secondary.main, textColor: '#fff' },
    { name: 'Secondary Light', value: theme.palette.secondary.light, textColor: '#fff' },
    { name: 'Secondary Dark', value: theme.palette.secondary.dark, textColor: '#fff' },
  ];

  const backgroundColors = [
    { name: 'Default', value: theme.palette.background.default },
    { name: 'Paper', value: theme.palette.background.paper },
  ];

  const textColors = [
    { name: 'Primary Text', value: theme.palette.text.primary },
    { name: 'Secondary Text', value: theme.palette.text.secondary },
  ];

  // Custom colors from our enhanced theme
  const customColors = [
    { name: 'Current Accent', value: (theme.palette as any).accent?.main || '#059669', textColor: '#fff' },
    { name: 'Surface Primary', value: (theme.palette as any).surface?.primary || 'rgba(37, 99, 235, 0.08)' },
    { name: 'Surface Secondary', value: (theme.palette as any).surface?.secondary || 'rgba(220, 38, 38, 0.08)' },
    { name: 'Surface Accent', value: (theme.palette as any).surface?.accent || 'rgba(5, 150, 105, 0.08)' },
  ];

  // 클릭 가능한 색상 팔레트
  const primaryPalette = [
    { name: '파란색', value: '#2563eb', textColor: '#fff', colorKey: 'primaryMain' },
    { name: '보라색', value: '#7c3aed', textColor: '#fff', colorKey: 'primaryMain' },
    { name: '초록색', value: '#059669', textColor: '#fff', colorKey: 'primaryMain' },
    { name: '빨간색', value: '#dc2626', textColor: '#fff', colorKey: 'primaryMain' },
    { name: '주황색', value: '#ea580c', textColor: '#fff', colorKey: 'primaryMain' },
    { name: '분홍색', value: '#db2777', textColor: '#fff', colorKey: 'primaryMain' },
    { name: '청록색', value: '#0891b2', textColor: '#fff', colorKey: 'primaryMain' },
    { name: '회색', value: '#374151', textColor: '#fff', colorKey: 'primaryMain' },
  ];

  const secondaryPalette = [
    { name: '파란색', value: '#3b82f6', textColor: '#fff', colorKey: 'secondaryMain' },
    { name: '보라색', value: '#8b5cf6', textColor: '#fff', colorKey: 'secondaryMain' },
    { name: '초록색', value: '#10b981', textColor: '#fff', colorKey: 'secondaryMain' },
    { name: '빨간색', value: '#ef4444', textColor: '#fff', colorKey: 'secondaryMain' },
    { name: '주황색', value: '#f59e0b', textColor: '#fff', colorKey: 'secondaryMain' },
    { name: '분홍색', value: '#ec4899', textColor: '#fff', colorKey: 'secondaryMain' },
    { name: '청록색', value: '#06b6d4', textColor: '#fff', colorKey: 'secondaryMain' },
    { name: '회색', value: '#6b7280', textColor: '#fff', colorKey: 'secondaryMain' },
  ];

  const accentPalette = [
    { name: '에메랄드', value: '#059669', textColor: '#fff', colorKey: 'accentMain' },
    { name: '청록색', value: '#0891b2', textColor: '#fff', colorKey: 'accentMain' },
    { name: '라임', value: '#65a30d', textColor: '#fff', colorKey: 'accentMain' },
    { name: '자주색', value: '#9333ea', textColor: '#fff', colorKey: 'accentMain' },
    { name: '골드', value: '#d97706', textColor: '#fff', colorKey: 'accentMain' },
    { name: '로즈', value: '#e11d48', textColor: '#fff', colorKey: 'accentMain' },
    { name: '인디고', value: '#4338ca', textColor: '#fff', colorKey: 'accentMain' },
    { name: '슬레이트', value: '#475569', textColor: '#fff', colorKey: 'accentMain' },
  ];

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        🎨 컬러 팔레트
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        현재 적용된 {theme.palette.mode === 'dark' ? '다크' : '라이트'} 테마의 컬러 팔레트입니다.
      </Typography>

      <Stack spacing={1} sx={{ mb: 3 }}>
        <Chip 
          label={`현재 모드: ${theme.palette.mode === 'dark' ? '다크 모드' : '라이트 모드'}`}
          color="primary"
          variant="filled"
        />
        <Chip 
          label={`테마 업데이트: ${new Date().toLocaleString()}`}
          variant="outlined"
        />
      </Stack>

      <ColorCard
        title="🔥 Primary Colors"
        description="현재 설정된 주요 브랜드 색상입니다."
        colors={primaryColors}
      />

      <ColorCard
        title="🎯 Primary 색상 변경"
        description="클릭하여 Primary 색상을 변경하세요."
        colors={primaryPalette}
      />

      <ColorCard
        title="💖 Secondary Colors"
        description="현재 설정된 보조 색상입니다."
        colors={secondaryColors}
      />

      <ColorCard
        title="🌈 Secondary 색상 변경"
        description="클릭하여 Secondary 색상을 변경하세요."
        colors={secondaryPalette}
      />

      <ColorCard
        title="🌟 Custom Colors"
        description="현재 설정된 사용자 정의 색상입니다."
        colors={customColors}
      />

      <ColorCard
        title="✨ Accent 색상 변경"
        description="클릭하여 Accent 색상을 변경하세요."
        colors={accentPalette}
      />

      <ColorCard
        title="📄 Background Colors"
        description="배경색으로 전체적인 톤을 설정합니다."
        colors={backgroundColors}
      />

      <ColorCard
        title="📝 Text Colors"
        description="텍스트 색상으로 가독성을 보장합니다."
        colors={textColors}
      />

      {/* Theme Details */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            🔧 테마 세부 정보
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Typography variant="body2" color="text.secondary">
                <strong>폰트 패밀리:</strong> {theme.typography.fontFamily}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="body2" color="text.secondary">
                <strong>기본 반경:</strong> {theme.shape.borderRadius}px
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="body2" color="text.secondary">
                <strong>모드:</strong> {theme.palette.mode}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="body2" color="text.secondary">
                <strong>Spacing Unit:</strong> {theme.spacing(1)}px
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Paper>
  );
};