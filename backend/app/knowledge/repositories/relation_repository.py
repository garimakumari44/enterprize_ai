# from __future__ import annotations

# from typing import List

# from sqlalchemy.orm import Session

# from app.db.models.relation import Relation


# class RelationRepository:
#     """
#     Repository for knowledge graph relations.
#     """

#     def __init__(self, db: Session):
#         self.db = db

#     def create(self, relation: Relation) -> Relation:
#         self.db.add(relation)
#         self.db.commit()
#         self.db.refresh(relation)
#         return relation

#     def get_all(self) -> List[Relation]:
#         return self.db.query(Relation).all()

#     def get_by_entity(self, entity_id: int):
#         return (
#             self.db.query(Relation)
#             .filter(
#                 (Relation.source_entity_id == entity_id)
#                 | (Relation.target_entity_id == entity_id)
#             )
#             .all()
#         )

#     def delete(self, relation_id: int):
#         relation = (
#             self.db.query(Relation)
#             .filter(Relation.id == relation_id)
#             .first()
#         )

#         if relation:
#             self.db.delete(relation)
#             self.db.commit()