"""Initial schema: shelters, users (staff/adopter), animals, applications.

Revision ID: 0001
Revises: -
Create Date: 2026-10-23 13:19:23.344536

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('shelters',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('city', sa.String(length=120), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('animals',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('species', sa.String(length=80), nullable=False),
    sa.Column('breed', sa.String(length=120), nullable=False),
    sa.Column('age', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('available', 'pending', 'adopted', name='animal_status', native_enum=False, create_constraint=True), nullable=False),
    sa.Column('shelter_id', sa.Integer(), nullable=False),
    sa.Column('photo_path', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint('age >= 0', name='ck_animals_age_non_negative'),
    sa.ForeignKeyConstraint(['shelter_id'], ['shelters.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('animals', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_animals_shelter_id'), ['shelter_id'], unique=False)

    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('hashed_password', sa.String(length=255), nullable=False),
    sa.Column('role', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('shelter_id', sa.Integer(), nullable=True),
    sa.CheckConstraint("role IN ('adopter', 'staff')", name='ck_users_role'),
    sa.ForeignKeyConstraint(['shelter_id'], ['shelters.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_users_email'), ['email'], unique=True)
        batch_op.create_index(batch_op.f('ix_users_role'), ['role'], unique=False)

    op.create_table('shelter_applications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('adopter_id', sa.Integer(), nullable=False),
    sa.Column('animal_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('pending', 'approved', 'rejected', name='application_status', native_enum=False, create_constraint=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['adopter_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['animal_id'], ['animals.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('shelter_applications', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_shelter_applications_adopter_id'), ['adopter_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_shelter_applications_animal_id'), ['animal_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('shelter_applications', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_shelter_applications_animal_id'))
        batch_op.drop_index(batch_op.f('ix_shelter_applications_adopter_id'))

    op.drop_table('shelter_applications')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_role'))
        batch_op.drop_index(batch_op.f('ix_users_email'))

    op.drop_table('users')
    with op.batch_alter_table('animals', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_animals_shelter_id'))

    op.drop_table('animals')
    op.drop_table('shelters')
