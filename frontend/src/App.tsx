import { Admin, Resource, houseLightTheme, houseDarkTheme } from 'react-admin';
import { authProvider, dataProvider } from './providers';
import { Layout } from './layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { SchoolList, SchoolCreate, SchoolEdit, SchoolShow } from './pages/schools';
import { TextbookList, TextbookCreate, TextbookEdit, TextbookShow } from './pages/textbooks';
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
      theme={houseLightTheme}
      darkTheme={houseDarkTheme}
    >
      {/* Ресурсы для SUPER_ADMIN */}
      <Resource
        name="schools"
        list={SchoolList}
        create={SchoolCreate}
        edit={SchoolEdit}
        show={SchoolShow}
        icon={SchoolIcon}
        options={{ label: 'Школы' }}
      />

      {/* Глобальные учебники (CRUD для SUPER_ADMIN) */}
      <Resource
        name="textbooks"
        list={TextbookList}
        create={TextbookCreate}
        edit={TextbookEdit}
        show={TextbookShow}
        icon={MenuBookIcon}
        options={{ label: 'Учебники' }}
      />

      {/* Placeholder ресурс (будет реализован в следующих фазах) */}
      <Resource
        name="tests"
        icon={QuizIcon}
        options={{ label: 'Тесты' }}
      />
    </Admin>
  );
}

export default App;
