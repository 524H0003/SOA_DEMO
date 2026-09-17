from app.config import get_settings
from app.db import SessionLocal, init_db
from app.models import GmailSyncState
from app.services.gmail import start_watch


if __name__ == "__main__":
    init_db()
    settings = get_settings()
    response = start_watch(settings)
    with SessionLocal() as db:
        state = db.get(GmailSyncState, 1) or GmailSyncState(id=1)
        state.last_history_id = str(response["historyId"])
        state.watch_expiration = None
        db.add(state)
        db.commit()
    print(response)
