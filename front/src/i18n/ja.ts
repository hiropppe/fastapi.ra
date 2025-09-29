import { TranslationMessages } from 'react-admin';
import japaneseMessages from "@bicstone/ra-language-japanese";

const customJapaneseMessages: TranslationMessages = {
    ...japaneseMessages,
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

export default customJapaneseMessages;
