import { Menu as RaMenu, usePermissions } from 'react-admin';
import DashboardIcon from '@mui/icons-material/Dashboard';
import SchoolIcon from '@mui/icons-material/School';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import QuizIcon from '@mui/icons-material/Quiz';
import { UserRole } from '../types';

/**
 * Боковое меню приложения с условным рендерингом на основе роли пользователя.
 *
 * Пункты меню для SUPER_ADMIN:
 * - Главная (Dashboard)
 * - Школы (Schools CRUD)
 * - Учебники (Textbooks) - CRUD для глобальных учебников (Итерация 5B)
 * - Тесты (Tests) - placeholder, disabled до Итерации 5C
 */
export const Menu = () => {
  const { permissions } = usePermissions();
  const isSuperAdmin = permissions === UserRole.SUPER_ADMIN;

  return (
    <RaMenu>
      <RaMenu.Item
        to="/"
        primaryText="Главная"
        leftIcon={<DashboardIcon />}
      />
      <RaMenu.Item
        to="/schools"
        primaryText="Школы"
        leftIcon={<SchoolIcon />}
      />

      {/* Показываем глобальные учебники и тесты только для SUPER_ADMIN */}
      {isSuperAdmin && (
        <>
          <RaMenu.Item
            to="/textbooks"
            primaryText="Учебники"
            leftIcon={<MenuBookIcon />}
          />
          <RaMenu.Item
            to="/tests"
            primaryText="Тесты"
            leftIcon={<QuizIcon />}
            disabled
          />
        </>
      )}
    </RaMenu>
  );
};
