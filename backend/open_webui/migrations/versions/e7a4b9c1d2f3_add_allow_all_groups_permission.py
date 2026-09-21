"""add access_grants.allow_all_groups user permission

Revision ID: e7a4b9c1d2f3
Revises: d4c1a8e37b62
Create Date: 2026-09-21 10:00:00.000000

Adds the ``access_grants.allow_all_groups`` permission, which decides whether a
user may grant access to every group or only to the groups they belong to.

Existing deployments could always share with any group, so every group that
stores permissions - and the stored default user permissions - are pinned to
``True`` here. Without that, flipping the shipped default to ``False`` later
would silently tighten groups that never opted in.
"""

import json
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e7a4b9c1d2f3'
down_revision: str | None = 'd4c1a8e37b62'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


PERMISSION_KEY = 'allow_all_groups'

_group = sa.table(
    'group',
    sa.column('id', sa.Text),
    sa.column('permissions', sa.JSON),
)

_config = sa.table(
    'config',
    sa.column('key', sa.Text),
    sa.column('value', sa.JSON),
)


def _as_dict(value):
    """JSON columns come back as dicts on some drivers and as strings on others."""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except Exception:
            return None
    return value if isinstance(value, dict) else None


def _apply(permissions: dict, value: bool | None) -> dict | None:
    """Set (bool) or drop (None) the permission. Returns None when nothing needs writing."""
    access_grants = permissions.get('access_grants')
    if not isinstance(access_grants, dict):
        access_grants = {}

    if value is None:
        if PERMISSION_KEY not in access_grants:
            return None
        access_grants = {k: v for k, v in access_grants.items() if k != PERMISSION_KEY}
        if not access_grants:
            return {k: v for k, v in permissions.items() if k != 'access_grants'}
    else:
        if access_grants.get(PERMISSION_KEY) == value:
            return None
        access_grants = {**access_grants, PERMISSION_KEY: value}

    return {**permissions, 'access_grants': access_grants}


def _migrate_group_permissions(conn, value: bool | None) -> None:
    rows = conn.execute(sa.select(_group.c.id, _group.c.permissions).where(_group.c.permissions.is_not(None)))
    for group_id, permissions in rows.fetchall():
        permissions = _as_dict(permissions)
        if permissions is None:
            continue
        updated = _apply(permissions, value)
        if updated is None:
            continue
        conn.execute(sa.update(_group).where(_group.c.id == group_id).values(permissions=updated))


def _migrate_default_permissions(conn, value: bool | None) -> None:
    row = conn.execute(sa.select(_config.c.value).where(_config.c.key == 'user.permissions')).fetchone()
    if row is None:
        return
    permissions = _as_dict(row[0])
    if permissions is None:
        return
    updated = _apply(permissions, value)
    if updated is None:
        return
    conn.execute(sa.update(_config).where(_config.c.key == 'user.permissions').values(value=updated))


def _set_permission(value: bool | None) -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = set(inspector.get_table_names())

    if 'group' in tables and 'permissions' in {c['name'] for c in inspector.get_columns('group')}:
        _migrate_group_permissions(conn, value)

    # Pre-reshape config tables held a single JSON blob; there the runtime backfills the default.
    if 'config' in tables and {'key', 'value'}.issubset({c['name'] for c in inspector.get_columns('config')}):
        _migrate_default_permissions(conn, value)


def upgrade() -> None:
    # True == what every existing deployment does today: share with any group.
    _set_permission(True)


def downgrade() -> None:
    _set_permission(None)
