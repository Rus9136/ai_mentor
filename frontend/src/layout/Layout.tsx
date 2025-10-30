import { Layout as RaLayout } from 'react-admin';
import type { LayoutProps } from 'react-admin';
import { AppBar } from './AppBar';
import { Menu } from './Menu';

/**
 * Главный Layout приложения.
 *
 * Использует кастомные компоненты:
 * - AppBar - верхняя панель с информацией о пользователе
 * - Menu - боковое меню с навигацией
 *
 * React Admin автоматически добавляет Sidebar с Menu внутри.
 */
export const Layout = (props: LayoutProps) => {
  return <RaLayout {...props} appBar={AppBar} menu={Menu} />;
};
