import { Card, CardContent, Typography, Box, Button } from '@mui/material';
import { useGetList } from 'react-admin';
import { Link } from 'react-router-dom';
import SchoolIcon from '@mui/icons-material/School';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import BlockIcon from '@mui/icons-material/Block';
import type { School } from '../types';

/**
 * Dashboard для SUPER_ADMIN.
 *
 * Отображает:
 * 1. Метрики (3 карточки):
 *    - Всего школ
 *    - Активные школы
 *    - Заблокированные школы
 * 2. Таблица последних созданных школ (5 записей)
 */
export const Dashboard = () => {
  const { data: schools, isLoading, error } = useGetList<School>('schools', {
    pagination: { page: 1, perPage: 100 },
    sort: { field: 'created_at', order: 'DESC' },
  });

  if (isLoading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Загрузка...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" color="error" gutterBottom>
          Ошибка загрузки данных
        </Typography>
      </Box>
    );
  }

  const totalSchools = schools?.length || 0;
  const activeSchools = schools?.filter((s) => s.is_active).length || 0;
  const blockedSchools = totalSchools - activeSchools;
  const recentSchools = schools?.slice(0, 5) || [];

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Главная
      </Typography>

      {/* Метрики */}
      <Box sx={{ display: 'flex', gap: 3, mb: 4, flexWrap: 'wrap' }}>
        <Box sx={{ flex: '1 1 300px', minWidth: '250px' }}>
          <MetricCard
            title="Всего школ"
            value={totalSchools}
            icon={<SchoolIcon sx={{ fontSize: 40 }} />}
            color="#1976d2"
          />
        </Box>
        <Box sx={{ flex: '1 1 300px', minWidth: '250px' }}>
          <MetricCard
            title="Активные"
            value={activeSchools}
            icon={<CheckCircleIcon sx={{ fontSize: 40 }} />}
            color="#4caf50"
          />
        </Box>
        <Box sx={{ flex: '1 1 300px', minWidth: '250px' }}>
          <MetricCard
            title="Заблокированные"
            value={blockedSchools}
            icon={<BlockIcon sx={{ fontSize: 40 }} />}
            color="#f44336"
          />
        </Box>
      </Box>

      {/* Последние школы */}
      <Card>
        <CardContent>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              mb: 2,
            }}
          >
            <Typography variant="h6">Последние созданные школы</Typography>
            <Button component={Link} to="/schools" variant="outlined" size="small">
              Все школы
            </Button>
          </Box>

          {recentSchools.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              Нет школ
            </Typography>
          ) : (
            <Box sx={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #e0e0e0' }}>
                    <th style={{ padding: '12px 8px', textAlign: 'left' }}>ID</th>
                    <th style={{ padding: '12px 8px', textAlign: 'left' }}>Название</th>
                    <th style={{ padding: '12px 8px', textAlign: 'left' }}>Код</th>
                    <th style={{ padding: '12px 8px', textAlign: 'left' }}>Email</th>
                    <th style={{ padding: '12px 8px', textAlign: 'left' }}>Статус</th>
                    <th style={{ padding: '12px 8px', textAlign: 'left' }}>Дата создания</th>
                  </tr>
                </thead>
                <tbody>
                  {recentSchools.map((school) => (
                    <tr
                      key={school.id}
                      style={{ borderBottom: '1px solid #f0f0f0' }}
                    >
                      <td style={{ padding: '12px 8px' }}>{school.id}</td>
                      <td style={{ padding: '12px 8px' }}>
                        <Typography variant="body2" fontWeight="bold">
                          {school.name}
                        </Typography>
                      </td>
                      <td style={{ padding: '12px 8px' }}>
                        <Typography variant="body2" color="text.secondary">
                          {school.code}
                        </Typography>
                      </td>
                      <td style={{ padding: '12px 8px' }}>
                        <Typography variant="body2" color="text.secondary">
                          {school.email || '—'}
                        </Typography>
                      </td>
                      <td style={{ padding: '12px 8px' }}>
                        <Box
                          sx={{
                            display: 'inline-block',
                            px: 1.5,
                            py: 0.5,
                            borderRadius: 1,
                            backgroundColor: school.is_active ? '#e8f5e9' : '#ffebee',
                            color: school.is_active ? '#2e7d32' : '#c62828',
                            fontSize: '0.875rem',
                          }}
                        >
                          {school.is_active ? 'Активна' : 'Заблокирована'}
                        </Box>
                      </td>
                      <td style={{ padding: '12px 8px' }}>
                        <Typography variant="body2" color="text.secondary">
                          {formatDate(school.created_at)}
                        </Typography>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

/**
 * Компонент карточки метрики
 */
interface MetricCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: string;
}

const MetricCard = ({ title, value, icon, color }: MetricCardProps) => {
  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography color="text.secondary" variant="body2" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h3" component="div">
              {value}
            </Typography>
          </Box>
          <Box sx={{ color }}>{icon}</Box>
        </Box>
      </CardContent>
    </Card>
  );
};

/**
 * Форматирует дату в читаемый формат
 */
function formatDate(dateString: string | undefined): string {
  if (!dateString) return '—';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateString;
  }
}
