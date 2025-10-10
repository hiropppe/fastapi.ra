import calendar
import datetime

JST = datetime.timezone(datetime.timedelta(hours=9), "JST")

MAX_DATE = datetime.date(9999, 12, 31)
MAX_DATETIME = datetime.datetime(9999, 12, 31, 23, 59, 59, tzinfo=JST)


def calculate_age(birthday: datetime.date) -> int:
    """年齢を計算する"""
    today = datetime.datetime.now(JST).date()
    return calculate_age_at(birthday, today)


def calculate_age_at(birthday: datetime.date, at: datetime.date) -> int:
    """指定日の年齢を計算する"""
    if not (birthday and at):
        raise ValueError("birthday and at must be set")
    return (int(at.strftime("%Y%m%d")) - int(birthday.strftime("%Y%m%d"))) // 10000


def jstnow() -> datetime.datetime:
    """JSTの現在日時を返す"""
    return datetime.datetime.now(JST)


def jsttoday() -> datetime.date:
    """JSTの今日の日付を返す"""
    return datetime.datetime.now(JST).date()


def get_last_datetime_of_month(dt: datetime.datetime) -> datetime.datetime:
    """月の最終日の23:59:59を返す"""
    return dt.replace(
        day=calendar.monthrange(dt.year, dt.month)[1], hour=23, minute=59, second=59
    )


def utc_to_jst(utc_datetime: datetime.datetime) -> datetime.datetime:
    """UTCの日時をJSTの日時に変換して返す"""
    return utc_datetime.replace(tzinfo=datetime.UTC).astimezone(JST)


def parse_utc_to_jst(utc_datetime: str) -> datetime.datetime:
    """UTCの日時文字列をJSTの日時に変換して返す"""
    return utc_to_jst(datetime.datetime.strptime(utc_datetime, "%Y-%m-%dT%H:%M:%S.%fZ"))
