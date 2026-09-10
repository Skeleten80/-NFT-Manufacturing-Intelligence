"""Internal policy primitives. No client claims or session authentication here."""

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class Permission(StrEnum):
    READ_OPERATIONS = "operations:read"
    RECORD_PRODUCTION = "production:record"
    MANAGE_OPERATIONS = "operations:manage"
    MANAGE_MEMBERS = "members:manage"
    MANAGE_ORGANIZATION = "organization:manage"


class Role(StrEnum):
    OWNER = "OWNER"
    ADMINISTRATOR = "ADMINISTRATOR"
    MANAGER = "MANAGER"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"


PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.VIEWER: frozenset({Permission.READ_OPERATIONS}),
    Role.OPERATOR: frozenset({Permission.READ_OPERATIONS, Permission.RECORD_PRODUCTION}),
    Role.MANAGER: frozenset(
        {Permission.READ_OPERATIONS, Permission.RECORD_PRODUCTION, Permission.MANAGE_OPERATIONS}
    ),
    Role.ADMINISTRATOR: frozenset(
        {
            Permission.READ_OPERATIONS,
            Permission.RECORD_PRODUCTION,
            Permission.MANAGE_OPERATIONS,
            Permission.MANAGE_MEMBERS,
        }
    ),
    Role.OWNER: frozenset(Permission),
}


@dataclass(frozen=True)
class AuthorizedContext:
    """Construct only after server-side session/membership checks in Phase 1."""

    user_id: UUID
    organization_id: UUID
    role: Role

    def require(self, permission: Permission) -> None:
        if permission not in PERMISSIONS.get(self.role, frozenset()):
            raise PermissionError("Permission denied")
