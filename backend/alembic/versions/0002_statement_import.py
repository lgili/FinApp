"""add statement import fields

Revision ID: 0002_statement_import
Revises: 0001_initial
Create Date: 2025-10-12 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0002_statement_import'
down_revision: Union[str, None] = '0001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # For SQLite, we'll use simple ALTER TABLE ADD COLUMN
    # This is simpler and avoids issues with batch operations
    
    # Add columns to import_batches (already has: id, source, external_id, file_sha256, imported_at, metadata)
    op.add_column('import_batches', sa.Column('filename', sa.String(length=255), nullable=True))
    op.add_column('import_batches', sa.Column('transaction_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('import_batches', sa.Column('error_message', sa.Text(), nullable=True))
    op.add_column('import_batches', sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'))
    op.add_column('import_batches', sa.Column('completed_at', sa.DateTime(), nullable=True))
    op.add_column('import_batches', sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('import_batches', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    
    # Create indexes for import_batches
    op.create_index('ix_import_batches_file_sha256', 'import_batches', ['file_sha256'], unique=False)
    op.create_index('ix_import_batches_status', 'import_batches', ['status'], unique=False)

    # Add columns to statement_entries (already has: id, batch_id, external_id, payee, memo, amount, currency, occurred_at, status, suggested_account_id, metadata)
    op.add_column('statement_entries', sa.Column('transaction_id', sa.Integer(), nullable=True))
    op.add_column('statement_entries', sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('statement_entries', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    
    # Create indexes for statement_entries
    op.create_index('ix_statement_entries_status', 'statement_entries', ['status'], unique=False)
    op.create_index('ix_statement_entries_occurred_at', 'statement_entries', ['occurred_at'], unique=False)
    op.create_index('ix_statement_entries_transaction_id', 'statement_entries', ['transaction_id'], unique=False)
    
    # Note: We're NOT renaming metadata to extra_metadata or imported_at to started_at
    # to keep backwards compatibility. The mapper will handle the name mapping.


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_statement_entries_transaction_id', table_name='statement_entries')
    op.drop_index('ix_statement_entries_occurred_at', table_name='statement_entries')
    op.drop_index('ix_statement_entries_status', table_name='statement_entries')
    
    # Drop columns from statement_entries
    # Note: SQLite doesn't support DROP COLUMN before version 3.35.0
    # For older versions, we'd need to recreate the table
    # For now, we'll just leave the columns (they'll be ignored)
    # In production, you'd want to handle this more carefully
    with op.batch_alter_table('statement_entries', schema=None) as batch_op:
        batch_op.drop_column('updated_at')
        batch_op.drop_column('created_at')
        batch_op.drop_column('transaction_id')
    
    # Drop indexes from import_batches
    op.drop_index('ix_import_batches_status', table_name='import_batches')
    op.drop_index('ix_import_batches_file_sha256', table_name='import_batches')
    
    # Drop columns from import_batches
    with op.batch_alter_table('import_batches', schema=None) as batch_op:
        batch_op.drop_column('updated_at')
        batch_op.drop_column('created_at')
        batch_op.drop_column('completed_at')
        batch_op.drop_column('status')
        batch_op.drop_column('error_message')
        batch_op.drop_column('transaction_count')
        batch_op.drop_column('filename')
