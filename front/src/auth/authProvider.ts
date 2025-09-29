import { AuthProvider, HttpError } from "react-admin";
import type { FormData } from './useCognitoLogin';
import { AuthClient } from './authClient';

const authEndpoint = import.meta.env.VITE_AUTH_PROVIDER_URL;

export const CognitoAuthProvider = (
): AuthProvider => {
    const authClient = AuthClient(authEndpoint);

    const processGetIdentity = async () => {
        return authClient.me().catch(
            ( error: Error ) => {
                if (error.body.detail === 'Not authenticated') {
                    localStorage.removeItem("auth");
                    return Promise.reject(
                        new HttpError("Unauthorized", 401, {
                            message: error.body.detail,
                        })
                    );
                } else if (["AccessTokenExpirationError", "InvalidAccessTokenError"].includes(error.body.error_type)) {
                    return authClient.refreshToken().catch(
                        ( error: Error ) => {
                            if (["AccessTokenRefreshError", "TokenRefreshNotSupportedError", "AuthInfoNotFoundError"].includes(error.body.error_type)) {
                                localStorage.removeItem("auth");
                                return Promise.reject(
                                    new HttpError("Unauthorized", 401, {
                                        error_type: error.body["error_type"],
                                        error_detail: error.body["error_detail"],
                                    })
                                );
                            };
                            return Promise.resolve();
                        }
                    ).then(
                        () => {
                            return authClient.me().catch(
                                (error: Error) => {
                                    if (["AccessTokenExpirationError", "InvalidAccessTokenError"].includes(error.body.error_type)) {
                                        localStorage.removeItem("auth");
                                        return Promise.reject(
                                            new HttpError("Unauthorized", 401, {
                                                message: "Session invalidated unexpectedly (After token refreshed)",
                                            })
                                        );
                                    }
                                    return Promise.resolve();
                                }
                            )
                        }
                    );
                } else if (["AccessDeniedError"].includes(error.body.error_type)) {
                    return Promise.resolve();
                } else {
                    return Promise.resolve();
                }
            }
        )
    }
    
    return {
        async login(form: FormData) {
            if (form.challengeName == 'ADMIN_USER_PASSWORD_AUTH') {
                return authClient.login(form.username, form.password, 'ADMIN_USER_PASSWORD_AUTH');
            } else if (form.challengeName == 'EMAIL_OTP') {
                return authClient.verifyTOTP(form.totp, 'EMAIL_OTP');
            } else if (form.challengeName == 'NEW_PASSWORD_REQUIRED') {
                return authClient.respond_to_new_password_required(form.newPassword, 'NEW_PASSWORD_REQUIRED');
            }
        },

        async checkError(error: Error) {
            if (!localStorage.getItem('auth')) {
                return Promise.resolve();
            }

            return await processGetIdentity()
        },

        async checkAuth() {
            if (!localStorage.getItem('auth')) {
                throw new Error('auth.errors.session_expired');
            }
        },

        async getPermissions() {
            return Promise.resolve(undefined);
        },

        async logout() {
            if (!localStorage.getItem('auth')) {
                return Promise.resolve();
            }
            
            authClient.discardToken();
            localStorage.removeItem("auth");
            return Promise.resolve();
        },

        async getIdentity() {
            return await processGetIdentity()
        },
    }
}
