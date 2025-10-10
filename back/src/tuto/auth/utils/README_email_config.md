# Email Configuration

パスワードリセット機能で使用する環境変数の設定について

## 必要な環境変数

```bash
# AWS SES設定
AWS_DEFAULT_REGION=ap-northeast-1  # AWSリージョン (デフォルト: ap-northeast-1)
AUTH_SES_CONFIG_SET=""             # SES Configuration Set名 (オプション)
AUTH_FROM_EMAIL="noreply@example.com"  # 送信者メールアドレス

# AWS認証情報 (通常はIAMロールまたはプロファイルで設定)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

## SES の設定要件

1. **送信者メールアドレスの認証**
   - `AUTH_FROM_EMAIL` で指定するメールアドレスまたはドメインがSESで認証済みである必要があります

2. **IAM権限**
   - アプリケーションに以下のSES権限が必要です：
     - `ses:SendEmail`
     - `ses:SendRawEmail`

3. **Configuration Set (オプション)**
   - メール送信の追跡や制御のためにConfiguration Setを使用できます
   - `AUTH_SES_CONFIG_SET` で指定

## テンプレートファイル

- 一時パスワード送信: `common/templates/auth/temporary_password.j2`
- パスワードリセット完了通知: `common/templates/auth/password_reset_success.j2`

## ログ出力

- 成功時: INFO レベルでメッセージIDを含むログ
- 失敗時: ERROR レベルでエラー詳細を含むログ