import { fetchUtils, HttpError } from "react-admin";
import { ErrorMfaTotpRequired, ErrorRequireNewPassword } from "./Errors";


export const AuthClient = ( endpointRoot: string ) => {
    return {
        login: (username: string, password: string, challengeName: string) => {
            const url = `${endpointRoot}/token`
            return fetchUtils
                .fetchJson(url, {
                    method: "POST",
                    headers: new Headers({
                        "Content-Type": "application/x-www-form-urlencoded",
                    }),
                    body: `grant_type=password&username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}&scope=&client_id=&client_secret=&challenge_name=${challengeName}`,
                    credentials: 'include'
                })
                .catch(
                    ( error: HttpError ) => {
                        if (error.status === 403) {
                            return Promise.reject(new Error('アクセスが禁止されています。サポートにお問い合わせください。'));
                        }
                        return Promise.reject(new Error('ra.auth.sign_in_error'));
                    }
                )
                .then(
                    ({ json }) => {
                        console.log(json);
                        if (json) {
                            if ("challenge_name" in json) {
                                if (json["challenge_name"] == "EMAIL_OTP") {
                                    return Promise.reject(new ErrorMfaTotpRequired());
                                }
                                if (json["challenge_name"] == "NEW_PASSWORD_REQUIRED") {
                                    return Promise.reject(new ErrorRequireNewPassword());
                                }
                            } else {
                                localStorage.setItem("auth", JSON.stringify(json));
                                return Promise.resolve();
                            }
                        }
                        return Promise.reject(
                            new HttpError("Invalid username or password", 401)
                        );
                    }
                );
        },

        verifyTOTP: (totp: string, challengeName: string) => {
            const url = `${endpointRoot}/verify_totp`
            
            // Trim whitespace from TOTP code
            const trimmedTotp = totp.trim();

            return fetchUtils
                .fetchJson(url, {
                    method: "POST",
                    headers: new Headers({
                        "Content-Type": "application/x-www-form-urlencoded",
                    }),
                    body: `grant_type=password&mfa_code=${encodeURIComponent(trimmedTotp)}&scope=&client_id=&client_secret=&challenge_name=${challengeName}`,
                    credentials: 'include'
                })
                .catch(
                    ( error: HttpError ) => {
                        localStorage.removeItem("auth");
                        return Promise.reject(
                            new HttpError(error.body.detail, 401)
                        );
                    }
                )
                .then(
                    ({ json }) => {
                        if (json) {
                            localStorage.setItem("auth", JSON.stringify(json));
                            return Promise.resolve();
                        }
                        localStorage.removeItem("auth");
                        return Promise.reject(
                            new HttpError("Unauthorized", 401, {
                                message: "Invalid authentication code",
                            })
                        );
                    }
                );
        },

        respond_to_new_password_required: (newPassword: string, challengeName: string) => {
            const url = `${endpointRoot}/set_new_password`
            
            // Trim whitespace from new password
            const trimmedNewPassword = newPassword.trim();
            
            return fetchUtils
                .fetchJson(url,
                    {
                        method: "POST",
                        headers: new Headers({
                            "Content-Type": "application/x-www-form-urlencoded",
                        }),
                        body: `grant_type=password&new_password=${encodeURIComponent(trimmedNewPassword)}&scope=&client_id=&client_secret=&challenge_name=${challengeName}`,
                        credentials: 'include',
                    }
                )
                .catch(
                    ( error ) => {
                        return Promise.reject(
                            new HttpError("Unauthorized", 401, {
                                message: "Failed to verify authentication code",
                            })
                        );
                    }
                )
                .then(
                    ({ json }) => {
                        if (json) {
                            if ("challenge_name" in json) {
                                if (json["challenge_name"] == "EMAIL_OTP") {
                                    return Promise.reject(new ErrorMfaTotpRequired());
                                }
                            } else {
                                localStorage.setItem("auth", JSON.stringify(json));
                                return Promise.resolve();
                            }
                        }
                        return Promise.reject(
                            new HttpError("Unauthorized", 401, {
                                message: "Invalid authentication code",
                            })
                        );
                    }
                );
        },
    
        me: () => {
            // TODO: use HTTP Headers etc
            const url = `${endpointRoot}/users/me`

            return fetchUtils
                .fetchJson(url, {
                    method: "GET",
                    headers: new Headers({
                        "accept": "application/json"
                    }),
                    credentials: 'include',
                })
                .then(
                    ({ json }) => {
                        if ("nickname" in json) {
                            json["fullName"] = json["nickname"]
                            return Promise.resolve(json);
                        } else {
                            return Promise.reject(
                                new HttpError("Unauthorized", 401, {
                                    message: "detail" in json ? json["detail"] : "Unauthorized",
                                })
                            );
                        }
                    }
                );
        },

        refreshToken: () => {
            const persistedToken = localStorage.getItem("auth");
            if (persistedToken == null) {
                return Promise.reject(
                    new HttpError("Unauthorized", 401, {
                        error_type: "AuthInfoNotFoundError",
                        error_detail: 'token info not found in local storage.',
                    })
                );
            }

            const token = persistedToken ? JSON.parse(persistedToken) : null;
            const refreshable = token["rtk"]

            if (!refreshable) {
                return Promise.reject(
                    new HttpError("Unauthorized", 401, {
                        error_type: "TokenRefreshNotSupportedError",
                        error_detail: "Token refresh not supported",
                    })
                );
            }

            const url = `${endpointRoot}/refresh_token`
        
            return fetchUtils
                .fetchJson(url, {
                    method: "POST",
                    headers: new Headers({
                        "accept": "application/json",
                        "Content-Type": "application/x-www-form-urlencoded",
                    }),
                    credentials: 'include',
                })
                .then(
                    ({ json }) => {
                        if (json) {
                            localStorage.setItem("auth", JSON.stringify(json));
                            return Promise.resolve();
                        }

                        localStorage.removeItem("auth");
                        return Promise.reject(
                            new HttpError("Unauthorized", 401, {
                                message: "Refresh token failed unexpectedly",
                            })
                        );
                    }
                )
        },

        discardToken: () => {
            if (localStorage.getItem("auth") !== null) {
                localStorage.removeItem("auth");
            }

            const url = `${endpointRoot}/discard_token`

            fetchUtils
                .fetchJson(url, {
                    method: "POST",
                    headers: new Headers({
                        "accept": "application/json",
                        "Content-Type": "application/x-www-form-urlencoded",
                    }),
                    credentials: 'include',
                })
                .then(
                    ({ json }) => {
                        //console.info(json);
                    }
                )
                .catch(
                    ( error ) => {
                        console.error(error);
                    }
                );
        },

        forgotPassword: (username: string, email: string) => {
            const url = `${endpointRoot}/forgot_password`
            return fetchUtils
                .fetchJson(url, {
                    method: "POST",
                    headers: new Headers({
                        "Content-Type": "application/json",
                    }),
                    body: JSON.stringify({ username, email }),
                    credentials: 'include'
                })
                .catch(
                    (error: HttpError) => {
                        const errorMessage = error.body?.detail || 'パスワードリセット要求に失敗しました';
                        return Promise.reject(new HttpError(errorMessage, error.status));
                    }
                )
                .then(
                    ({ json }) => {
                        return Promise.resolve(json);
                    }
                );
        },

        checkPasswordResetAvailability: () => {
            const url = `${endpointRoot}/check_password_reset_availability`
            return fetchUtils
                .fetchJson(url, {
                    method: "GET",
                    headers: new Headers({
                        "accept": "application/json"
                    }),
                })
                .catch(
                    (error: HttpError) => {
                        return Promise.resolve({ 
                            json: { 
                                password_reset_available: true, 
                                reason: null 
                            } 
                        });
                    }
                )
                .then(
                    ({ json }) => {
                        return Promise.resolve(json);
                    }
                );
        },
    }
}
