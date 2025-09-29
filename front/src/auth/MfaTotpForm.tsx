import { Button, CardContent, CircularProgress, Typography } from '@mui/material';
import clsx from 'clsx';
import * as React from 'react';
import {
    Form,
    LoginFormClasses,
    TextInput,
    required,
    useTranslate,
} from 'react-admin';
import type { SubmitHandler } from 'react-hook-form';
import type { FormData } from './useCognitoLogin';

export type MfaTotpFormProps = {
    className?: string;
    submit: SubmitHandler<FormData>;
    isLoading?: boolean;
};

export const MfaTotpForm = ({
    className,
    submit,
    isLoading,
}: MfaTotpFormProps) => {
    const translate = useTranslate();

    return (
        <Form
            onSubmit={submit}
            mode="onChange"
            noValidate
            className={clsx('RaLoginForm-root', className)}
        >
            <CardContent
                className={LoginFormClasses.content}
                sx={{
                    width: '500px',
                }}
            >
                <Typography>
                    {translate('auth.cognito.mfa.totp.message')}
                </Typography>
                <TextInput
                    autoFocus
                    source="totp"
                    label="auth.cognito.mfa.totp.label"
                    validate={required()}
                    fullWidth
                    InputProps={{
                        autoComplete: 'false',
                    }}
                />
                <TextInput
                    source="challengeName"
                    defaultValue='EMAIL_OTP'
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
            </CardContent>
        </Form>
    );
};
