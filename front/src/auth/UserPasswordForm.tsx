import { Button, CardContent, CircularProgress, Link, Box } from '@mui/material';
import clsx from 'clsx';
import * as React from 'react';
import {
    Form,
    LoginFormClasses,
    TextInput,
    PasswordInput,
    required,
    useTranslate,
} from 'react-admin';
import type { SubmitHandler } from 'react-hook-form';
import type { FormData } from './useCognitoLogin';

export type UserPasswordFormProps = {
    className?: string;
    submit: SubmitHandler<FormData>;
    isLoading?: boolean;
    onForgotPassword?: () => void;
};

export const UserPasswordForm = ({
    className,
    submit,
    isLoading,
    onForgotPassword,
}: UserPasswordFormProps) => {
    const translate = useTranslate();
    const [shouldThrowError, setShouldThrowError] = React.useState(false);
    
    // 🔥 デバッグ用: render時にエラーを発生させる
    if (shouldThrowError) {
        throw new Error('Test error from UserPasswordForm render');
    }
    return (
        <Form
            onSubmit={submit}
            mode="onSubmit"
            noValidate
            className={clsx('RaLoginForm-root', className)}
        >
            <CardContent 
                className={LoginFormClasses.content}
                sx={{
                    padding: '24px 32px',
                    '&:last-child': {
                        paddingBottom: '24px'
                    }
                }}
            >
                <TextInput
                    autoFocus
                    source="username"
                    label={translate('auth.username_or_email')}
                    validate={required()}
                    fullWidth
                />
                <PasswordInput
                    source="password"
                    label={translate('ra.auth.password')}
                    autoComplete="current-password"
                    validate={required()}
                    fullWidth
                />
                <TextInput
                    source="challengeName"
                    defaultValue='ADMIN_USER_PASSWORD_AUTH'
                    style={{display:'none'}}
                />
                <Button
                    variant="contained"
                    type="submit"
                    color="primary"
                    disabled={isLoading}
                    fullWidth
                    className={LoginFormClasses.button}
                >
                    {isLoading ? (
                        <CircularProgress
                            className={LoginFormClasses.icon}
                            size={19}
                            thickness={3}
                        />
                    ) : (
                        translate('ra.auth.sign_in')
                    )}
                </Button>
                
                {onForgotPassword && (
                    <Box sx={{ textAlign: 'center', mt: 2 }}>
                        <Link
                            component="button"
                            variant="body2"
                            onClick={(e) => {
                                e.preventDefault();
                                onForgotPassword();
                            }}
                            disabled={isLoading}
                        >
                            パスワードを忘れた場合
                        </Link>
                    </Box>
                )}
            </CardContent>
        </Form>
    );
};
