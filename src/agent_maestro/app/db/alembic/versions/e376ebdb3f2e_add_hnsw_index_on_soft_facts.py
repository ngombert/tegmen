"""add_hnsw_index_on_soft_facts

Revision ID: e376ebdb3f2e
Revises: 2d9490624fda
Create Date: 2026-06-09 00:39:39.344899

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e376ebdb3f2e'
down_revision: Union[str, Sequence[str], None] = '2d9490624fda'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        "idx_soft_facts_embedding_hnsw",
        "soft_facts",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"}
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_soft_facts_embedding_hnsw", table_name="soft_facts")
