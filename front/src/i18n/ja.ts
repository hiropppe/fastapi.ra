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
    auth: {
        sign_in: 'ログイン',
        username: 'ユーザ名',
        username_or_email: 'ユーザ名またはメールアドレス',
        password: 'パスワード',
        confirm_password: 'パスワード（確認）',
        old_password: '現在のパスワード',
        new_password: '新しいパスワード',
        confirm_new_password: '新しいパスワード（確認）',
        cognito: {
            mfa: {
                totp: {
                    message: '登録されているメールアドレスに送信された認証コードをご入力ください。',
                    label: '認証コード'
                }
            }
        },
        require_new_password: '新しいパスワードを入力してください。',
        password_policy: {
            available_chars: '半角英数字および半角記号 ^ $ * . [ ] { } ( ) ? - " ! @ # % & / \ , > < \' : ; | _ ~ ` + = を使用 ',
            length8: '8文字以上',
            max_char_vars: '数字、記号、大文字、小文字をそれぞれ1文字以上含む',
            contains_number: '数字を1文字以上含む',
            contains_special: '記号を1文字以上含む',
            contains_lowercase: '小文字を1文字以上含む',
            contains_uppercase: '大文字を1文字以上含む',
        },
        errors: {
            auth_session_expired: '認証セッション切れです、最初からやり直してください',
            session_expired: 'セッション切れです、再度ログインしてください'
        }
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
