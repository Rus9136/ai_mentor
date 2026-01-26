import { Menu as RaMenu, usePermissions } from 'react-admin';
import DashboardIcon from '@mui/icons-material/Dashboard';
import SchoolIcon from '@mui/icons-material/School';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import QuizIcon from '@mui/icons-material/Quiz';
import PeopleIcon from '@mui/icons-material/People';
import BadgeIcon from '@mui/icons-material/Badge';
import FamilyRestroomIcon from '@mui/icons-material/FamilyRestroom';
import ClassIcon from '@mui/icons-material/Class';
import SettingsIcon from '@mui/icons-material/Settings';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import TrackChangesIcon from '@mui/icons-material/TrackChanges';
import { UserRole } from '../types';

/**
 * Боковое меню приложения с условным рендерингом на основе роли пользователя.
 *
 * Пункты меню для SUPER_ADMIN:
 * - Главная (Dashboard)
 * - Школы (Schools CRUD)
 * - Учебники (Textbooks) - CRUD для глобальных учебников (Итерация 5B)
 * - Тесты (Tests) - CRUD для глобальных тестов (Итерация 5C)
 *
 * Пункты меню для школьного ADMIN:
 * - Главная (Dashboard)
 * - Ученики (Students CRUD) - Итерация 5D
 * - Учителя (Teachers CRUD) - Итерация 5D
 * - Родители (Parents CRUD) - Итерация 5D
 * - Классы (Classes CRUD) - Итерация 5D
 */
export const Menu = () => {
  const { permissions } = usePermissions();
  const isSuperAdmin = permissions === UserRole.SUPER_ADMIN;
  const isSchoolAdmin = permissions === UserRole.ADMIN;

  return (
    <RaMenu>
      <RaMenu.Item
        to="/"
        primaryText="Главная"
        leftIcon={<DashboardIcon />}
      />

      {/* Пункты меню для SUPER_ADMIN */}
      {isSuperAdmin && [
        <RaMenu.Item
          key="schools"
          to="/schools"
          primaryText="Школы"
          leftIcon={<SchoolIcon />}
        />,
        <RaMenu.Item
          key="textbooks"
          to="/textbooks"
          primaryText="Учебники"
          leftIcon={<MenuBookIcon />}
        />,
        <RaMenu.Item
          key="tests"
          to="/tests"
          primaryText="Тесты"
          leftIcon={<QuizIcon />}
        />,
        <RaMenu.Item
          key="goso-frameworks"
          to="/goso-frameworks"
          primaryText="ГОСО Стандарты"
          leftIcon={<AccountBalanceIcon />}
        />,
        <RaMenu.Item
          key="learning-outcomes"
          to="/learning-outcomes"
          primaryText="Цели обучения"
          leftIcon={<TrackChangesIcon />}
        />,
      ]}

      {/* Пункты меню для школьного ADMIN */}
      {isSchoolAdmin && [
        <RaMenu.Item
          key="students"
          to="/students"
          primaryText="Ученики"
          leftIcon={<PeopleIcon />}
        />,
        <RaMenu.Item
          key="teachers"
          to="/teachers"
          primaryText="Учителя"
          leftIcon={<BadgeIcon />}
        />,
        <RaMenu.Item
          key="parents"
          to="/parents"
          primaryText="Родители"
          leftIcon={<FamilyRestroomIcon />}
        />,
        <RaMenu.Item
          key="classes"
          to="/classes"
          primaryText="Классы"
          leftIcon={<ClassIcon />}
        />,
        <RaMenu.Item
          key="school-textbooks"
          to="/school-textbooks"
          primaryText="Учебники"
          leftIcon={<MenuBookIcon />}
        />,
        <RaMenu.Item
          key="school-tests"
          to="/school-tests"
          primaryText="Тесты"
          leftIcon={<QuizIcon />}
        />,
        <RaMenu.Item
          key="school-settings"
          to="/school-settings"
          primaryText="Настройки"
          leftIcon={<SettingsIcon />}
        />,
      ]}
    </RaMenu>
  );
};
