import services
from core import DummyDatabase
from core.schemas import User

dummy_db = DummyDatabase()


async def report(initiator: User, target_user_id: str | None) -> None:
    target_user_id = "" if target_user_id is None else target_user_id
    target_user = dummy_db.users.get_by_id(idx=target_user_id)
    if target_user is None:
        error_message = "[*] User with %s id does not exists\n" % target_user_id
        initiator.writer.write(error_message.encode())
        await initiator.writer.drain()
        return

    if target_user.idx != initiator.idx:
        await services.report_on_user(target_user)
