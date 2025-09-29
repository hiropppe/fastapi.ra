import {
    Button,
    CardContent,
    CircularProgress,
    Typography,
    Box,
} from '@mui/material';
import clsx from 'clsx';
import * as React from 'react';
import {
    Form,
    LoginFormClasses,
    PasswordInput,
    TextInput,
    required,
    useTranslate,
} from 'react-admin';
import type { SubmitHandler } from 'react-hook-form';
import type { FormData } from './useCognitoLogin';
import { validatePasswordsMatch, validatePasswordPolicy } from './passwordValidator';


export type RequestNewPasswordFormProps = {
    className?: string;
    submit: SubmitHandler<FormData>;
    isLoading?: boolean;
};

export const RequestNewPasswordForm = ({
    className,
    submit,
    isLoading,
}: RequestNewPasswordFormProps) => {
    const translate = useTranslate();

    return (
        <Box 
            className="RequestNewPasswordFormWrapper"
            sx={{ 
                maxWidth: '600px !important',
                width: '100%', 
                margin: 'auto' 
            }}
        >
            <Form
                onSubmit={submit}
                mode="onChange"
                noValidate
                className={clsx('RaLoginForm-root', 'RaRequestNewPasswordForm', className)}
            >
                <CardContent className={LoginFormClasses.content}>
                <Typography gutterBottom>
                    {translate('auth.cognito.require_new_password', {
                        _: translate('auth.require_new_password', {
                            _: 'Please enter a new password',
                        }),
                    })}
                </Typography>
                <Typography variant="subtitle1">* {translate('auth.password_policy.length8')}</Typography>
                <Typography variant="subtitle1">* {translate('auth.password_policy.available_chars')}</Typography>
                <Typography variant="subtitle1">* {translate('auth.password_policy.max_char_vars')}</Typography>
                <PasswordInput
                    source="newPassword"
                    label={translate('auth.password')}
                    inputProps={{ autoComplete: 'off' }}
                    validate={validatePasswordPolicy}
                    required
                    fullWidth
                    sx={{
                        '& .MuiFormHelperText-root': {
                            whiteSpace: 'pre-line',
                            wordWrap: 'break-word',
                            maxWidth: '100%'
                        }
                    }}
                />
                <PasswordInput
                    source="confirmNewPassword"
                    label={translate('auth.confirm_password', {
                        _: 'Confirm password',
                    })}
                    inputProps={{ autoComplete: 'off' }}
                    validate={validatePasswordsMatch('newPassword')}
                    required
                    fullWidth
                />
                <TextInput
                    source="challengeName"
                    defaultValue='NEW_PASSWORD_REQUIRED'
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
        </Box>
    );
};
