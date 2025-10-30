import { Admin, Resource, ListGuesser } from 'react-admin';
import { authProvider, dataProvider } from './providers';
import { Layout } from './layout/Layout';
import { Dashboard } from './pages/Dashboard';
import SchoolIcon from '@mui/icons-material/School';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import QuizIcon from '@mui/icons-material/Quiz';

function App() {
  return (
    <Admin
      authProvider={authProvider}
      dataProvider={dataProvider}
      layout={Layout}
      dashboard={Dashboard}
      requireAuth
      title="AI Mentor Admin"
    >
      {/* Ресурсы для SUPER_ADMIN */}
      <Resource
        name="schools"
        list={ListGuesser}
        icon={SchoolIcon}
        options={{ label: 'Школы' }}
      />

      {/* Placeholder ресурсы (будут реализованы в следующих фазах) */}
      <Resource
        name="textbooks"
        icon={MenuBookIcon}
        options={{ label: 'Учебники' }}
      />
      <Resource
        name="tests"
        icon={QuizIcon}
        options={{ label: 'Тесты' }}
      />
    </Admin>
  );
}

export default App;
