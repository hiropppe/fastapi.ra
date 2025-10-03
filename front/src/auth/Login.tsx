import * as React from 'react';
import { Login as RaLogin, useNotify } from 'react-admin';
import clsx from 'clsx';
import { SubmitHandler } from 'react-hook-form';
import { RequestNewPasswordForm } from './RequestNewPasswordForm';
import { MfaTotpForm } from './MfaTotpForm'
import { UserPasswordForm } from './UserPasswordForm';
import ForgotPasswordForm from './ForgotPasswordForm';
import { AuthClient } from './authClient';
import type { FormData } from './useCognitoLogin';
import { useCognitoLogin } from './useCognitoLogin';

type PasswordResetState = 'login' | 'forgot';

interface PasswordResetData {
    username?: string;
}

export const Login = (props: any) => {
    return (
        <RaLogin 
            {...props}
            sx={{
                '& .RaLogin-card': {
                    minWidth: 'unset',
                    maxWidth: '600px',
                    width: '100%'
                },
                '& .RaLoginForm-root': {
                    width: '100%',
                    // デフォルトは500px
                    maxWidth: '500px',
                    margin: '0 auto'
                },
                // RequestNewPasswordForm だけ幅を広く
                '& .RaRequestNewPasswordForm': {
                    maxWidth: '600px !important'
                },
                // RequestNewPasswordForm の親 Box も幅を広く
                '& .RequestNewPasswordFormWrapper': {
                    maxWidth: '600px !important'
                },
                // ForgotPasswordForm のCard も同じ位置に配置
                '& .MuiCard-root': {
                    minWidth: 'unset',
                    maxWidth: '500px',
                    width: '100%',
                    margin: '0 auto',
                    marginTop: '8vh'
                },
                // wide-form クラスがある場合のCard
                '& .wide-form ~ .MuiCard-root, &:has(.wide-form) .MuiCard-root': {
                    maxWidth: '600px !important'
                }
            }}
        >
            <LoginForm />
        </RaLogin>
    );
};

export const LoginForm = (props: any) => {
    const { redirectTo, className } = props;
    const notify = useNotify();
    
    const [passwordResetState, setPasswordResetState] = React.useState<PasswordResetState>('login');
    const [passwordResetData, setPasswordResetData] = React.useState<PasswordResetData>({});
    
    const [
        login,
        {
            isPending,
            requireNewPassword,
            requireMfaTotp,
            requireMfaTotpAssociation,
            secretCode,
            username,
            applicationName,
        },
    ] = useCognitoLogin({
        redirectTo,
    });

    // 認証クライアントの初期化
    const authClient = React.useMemo(() => {
        const authProviderUrl = import.meta.env.VITE_AUTH_PROVIDER_URL || 'http://localhost:8001/auth';
        return AuthClient(authProviderUrl);
    }, []);

    const submit: SubmitHandler<FormData> = values => {
        // Trim whitespace from input values
        const trimmedValues = {
            ...values,
            username: values.username?.trim() || '',
            password: values.password?.trim() || '',
            totp: values.totp?.trim() || '',
            newPassword: values.newPassword?.trim() || '',
            confirmNewPassword: values.confirmNewPassword?.trim() || '',
        };
        
        login(trimmedValues).catch(error => {
            notify(
                typeof error === 'string'
                    ? error
                    : typeof error === 'undefined' || !error.message
                      ? 'ra.auth.sign_in_error'
                      : error.message,
                {
                    type: 'error',
                    messageArgs: {
                        _:
                            typeof error === 'string'
                                ? error
                                : error && error.message
                                  ? error.message
                                  : undefined,
                    },
                }
            );
        });
    };

    // パスワードリセット関連の状態管理
    const handleForgotPassword = () => {
        setPasswordResetState('forgot');
    };

    const handleForgotPasswordSuccess = (username: string) => {
        setPasswordResetData({ username });
        setPasswordResetState('login');
        notify('一時パスワードをメールに送信しました。一時パスワードでログインして新しいパスワードを設定してください。', { 
            type: 'success',
            autoHideDuration: null  // nullにすると手動で閉じるまで表示される
        });
    };

    const handleBackToLogin = () => {
        setPasswordResetState('login');
        setPasswordResetData({});
    };

    // パスワードリセットフローの表示
    if (passwordResetState === 'forgot') {
        return (
            <ForgotPasswordForm
                onSuccess={handleForgotPasswordSuccess}
                onBackToLogin={handleBackToLogin}
                authClient={authClient}
            />
        );
    }

    // 新規パスワード設定フロー
    if (requireNewPassword) {
        return (
            <RequestNewPasswordForm
                submit={submit}
                className={clsx(className, 'wide-form')}
                isLoading={isPending}
            />
        );
    }

    if (requireMfaTotp) {
        return (
            <MfaTotpForm
                submit={submit}
                className={className}
                isLoading={isPending}
            />
        );
    }

    if (requireMfaTotpAssociation) {
        // TODO: Implement MfaTotpAssociationForm component
        return (
            <div>MFA TOTP Association required - component not yet implemented</div>
        );
    }

    return (
        <UserPasswordForm
            submit={submit}
            isLoading={isPending}
            className={className}
            onForgotPassword={handleForgotPassword}
        />
    );
};
