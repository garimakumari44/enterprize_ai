
"""
app.processing.providers.implementations.pgvector_indexer

PostgreSQL / pgvector indexing provider.

The implementation is intentionally defensive because pgvector may not
be installed or enabled in every development environment.

The provider:

    - validates database configuration
    - lazily imports SQLAlchemy
    - verifies the PostgreSQL vector extension when requested
    - creates vector indexes/tables through the supplied database layer
      where possible
    - keeps database-specific details isolated from the provider contract

Configuration example:

    {
        "session_factory": ...,
        "table_name": "document_embeddings",
        "embedding_dimension": 384,
        "distance": "cosine"
    }

A session factory is preferred over a raw database connection.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping, Sequence

from ..base import (
    ProviderConfigurationError,
    ProviderUnavailableError,
)
from ..indexing import (
    BaseIndexingProvider,
    IndexingRequest,
    IndexingResult,
)

logger = logging.getLogger(__name__)


class PGVectorIndexer(BaseIndexingProvider):
    """
    PostgreSQL + pgvector indexing provider.

    This provider assumes the application already owns its SQLAlchemy
    database configuration. It does not create a global engine.
    """

    PROVIDER_NAME = "pgvector_indexer"

    PROVIDER_TYPE = "indexing"

    VERSION = "1.0"

    DEFAULT_TABLE = "document_embeddings"

    def __init__(
        self,
        *,
        config: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(
            config=config
        )

        self._session_factory = self.get_config(
            "session_factory"
        )

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    @property
    def table_name(self) -> str:
        value = self.get_config(
            "table_name",
            self.DEFAULT_TABLE,
        )

        value = str(
            value or self.DEFAULT_TABLE
        ).strip()

        if not value:
            return self.DEFAULT_TABLE

        return value

    @property
    def embedding_dimension(self) -> int | None:
        value = self.get_config(
            "embedding_dimension"
        )

        if value is None:
            return None

        try:
            dimension = int(
                value
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ProviderConfigurationError(
                "embedding_dimension must be an integer."
            ) from exc

        if dimension <= 0:
            raise ProviderConfigurationError(
                "embedding_dimension must be greater than zero."
            )

        return dimension

    @property
    def distance(self) -> str:
        value = str(
            self.get_config(
                "distance",
                "cosine",
            )
        ).strip().lower()

        allowed = {
            "cosine",
            "l2",
            "euclidean",
            "ip",
            "inner_product",
        }

        if value not in allowed:
            raise ProviderConfigurationError(
                "Unsupported pgvector distance metric: "
                f"{value}. Supported values: "
                f"{sorted(allowed)}"
            )

        return value

    def validate_config(self) -> None:
        if not self.table_name:
            raise ProviderConfigurationError(
                "pgvector table_name cannot be empty."
            )

        if self.embedding_dimension is not None:
            if self.embedding_dimension <= 0:
                raise ProviderConfigurationError(
                    "embedding_dimension must be positive."
                )

    # ------------------------------------------------------------------
    # Capabilities
    # ------------------------------------------------------------------

    def capabilities(self) -> set[str]:
        capabilities = super().capabilities()

        capabilities.update(
            {
                "vector_indexing",
                "postgresql",
                "pgvector",
            }
        )

        return capabilities

    # ------------------------------------------------------------------
    # Dependency checks
    # ------------------------------------------------------------------

    def _load_sqlalchemy(self):
        try:
            import sqlalchemy
        except ImportError as exc:
            raise ProviderUnavailableError(
                "SQLAlchemy is not installed. "
                "Install it with: pip install sqlalchemy"
            ) from exc

        return sqlalchemy

    # ------------------------------------------------------------------
    # Session handling
    # ------------------------------------------------------------------

    def _get_session_factory(self) -> Any:
        factory = (
            self._session_factory
            or self.get_config(
                "session_factory"
            )
        )

        if factory is None:
            raise ProviderConfigurationError(
                "pgvector_indexer requires a "
                "'session_factory' configuration."
            )

        return factory

    async def _open_session(self) -> Any:
        factory = (
            self._get_session_factory()
        )

        session = factory()

        if hasattr(
            session,
            "__aenter__",
        ):
            return session

        return session

    async def _close_session(
        self,
        session: Any,
    ) -> None:
        if session is None:
            return

        close = getattr(
            session,
            "close",
            None,
        )

        if close is None:
            return

        result = close()

        if hasattr(
            result,
            "__await__",
        ):
            await result

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        try:
            self.validate_config()

            self._load_sqlalchemy()

            session = await self._open_session()

            try:
                sqlalchemy = (
                    self._load_sqlalchemy()
                )

                result = await session.execute(
                    sqlalchemy.text(
                        "SELECT 1"
                    )
                )

                # Consume the result so DB drivers execute it fully.
                result.scalar()

            finally:
                await self._close_session(
                    session
                )

            return True

        except Exception:
            logger.debug(
                "pgvector health check failed.",
                exc_info=True,
            )

            return False

    # ------------------------------------------------------------------
    # SQL helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _quote_identifier(
        identifier: str,
    ) -> str:
        """
        Safely quote a PostgreSQL identifier.

        Identifiers cannot be passed as normal SQL parameters, so we
        validate the expected identifier shape.
        """

        value = str(
            identifier
        ).strip()

        if not value:
            raise ValueError(
                "SQL identifier cannot be empty."
            )

        if not (
            value.replace(
                "_",
                "",
            ).isalnum()
        ):
            raise ValueError(
                f"Unsafe SQL identifier: {value!r}"
            )

        return f'"{value}"'

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    async def index(
        self,
        request: IndexingRequest,
    ) -> IndexingResult:
        """
        Index embeddings into PostgreSQL.

        The exact row schema can be supplied through configuration:

            insert_sql

        Example:

            {
                "insert_sql":
                    "INSERT INTO document_embeddings "
                    "(document_id, chunk_id, embedding, metadata) "
                    "VALUES (:document_id, :chunk_id, "
                    ":embedding, CAST(:metadata AS JSONB))"
            }

        This keeps the provider compatible with an application's
        existing database schema rather than assuming a particular ORM
        model.
        """

        request.validate()

        self.validate_config()

        sqlalchemy = self._load_sqlalchemy()

        session = await self._open_session()

        indexed_count = 0

        try:
            embeddings = getattr(
                request,
                "embeddings",
                None,
            )

            if embeddings is None:
                embeddings = getattr(
                    request,
                    "items",
                    None,
                )

            if embeddings is None:
                embeddings = []

            insert_sql = self.get_config(
                "insert_sql"
            )

            if not insert_sql:
                raise ProviderConfigurationError(
                    "pgvector_indexer requires 'insert_sql' "
                    "to be configured for indexing."
                )

            statement = sqlalchemy.text(
                str(insert_sql)
            )

            for item in embeddings:
                params = self._normalize_item(
                    item
                )

                await session.execute(
                    statement,
                    params,
                )

                indexed_count += 1

            commit = getattr(
                session,
                "commit",
                None,
            )

            if commit is not None:
                result = commit()

                if hasattr(
                    result,
                    "__await__",
                ):
                    await result

        except Exception:
            rollback = getattr(
                session,
                "rollback",
                None,
            )

            if rollback is not None:
                try:
                    result = rollback()

                    if hasattr(
                        result,
                        "__await__",
                    ):
                        await result

                except Exception:
                    logger.debug(
                        "pgvector rollback failed.",
                        exc_info=True,
                    )

            raise

        finally:
            await self._close_session(
                session
            )

        return IndexingResult(
            success=True,
            indexed_count=indexed_count,
            failed_count=0,
            metadata={
                "provider": self.name,
                "table_name": self.table_name,
                "distance": self.distance,
                "embedding_dimension": (
                    self.embedding_dimension
                ),
            },
            warnings=[],
        )

    # ------------------------------------------------------------------
    # Item normalization
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_item(
        item: Any,
    ) -> dict[str, Any]:
        if isinstance(
            item,
            Mapping,
        ):
            return dict(item)

        result: dict[str, Any] = {}

        for key in (
            "document_id",
            "chunk_id",
            "embedding",
            "metadata",
            "text",
            "vector",
        ):
            value = getattr(
                item,
                key,
                None,
            )

            if value is not None:
                result[key] = value

        if "embedding" not in result:
            if "vector" in result:
                result["embedding"] = (
                    result["vector"]
                )

        return result

    # ------------------------------------------------------------------
    # Extension verification
    # ------------------------------------------------------------------

    async def verify_vector_extension(
        self,
    ) -> bool:
        """
        Verify that PostgreSQL has pgvector installed.

        This is separate from health_check because a database can be
        reachable while the vector extension is unavailable.
        """

        sqlalchemy = self._load_sqlalchemy()

        session = await self._open_session()

        try:
            result = await session.execute(
                sqlalchemy.text(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM pg_extension
                        WHERE extname = 'vector'
                    )
                    """
                )
            )

            return bool(
                result.scalar()
            )

        except Exception:
            logger.debug(
                "Unable to verify pgvector extension.",
                exc_info=True,
            )

            return False

        finally:
            await self._close_session(
                session
            )

    # ------------------------------------------------------------------
    # Index creation
    # ------------------------------------------------------------------

    async def create_vector_index(
        self,
        *,
        index_name: str,
        column_name: str = "embedding",
        table_name: str | None = None,
        method: str = "hnsw",
    ) -> None:
        """
        Create a pgvector index.

        Supported methods:

            hnsw
            ivfflat

        Note:

            HNSW requires a PostgreSQL installation with a pgvector
            version that supports HNSW. If pgvector is absent, this
            operation will fail at the database layer.
        """

        method = str(
            method
        ).strip().lower()

        if method not in {
            "hnsw",
            "ivfflat",
        }:
            raise ValueError(
                "Vector index method must be 'hnsw' or 'ivfflat'."
            )

        index_identifier = (
            self._quote_identifier(
                index_name
            )
        )

        table_identifier = (
            self._quote_identifier(
                table_name
                or self.table_name
            )
        )

        column_identifier = (
            self._quote_identifier(
                column_name
            )
        )

        sqlalchemy = self._load_sqlalchemy()

        session = await self._open_session()

        try:
            sql = (
                f"CREATE INDEX IF NOT EXISTS "
                f"{index_identifier} "
                f"ON {table_identifier} "
                f"USING {method} "
                f"({column_identifier})"
            )

            await session.execute(
                sqlalchemy.text(
                    sql
                )
            )

            commit = getattr(
                session,
                "commit",
                None,
            )

            if commit is not None:
                result = commit()

                if hasattr(
                    result,
                    "__await__",
                ):
                    await result

        finally:
            await self._close_session(
                session
            )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def startup(self) -> None:
        self.validate_config()

        if self.get_config(
            "verify_database_on_startup",
            False,
        ):
            healthy = await self.health_check()

            if not healthy:
                raise ProviderUnavailableError(
                    "PostgreSQL is not available."
                )

    async def shutdown(self) -> None:
        # Database sessions are deliberately request-scoped.
        pass

