import ipaddress

from fastapi import Request

from tuto.auth.exceptions import AccessDeniedError


def get_client_ip(request: Request) -> str | None:
    """クライアントの実際のIPアドレスを取得する"""
    # X-Forwarded-For ヘッダーを確認
    forwarded_for = request.headers.get("X-Forwarded-For")

    if forwarded_for:
        # 最初のIPがオリジナルのクライアントIP
        # X-Forwarded-For: client, proxy1, proxy2, ...
        client_ip = forwarded_for.split(",")[0].strip()
        return client_ip

    # フォールバック: 直接接続の場合（テスト環境など）
    return request.client.host if request.client else None


class IPRestriction:
    """特定ユーザーのIPアドレス制限を管理するクラス"""

    def __init__(self, allowed_ips: list[str] | None = None) -> None:
        self.allowed_ips = allowed_ips if allowed_ips else []

    @property
    def is_restricted(self) -> bool:
        return bool(self.allowed_ips)

    def is_ip_allowed(self, ip: str) -> bool:
        """IPアドレスが許可リストにあるか確認"""
        if not self.allowed_ips:  # 制限なしの場合
            return True

        try:
            client_ip = ipaddress.ip_address(ip)

            # 許可されたIPリストをチェック
            for allowed_ip in self.allowed_ips:
                # CIDR表記チェック（例: 192.168.1.0/24）
                if "/" in allowed_ip:
                    network = ipaddress.ip_network(allowed_ip, strict=False)
                    if client_ip in network:
                        return True
                # 単一IPアドレスの比較
                elif ip == allowed_ip:
                    return True

            return False
        except ValueError:
            # IPアドレスの解析に失敗
            return False


devtest_ips = [
    "192.168.88.0/24",
    "10.0.0.0/16",
]

password_reset_restricted_ips = []

user_ip_restrictions = {}


def verify_ip_access(request: Request, user_id: str) -> bool:
    """ユーザーのIPアクセス制限を確認するミドルウェア関数"""
    client_ip = get_client_ip(request)

    if user_id not in user_ip_restrictions:
        return False

    ip_restriction: IPRestriction = user_ip_restrictions[user_id]

    if ip_restriction.is_restricted:
        if ip_restriction.is_ip_allowed(client_ip):
            return True

        msg = "Access denied from this IP address"
        raise AccessDeniedError(msg)

    return False
