import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  CircularProgress,
  Alert,
  Chip,
  Stack
} from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { TrendingUp, Category, Timeline, Analytics } from '@mui/icons-material';

interface TimeSeriesData {
  date: string;
  count: number;
}

interface CategoryData {
  [category: string]: number;
}

interface InsightsData {
  time_series: TimeSeriesData[];
  category_counts: CategoryData;
  total_articles: number;
  period: string;
  date_range?: {
    start: string;
    end: string;
  };
}

interface Article {
  id: number;
  title: string;
  link: string;
  published: string;
  source: string;
  summary?: string;
  keywords?: string[] | string;
  is_favorite?: boolean;
}

interface InsightsChartsProps {
  articles: Article[];
}

export const InsightsCharts: React.FC<InsightsChartsProps> = ({ articles }) => {
  const [data, setData] = useState<InsightsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<string>('daily');
  const [daysBack, setDaysBack] = useState<number>(30);

  // 차트 색상 팔레트
  const colors = [
    '#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1', 
    '#d084d0', '#ffb347', '#87ceeb', '#dda0dd', '#98fb98'
  ];

  const processInsights = () => {
    setLoading(true);
    setError(null);
    
    try {
      if (!articles || articles.length === 0) {
        setError('분석할 데이터가 없습니다.');
        setLoading(false);
        return;
      }

      // 날짜별 기사 수 계산
      const dateMap: Record<string, number> = {};
      const categoryMap: Record<string, number> = {};
      
      articles.forEach(article => {
        const date = new Date(article.published);
        const dateKey = period === 'monthly' 
          ? `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
          : period === 'weekly'
          ? `${date.getFullYear()}-W${Math.ceil(date.getDate() / 7)}`
          : `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
        
        dateMap[dateKey] = (dateMap[dateKey] || 0) + 1;
        
        // 소스별 카운트
        categoryMap[article.source] = (categoryMap[article.source] || 0) + 1;
      });

      // 최근 daysBack일 동안의 데이터만 필터링
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - daysBack);
      
      const filteredDateMap = Object.entries(dateMap).filter(([dateKey]) => {
        const [year, month, day] = dateKey.split('-').map(Number);
        const articleDate = new Date(year, month - 1, day || 1);
        return articleDate >= cutoffDate;
      });

      const time_series = filteredDateMap.map(([date, count]) => ({ date, count }));
      
      const insightsData: InsightsData = {
        time_series,
        category_counts: categoryMap,
        total_articles: articles.length,
        period,
        date_range: {
          start: cutoffDate.toISOString().split('T')[0],
          end: new Date().toISOString().split('T')[0]
        }
      };
      
      setData(insightsData);
    } catch (err) {
      setError('데이터 분석 중 오류가 발생했습니다.');
      console.error('Insights processing error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    processInsights();
  }, [articles, period, daysBack]);

  // 카테고리 데이터를 차트용으로 변환
  const categoryChartData = data ? Object.entries(data.category_counts).map(([category, count]) => ({
    category: category.length > 15 ? `${category.substring(0, 12)}...` : category,
    fullCategory: category,
    count: count
  })).sort((a, b) => b.count - a.count) : [];

  // 시계열 데이터 포맷팅
  const timeSeriesChartData = data ? data.time_series.map(item => ({
    ...item,
    formattedDate: period === 'monthly' ? 
      item.date : 
      new Date(item.date).toLocaleDateString('ko-KR', {
        month: 'short',
        day: 'numeric',
        ...(period === 'weekly' ? { weekday: 'short' } : {})
      })
  })) : [];

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={400}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (!data) {
    return <Alert severity="info">인사이트 데이터가 없습니다.</Alert>;
  }

  return (
    <Box>
      {/* 제어 패널 */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={4}>
          <FormControl fullWidth>
            <InputLabel>기간 단위</InputLabel>
            <Select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              label="기간 단위"
            >
              <MenuItem value="daily">일간</MenuItem>
              <MenuItem value="weekly">주간</MenuItem>
              <MenuItem value="monthly">월간</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} sm={4}>
          <FormControl fullWidth>
            <InputLabel>조회 기간</InputLabel>
            <Select
              value={daysBack}
              onChange={(e) => setDaysBack(Number(e.target.value))}
              label="조회 기간"
            >
              <MenuItem value={7}>최근 7일</MenuItem>
              <MenuItem value={30}>최근 30일</MenuItem>
              <MenuItem value={90}>최근 90일</MenuItem>
              <MenuItem value={180}>최근 6개월</MenuItem>
              <MenuItem value={365}>최근 1년</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.main', color: 'white' }}>
            <Typography variant="h4">{data.total_articles}</Typography>
            <Typography variant="body2">총 기사 수</Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* 요약 통계 */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} sm={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Analytics color="primary" sx={{ fontSize: 40, mb: 1 }} />
            <Typography variant="h6">{period === 'daily' ? '일평균' : period === 'weekly' ? '주평균' : '월평균'}</Typography>
            <Typography variant="h4" color="primary">
              {Math.round(data.total_articles / (timeSeriesChartData.length || 1))}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <TrendingUp color="success" sx={{ fontSize: 40, mb: 1 }} />
            <Typography variant="h6">최대 기사수</Typography>
            <Typography variant="h4" color="success.main">
              {Math.max(...timeSeriesChartData.map(d => d.count), 0)}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Category color="secondary" sx={{ fontSize: 40, mb: 1 }} />
            <Typography variant="h6">활성 카테고리</Typography>
            <Typography variant="h4" color="secondary.main">
              {Object.keys(data.category_counts).length}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Timeline color="warning" sx={{ fontSize: 40, mb: 1 }} />
            <Typography variant="h6">분석 기간</Typography>
            <Typography variant="h4" color="warning.main">
              {daysBack}일
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* 시계열 차트 */}
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TrendingUp />
              {period === 'daily' ? '일별' : period === 'weekly' ? '주별' : '월별'} 기사 수 추이
            </Typography>
            {timeSeriesChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={timeSeriesChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="formattedDate"
                    angle={period === 'daily' ? -45 : 0}
                    textAnchor={period === 'daily' ? 'end' : 'middle'}
                    height={period === 'daily' ? 80 : 60}
                  />
                  <YAxis />
                  <Tooltip 
                    labelFormatter={(value) => `${value}`}
                    formatter={(value: number) => [`${value}개`, '기사 수']}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="count" 
                    stroke="#8884d8" 
                    strokeWidth={3}
                    dot={{ fill: '#8884d8', strokeWidth: 2, r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                해당 기간에 데이터가 없습니다.
              </Typography>
            )}
          </Paper>
        </Grid>

        {/* 카테고리별 기사 수 */}
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Category />
              카테고리별 기사 수
            </Typography>
            {categoryChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={categoryChartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="category"
                    angle={-45}
                    textAnchor="end"
                    height={100}
                    interval={0}
                  />
                  <YAxis />
                  <Tooltip 
                    labelFormatter={(value, payload) => payload?.[0]?.payload?.fullCategory || value}
                    formatter={(value: number) => [`${value}개`, '기사 수']}
                  />
                  <Bar dataKey="count" fill="#82ca9d" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                카테고리 데이터가 없습니다.
              </Typography>
            )}
          </Paper>
        </Grid>

        {/* 카테고리 분포 파이 차트 */}
        <Grid item xs={12} lg={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              카테고리 분포
            </Typography>
            {categoryChartData.length > 0 ? (
              <Box>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={categoryChartData.slice(0, 8)} // 상위 8개만 표시
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={120}
                      paddingAngle={2}
                      dataKey="count"
                      label={({ category, percent }) => 
                        `${category} ${(percent * 100).toFixed(0)}%`
                      }
                    >
                      {categoryChartData.slice(0, 8).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: number) => [`${value}개`, '기사 수']} />
                  </PieChart>
                </ResponsiveContainer>
                
                {/* 범례 */}
                <Stack direction="row" flexWrap="wrap" gap={1} justifyContent="center">
                  {categoryChartData.slice(0, 8).map((item, index) => (
                    <Chip
                      key={item.category}
                      label={`${item.fullCategory} (${item.count})`}
                      size="small"
                      sx={{ 
                        bgcolor: colors[index % colors.length], 
                        color: 'white',
                        fontSize: '0.7rem'
                      }}
                    />
                  ))}
                </Stack>
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                분포 데이터가 없습니다.
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* 기간 정보 */}
      {data.date_range && (
        <Box sx={{ mt: 2, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            분석 기간: {data.date_range.start} ~ {data.date_range.end}
          </Typography>
        </Box>
      )}
    </Box>
  );
};