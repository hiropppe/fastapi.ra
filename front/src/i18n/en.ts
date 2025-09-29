import { TranslationMessages } from 'react-admin';
import englishMessages from 'ra-language-english';

const customEnglishMessages: TranslationMessages = {
    ...englishMessages,
    pos: {
        search: 'Search',
        configuration: 'Configuration',
        language: 'Language',
        theme: {
            name: 'Theme',
            light: 'Light',
            dark: 'Dark',
        },
        dashboard: {
        },
        menu: {
        },
        appbar: {
            usermenu: {
                password: 'Change Password'
            }
        },
    },
    resources: {
        users: {
            name: 'User |||| Users',
            detail: 'User Detail',
            fields: {
                id: 'id',
                username: 'username',
                nickname: 'nickname',
                email: 'email',
            }
        },
    },
};

export default customEnglishMessages;
