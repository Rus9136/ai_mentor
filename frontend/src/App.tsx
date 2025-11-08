import { Admin, Resource, CustomRoutes, defaultLightTheme, defaultDarkTheme } from 'react-admin';
import { Route } from 'react-router-dom';
import { authProvider, dataProvider } from './providers';
import { Layout } from './layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { SchoolList, SchoolCreate, SchoolEdit, SchoolShow } from './pages/schools';
import { TextbookList, TextbookCreate, TextbookEdit, TextbookShow } from './pages/textbooks';
import { TestList, TestCreate, TestEdit, TestShow } from './pages/tests';
import { StudentList, StudentCreate, StudentEdit, StudentShow } from './pages/students';
import { TeacherList, TeacherCreate, TeacherEdit, TeacherShow } from './pages/teachers';
import { ParentList, ParentCreate, ParentShow } from './pages/parents';
import { ClassList, ClassCreate, ClassEdit, ClassShow } from './pages/classes';
import { SchoolTextbookList } from './pages/school-content/textbooks';
import { SchoolTestList } from './pages/school-content/tests';
import { SchoolSettings } from './pages/school-content/settings';
import SchoolIcon from '@mui/icons-material/School';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import QuizIcon from '@mui/icons-material/Quiz';
import PeopleIcon from '@mui/icons-material/People';
import BadgeIcon from '@mui/icons-material/Badge';
import FamilyRestroomIcon from '@mui/icons-material/FamilyRestroom';
import ClassIcon from '@mui/icons-material/Class';

function App() {
  return (
    <Admin
      authProvider={authProvider}
      dataProvider={dataProvider}
      layout={Layout}
      dashboard={Dashboard}
      requireAuth
      title="AI Mentor Admin"
      theme={defaultLightTheme}
      darkTheme={defaultDarkTheme}
      disableTelemetry
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

      {/* Глобальные тесты (CRUD для SUPER_ADMIN) */}
      <Resource
        name="tests"
        list={TestList}
        create={TestCreate}
        edit={TestEdit}
        show={TestShow}
        icon={QuizIcon}
        options={{ label: 'Тесты' }}
      />

      {/* Ресурсы для школьного ADMIN */}
      <Resource
        name="students"
        list={StudentList}
        create={StudentCreate}
        edit={StudentEdit}
        show={StudentShow}
        icon={PeopleIcon}
        options={{ label: 'Ученики' }}
      />

      <Resource
        name="teachers"
        list={TeacherList}
        create={TeacherCreate}
        edit={TeacherEdit}
        show={TeacherShow}
        icon={BadgeIcon}
        options={{ label: 'Учителя' }}
      />

      <Resource
        name="parents"
        list={ParentList}
        create={ParentCreate}
        show={ParentShow}
        icon={FamilyRestroomIcon}
        options={{ label: 'Родители' }}
      />

      <Resource
        name="classes"
        list={ClassList}
        create={ClassCreate}
        edit={ClassEdit}
        show={ClassShow}
        icon={ClassIcon}
        options={{ label: 'Классы' }}
      />

      {/* Школьные учебники (для школьного ADMIN) */}
      <Resource
        name="school-textbooks"
        list={SchoolTextbookList}
        create={TextbookCreate}
        edit={TextbookEdit}
        show={TextbookShow}
        icon={MenuBookIcon}
        options={{ label: 'Библиотека учебников' }}
      />

      {/* Школьные тесты (для школьного ADMIN) */}
      <Resource
        name="school-tests"
        list={SchoolTestList}
        create={TestCreate}
        edit={TestEdit}
        show={TestShow}
        icon={QuizIcon}
        options={{ label: 'Библиотека тестов' }}
      />

      {/* Главы и параграфы - без UI, только для ReferenceInput */}
      <Resource name="chapters" />
      <Resource name="paragraphs" />
      <Resource name="school-chapters" />
      <Resource name="school-paragraphs" />
      <Resource name="questions" />
      <Resource name="school-questions" />

      {/* Custom routes */}
      <CustomRoutes>
        <Route path="/school-settings" element={<SchoolSettings />} />
      </CustomRoutes>
    </Admin>
  );
}

export default App;
