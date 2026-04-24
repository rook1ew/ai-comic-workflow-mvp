from typing import Any

from sqlalchemy.orm import Session


def create_and_refresh(db: Session, instance: Any) -> Any:
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance
