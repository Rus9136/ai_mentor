import { Admin, Resource, ListGuesser } from 'react-admin';
import { authProvider, dataProvider } from './providers';

function App() {
  return (
    <Admin
      authProvider={authProvider}
      dataProvider={dataProvider}
      requireAuth
      title="AI Mentor Admin"
    >
      {/* Пока добавим пустой ресурс для тестирования */}
      {/* Resources будут добавлены в Фазе 3 */}
      <Resource name="schools" list={ListGuesser} />
    </Admin>
  );
}

export default App;
