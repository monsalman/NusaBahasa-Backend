"""initial schema + pgvector extension

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-09

Catatan: untuk bootstrap cepat, migration ini mengaktifkan extension pgvector
lalu membuat seluruh tabel dari metadata model. Untuk perubahan skema berikutnya,
gunakan `alembic revision --autogenerate -m "..."` seperti biasa.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    from app.db import Base
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    from app.db import Base
    import app.models  # noqa: F401

    Base.metadata.drop_all(bind=op.get_bind())
