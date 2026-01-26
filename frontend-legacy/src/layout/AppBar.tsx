import { AppBar as RaAppBar, Logout, UserMenu, useGetIdentity, ToggleThemeButton } from 'react-admin';
import { Box, Chip, Typography } from '@mui/material';
import PersonIcon from '@mui/icons-material/Person';

/**
 * Кастомный AppBar с информацией о текущем пользователе.
 *
 * Отображает:
 * - Название приложения
 * - Имя пользователя
 * - Роль пользователя (badge)
 * - Кнопку Logout
 */
export const AppBar = () => {
  const { data: identity, isLoading } = useGetIdentity();

  if (isLoading) {
    return <RaAppBar />;
  }

  return (
    <RaAppBar
      userMenu={
        <UserMenu>
          <Logout />
        </UserMenu>
      }
    >
      <Typography
        flex="1"
        variant="h6"
        id="react-admin-title"
      />
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 2,
          mr: 2,
        }}
      >
        {identity && (
          <>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <PersonIcon fontSize="small" />
              <Typography variant="body2">
                {identity.first_name} {identity.last_name}
              </Typography>
            </Box>
            <Chip
              label={getRoleLabel(identity.role)}
              size="small"
              color={identity.role === 'SUPER_ADMIN' ? 'secondary' : 'primary'}
              variant="outlined"
            />
          </>
        )}
        <ToggleThemeButton />
      </Box>
    </RaAppBar>
  );
};

/**
 * Возвращает читаемое название роли на русском языке
 */
function getRoleLabel(role: string): string {
  const roleLabels: Record<string, string> = {
    SUPER_ADMIN: 'Суперадмин',
    ADMIN: 'Администратор',
    TEACHER: 'Учитель',
    STUDENT: 'Ученик',
    PARENT: 'Родитель',
  };
  return roleLabels[role] || role;
}
