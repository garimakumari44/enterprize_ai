from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class SearchPrincipal:
    """
    Identity used when evaluating knowledge-search permissions.
    """

    user_id: str
    company_id: str | None = None


class SearchAccessController:
    """
    Authorization boundary for knowledge search.
    """

    def can_search(
        self,
        principal: SearchPrincipal,
    ) -> bool:
        return bool(principal.user_id)

    def require_search_access(
        self,
        principal: SearchPrincipal,
    ) -> None:
        if not self.can_search(principal):
            raise PermissionError(
                "User is not authorized to perform knowledge search."
            )

    def can_access_document(
        self,
        principal: SearchPrincipal,
        document_company_id: str | None,
    ) -> bool:

        if not principal.user_id:
            return False

        if (
            principal.company_id is not None
            and document_company_id is not None
            and principal.company_id != document_company_id
        ):
            return False

        return True

    def filter_document_ids(
        self,
        principal: SearchPrincipal,
        documents: Iterable[tuple[str, str | None]],
    ) -> list[str]:

        if not self.can_search(principal):
            return []

        allowed: list[str] = []

        for document_id, company_id in documents:
            if self.can_access_document(
                principal,
                company_id,
            ):
                allowed.append(document_id)

        return allowed