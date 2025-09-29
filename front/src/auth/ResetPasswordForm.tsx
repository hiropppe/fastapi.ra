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
    IconButton,
    InputAdornment,
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import { useNotify } from 'react-admin';
import { AuthClient } from './authClient';

interface ResetPasswordFormProps {
    username: string;
    onSuccess: () => void;
    onBackToLogin: () => void;
    authClient: ReturnType<typeof AuthClient>;
}

const ResetPasswordForm: React.FC<ResetPasswordFormProps> = ({
    username,
    onSuccess,
    onBackToLogin,
    authClient,
}) => {
    const [temporaryPassword, setTemporaryPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [errors, setErrors] = useState<{[key: string]: string}>({});
    const notify = useNotify();

    const validatePassword = (password: string): string[] => {
        const errors: string[] = [];
        
        if (password.length < 8) {
            errors.push('8文字以上である必要があります');
        }
        if (!/\d/.test(password)) {
            errors.push('数字を1つ以上含む必要があります');
        }
        if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
            errors.push('特殊文字を1つ以上含む必要があります');
        }
        if (!/[A-Z]/.test(password)) {
            errors.push('大文字を1つ以上含む必要があります');
        }
        if (!/[a-z]/.test(password)) {
            errors.push('小文字を1つ以上含む必要があります');
        }
        
        return errors;
    };

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();
        
        const newErrors: {[key: string]: string} = {};

        // バリデーション
        if (!temporaryPassword) {
            newErrors.temporaryPassword = '一時パスワードを入力してください';
        } else if (temporaryPassword.length < 8) {
            newErrors.temporaryPassword = '一時パスワードは8文字以上である必要があります';
        }

        if (!newPassword) {
            newErrors.newPassword = 'パスワードを入力してください';
        } else {
            const passwordErrors = validatePassword(newPassword);
            if (passwordErrors.length > 0) {
                newErrors.newPassword = passwordErrors.join('、');
            }
        }

        if (!confirmPassword) {
            newErrors.confirmPassword = 'パスワード確認を入力してください';
        } else if (newPassword !== confirmPassword) {
            newErrors.confirmPassword = 'パスワードが一致しません';
        }

        if (Object.keys(newErrors).length > 0) {
            setErrors(newErrors);
            return;
        }

        setLoading(true);
        setErrors({});

        try {
            // Trim whitespace from password inputs
            const trimmedTemporaryPassword = temporaryPassword.trim();
            const trimmedNewPassword = newPassword.trim();
            
            await authClient.resetPassword(username, trimmedTemporaryPassword, trimmedNewPassword);
            notify('パスワードが正常にリセットされました', { type: 'success' });
            onSuccess();
        } catch (error: any) {
            console.error('Reset password error:', error);
            const errorMessage = error.body?.detail || error.message || 'パスワードリセットに失敗しました';
            
            // エラーメッセージに基づいて適切なフィールドにエラーを設定
            if (errorMessage.includes('一時パスワード') || errorMessage.includes('temporary password')) {
                setErrors({ temporaryPassword: errorMessage });
            } else if (errorMessage.includes('パスワード')) {
                setErrors({ newPassword: errorMessage });
            } else {
                setErrors({ general: errorMessage });
            }
            
            notify(errorMessage, { type: 'error' });
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card sx={{ maxWidth: 400, margin: 'auto', mt: 8 }}>
            <CardContent>
                <Typography variant="h5" component="h1" gutterBottom align="center">
                    パスワードリセット
                </Typography>
                <Typography variant="body2" color="text.secondary" align="center" sx={{ mb: 3 }}>
                    登録されたメールアドレスに送信された一時パスワードと新しいパスワードを入力してください。
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
                        id="temporaryPassword"
                        label="一時パスワード"
                        name="temporaryPassword"
                        type="password"
                        autoComplete="current-password"
                        autoFocus
                        value={temporaryPassword}
                        onChange={(e) => setTemporaryPassword(e.target.value)}
                        error={!!errors.temporaryPassword}
                        helperText={errors.temporaryPassword || 'メールで送信された一時パスワードを入力してください'}
                        disabled={loading}
                    />
                    
                    <TextField
                        margin="normal"
                        required
                        fullWidth
                        id="newPassword"
                        label="新しいパスワード"
                        name="newPassword"
                        type={showPassword ? 'text' : 'password'}
                        autoComplete="new-password"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        error={!!errors.newPassword}
                        helperText={errors.newPassword}
                        disabled={loading}
                        InputProps={{
                            endAdornment: (
                                <InputAdornment position="end">
                                    <IconButton
                                        aria-label="toggle password visibility"
                                        onClick={() => setShowPassword(!showPassword)}
                                        edge="end"
                                    >
                                        {showPassword ? <VisibilityOff /> : <Visibility />}
                                    </IconButton>
                                </InputAdornment>
                            ),
                        }}
                    />
                    
                    <TextField
                        margin="normal"
                        required
                        fullWidth
                        id="confirmPassword"
                        label="パスワード確認"
                        name="confirmPassword"
                        type={showConfirmPassword ? 'text' : 'password'}
                        autoComplete="new-password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        error={!!errors.confirmPassword}
                        helperText={errors.confirmPassword}
                        disabled={loading}
                        InputProps={{
                            endAdornment: (
                                <InputAdornment position="end">
                                    <IconButton
                                        aria-label="toggle confirm password visibility"
                                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                        edge="end"
                                    >
                                        {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                                    </IconButton>
                                </InputAdornment>
                            ),
                        }}
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

export default ResetPasswordForm;