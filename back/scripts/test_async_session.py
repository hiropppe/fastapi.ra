import asyncio
import pathlib
import sys

# プロジェクトのパスを追加
sys.path.append(
    pathlib.Path(pathlib.Path(pathlib.Path(__file__).resolve()).parent).parent.__str__()
)


from tuto.auth.auth_helper import hash_password
from tuto.datasource.database import async_engine, async_session
from tuto.model.user import NewUser, User


async def create_test_user() -> None:
    """
    テストユーザを作成するスクリプト
    # async with を使うことでセッションが自動的に適切にクローズされ、
    # await async_engine.dispose() でイベントループ終了前に接続プールがクリーンアップされる
    """
    # async context managerを使用
    async with async_session() as asession:
        new_user = NewUser(
            username="testuser",
            email="testuser@test.com",
            nickname="test",
            password="testtest",
        )
        new_user.hashed_password = hash_password(new_user.password)

        db_user = User.model_validate(new_user)

        asession.add(db_user)

        await asession.commit()

    # エンジンを明示的にクリーンアップ
    await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_test_user())
