from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as connection:
    tables = connection.execute(
        text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name IN (
                  'document_chunks',
                  'embeddings',
                  'document_chunk_vectors'
              )
            ORDER BY table_name
        """)
    ).fetchall()

    print("\nTABLES:")
    for row in tables:
        print(row)

    columns = connection.execute(
        text("""
            SELECT
                table_name,
                column_name,
                data_type,
                udt_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name IN (
                  'document_chunks',
                  'embeddings',
                  'document_chunk_vectors'
              )
            ORDER BY table_name, ordinal_position
        """)
    ).fetchall()

    print("\nCOLUMNS:")
    for row in columns:
        print(row)
