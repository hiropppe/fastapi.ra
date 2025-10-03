import React, { useState } from 'react';
import {
    Box,
    Button,
    Card,
    CardContent,
    CircularProgress,
    TextField,
    Typography,
    Link,
    Alert,
} from '@mui/material';
import { useNotify } from 'react-admin';
import { AuthClient } from './authClient';

interface ForgotPasswordFormProps {
    onSuccess: (username: string) => void;
    onBackToLogin: () => void;
    authClient: ReturnType<typeof AuthClient>;
}

const ForgotPasswordForm: React.FC<ForgotPasswordFormProps> = ({
    onSuccess,
    onBackToLogin,
    authClient,
}) => {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [errors, setErrors] = useState<{[key: string]: string}>({});
    const [success, setSuccess] = useState(false);
    const notify = useNotify();

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();
        
        const newErrors: {[key: string]: string} = {};

        if (!email) {
            newErrors.email = 'メールアドレスを入力してください';
        } else if (email.trim().length === 0) {
            newErrors.email = '有効なメールアドレスを入力してください';
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            newErrors.email = '有効なメールアドレスの形式で入力してください';
        }

        if (Object.keys(newErrors).length > 0) {
            setErrors(newErrors);
            return;
        }

        setLoading(true);
        setErrors({});

        try {
            // Trim whitespace from inputs
            const trimmedUsername = username.trim();
            const trimmedEmail = email.trim();
            
            await authClient.forgotPassword(trimmedUsername, trimmedEmail);
            setSuccess(true);
            // Login.tsx側で成功メッセージを表示するため、ここでは表示しない
            onSuccess(trimmedUsername);
        } catch (error: any) {
            console.error('Forgot password error:', error);
            const errorMessage = error.body?.detail || error.message || 'パスワードリセット要求に失敗しました';
            
            // エラーメッセージに基づいて適切なフィールドにエラーを設定
            if (errorMessage.includes('ユーザー名またはメールアドレスが一致しません')) {
                setErrors({ 
                    username: errorMessage,
                    email: errorMessage
                });
            } else {
                setErrors({ general: errorMessage });
            }
            
            notify(errorMessage, { type: 'error' });
        } finally {
            setLoading(false);
        }
    };

    if (success) {
        return (
            <Card sx={{ maxWidth: 500, margin: 'auto' }}>
                <CardContent>
                    <Typography variant="h5" component="h1" gutterBottom align="center">
                        メールを確認してください
                    </Typography>
                    <Alert severity="success" sx={{ mb: 2 }}>
                        一時パスワードを登録されたメールアドレスに送信しました。
                        ログイン画面で一時パスワードを使用してログインしてください。
                    </Alert>
                    <Box sx={{ textAlign: 'center' }}>
                        <Link
                            component="button"
                            variant="body2"
                            onClick={onBackToLogin}
                            sx={{ mt: 2 }}
                        >
                            ログイン画面に戻る
                        </Link>
                    </Box>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card sx={{ maxWidth: 500, margin: 'auto' }}>
            <CardContent>
                <Typography variant="h5" component="h1" gutterBottom align="center">
                    パスワードを忘れた場合
                </Typography>
                <Typography variant="body2" color="text.secondary" align="center" sx={{ mb: 3 }}>
                    一時パスワードを発行しますので、登録されたメールアドレスを入力してください。
                </Typography>

                {errors.general && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                        {errors.general}
                    </Alert>
                )}
                
                <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>                    
                    <TextField
                        margin="normal"
                        required
                        fullWidth
                        id="email"
                        label="メールアドレス"
                        name="email"
                        type="email"
                        autoComplete="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        error={!!errors.email}
                        helperText={errors.email}
                        disabled={loading}
                    />
                    
                    <Button
                        type="submit"
                        fullWidth
                        variant="contained"
                        sx={{ mt: 3, mb: 2 }}
                        disabled={loading}
                    >
                        {loading ? (
                            <CircularProgress size={24} />
                        ) : (
                            'パスワードをリセット'
                        )}
                    </Button>
                    
                    <Box sx={{ textAlign: 'center' }}>
                        <Link
                            component="button"
                            variant="body2"
                            onClick={onBackToLogin}
                            disabled={loading}
                        >
                            ログイン画面に戻る
                        </Link>
                    </Box>
                </Box>
            </CardContent>
        </Card>
    );
};

export default ForgotPasswordForm;