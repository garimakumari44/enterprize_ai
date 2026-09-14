from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.models.collection import Collection


class CollectionRepository:
    """
    Repository for knowledge collections.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, collection: Collection) -> Collection:
        self.db.add(collection)
        self.db.commit()
        self.db.refresh(collection)
        return collection

    def get(self, collection_id: int) -> Optional[Collection]:
        return (
            self.db.query(Collection)
            .filter(Collection.id == collection_id)
            .first()
        )

    def list(self) -> List[Collection]:
        return self.db.query(Collection).all()

    def update(self, collection: Collection):
        self.db.commit()
        self.db.refresh(collection)
        return collection

    def delete(self, collection_id: int):
        collection = self.get(collection_id)

        if collection:
            self.db.delete(collection)
            self.db.commit()