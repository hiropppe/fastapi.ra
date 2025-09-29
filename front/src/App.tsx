import polyglotI18nProvider from 'ra-i18n-polyglot';
import englishMessages from './i18n/en';
import japaneseMessages from './i18n/ja';

import { Admin, Resource, localStorageStore, useStore, useTranslate } from "react-admin";
import { Layout } from "./Layout";
import { CognitoAuthProvider } from "./auth/authProvider";
import { Login } from "./auth/Login";
import { dataProvider } from "./ra/dataProvider";
import users from "./users";

const i18nProvider = polyglotI18nProvider(
    locale => {
      if (locale === 'ja') {
        return japaneseMessages;
      } else {
        return englishMessages;
      }
    },
    'ja',
    [
      { locale: 'ja', name: '日本語' },
      { locale: 'en', name: 'English' },
    ]
  );

const authProvider = CognitoAuthProvider();
const store = localStorageStore(undefined, 'tuto');

export const App = () => {
    const translate = useTranslate();

    return (
        <Admin
          layout={Layout}
          dataProvider={dataProvider}
          authProvider={authProvider}
          store={store}
          loginPage={Login}
          i18nProvider={i18nProvider}
          disableTelemetry
          defaultTheme="light"
        >
            <Resource name="users" options={{ label: translate(`resources.users.name`) }} {...users}/>
        </Admin>
    )
}
