"""NFT foundation tables and database enforcement; no operational seed data."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def created():
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        created(),
        sa.CheckConstraint(
            "email = lower(trim(email)) AND length(email) > 3", name="ck_users_email"
        ),
    )
    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("timezone", sa.String(100), nullable=False, server_default="America/Toronto"),
        sa.Column("mode", sa.String(10), nullable=False, server_default="REAL"),
        created(),
        sa.CheckConstraint("mode IN ('REAL','DEMO')", name="ck_organizations_mode"),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_organizations_name"),
    )
    op.create_table(
        "organization_members",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        created(),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_members_user"),
        sa.UniqueConstraint("organization_id", "id", name="uq_members_tenant_id"),
        sa.CheckConstraint(
            "role IN ('OWNER','ADMINISTRATOR','MANAGER','OPERATOR','VIEWER')",
            name="ck_members_role",
        ),
    )
    op.create_index("ix_members_user", "organization_members", ["user_id"])
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("actor_member_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(100), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        created(),
        sa.ForeignKeyConstraint(
            ["organization_id", "actor_member_id"],
            ["organization_members.organization_id", "organization_members.id"],
            name="fk_audit_actor_tenant",
        ),
    )
    op.create_index("ix_audit_org_time", "audit_logs", ["organization_id", "created_at"])
    for table, tenant_key in [
        ("organizations", "id"),
        ("organization_members", "organization_id"),
        ("audit_logs", "organization_id"),
    ]:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        predicate = f"{tenant_key} = NULLIF(current_setting('nft.organization_id', true), '')::uuid"
        op.execute(
            f"CREATE POLICY nft_tenant ON {table} USING ({predicate}) WITH CHECK ({predicate})"
        )
    op.execute("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON organizations, organization_members TO nft_runtime"
    )
    op.execute("GRANT SELECT, INSERT ON audit_logs TO nft_runtime")
    op.execute("GRANT SELECT ON alembic_version TO nft_runtime")
    op.execute(
        "CREATE FUNCTION nft_prevent_audit_change() RETURNS trigger "
        "LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'Audit records are "
        "append-only'; END; $$"
    )
    op.execute(
        "CREATE TRIGGER nft_audit_immutable BEFORE UPDATE OR DELETE ON "
        "audit_logs FOR EACH ROW EXECUTE FUNCTION "
        "nft_prevent_audit_change()"
    )
    op.execute(
        "CREATE FUNCTION nft_prevent_mode_change() RETURNS trigger "
        "LANGUAGE plpgsql AS $$ BEGIN IF NEW.mode <> OLD.mode THEN RAISE "
        "EXCEPTION 'Organization data mode is immutable'; END IF; RETURN "
        "NEW; END; $$"
    )
    op.execute(
        "CREATE TRIGGER nft_mode_immutable BEFORE UPDATE ON organizations "
        "FOR EACH ROW EXECUTE FUNCTION nft_prevent_mode_change()"
    )


def downgrade():
    op.drop_table("audit_logs")
    op.drop_table("organization_members")
    op.drop_table("organizations")
    op.drop_table("users")
    op.execute("DROP FUNCTION nft_prevent_audit_change()")
    op.execute("DROP FUNCTION nft_prevent_mode_change()")
