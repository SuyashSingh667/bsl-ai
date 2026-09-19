"""
Role-Based Access Control (RBAC) for BSL AI Platform.
Enforces multi-tier permissions across frontline workers, supervisors,
safety officers, control room dispatchers, and plant administrators.
"""

from __future__ import annotations

from enum import Enum
from typing import Callable

from fastapi import Depends, Header, HTTPException, status


class UserRole(str, Enum):
    WORKER = "worker"
    SUPERVISOR = "supervisor"
    SAFETY_OFFICER = "safety_officer"
    CONTROL_ROOM = "control_room"
    ADMIN = "admin"


# Hierarchy and permissions matrix
ROLE_HIERARCHY: dict[UserRole, int] = {
    UserRole.WORKER: 1,
    UserRole.SUPERVISOR: 2,
    UserRole.SAFETY_OFFICER: 3,
    UserRole.CONTROL_ROOM: 3,
    UserRole.ADMIN: 4,
}

PERMISSIONS: dict[str, list[UserRole]] = {
    "incident:create": [UserRole.WORKER, UserRole.SUPERVISOR, UserRole.SAFETY_OFFICER, UserRole.CONTROL_ROOM, UserRole.ADMIN],
    "incident:proxy_report": [UserRole.SUPERVISOR, UserRole.SAFETY_OFFICER, UserRole.ADMIN],
    "incident:read": [UserRole.WORKER, UserRole.SUPERVISOR, UserRole.SAFETY_OFFICER, UserRole.CONTROL_ROOM, UserRole.ADMIN],
    "incident:triage_override": [UserRole.SAFETY_OFFICER, UserRole.CONTROL_ROOM, UserRole.ADMIN],
    "incident:resolve": [UserRole.SAFETY_OFFICER, UserRole.ADMIN],
    "audit:read": [UserRole.SAFETY_OFFICER, UserRole.CONTROL_ROOM, UserRole.ADMIN],
    "plant:configure": [UserRole.ADMIN],
    "sop:upload": [UserRole.SAFETY_OFFICER, UserRole.ADMIN],
    "integration:manage": [UserRole.ADMIN],
    "data:export": [UserRole.SAFETY_OFFICER, UserRole.CONTROL_ROOM, UserRole.ADMIN],
    "data:retention_prune": [UserRole.ADMIN],
}


class AuthContext:
    def __init__(
        self,
        user_id: str,
        role: UserRole,
        plant_id: str,
    ):
        self.user_id = user_id
        self.role = role
        self.plant_id = plant_id

    def has_permission(self, permission: str) -> bool:
        allowed_roles = PERMISSIONS.get(permission, [])
        return self.role in allowed_roles

    def require_permission(self, permission: str) -> None:
        if not self.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{self.role.value}' lacks required permission '{permission}'",
            )


def get_current_auth(
    x_user_id: str | None = Header(default=None),
    x_user_role: str | None = Header(default=None),
    x_plant_id: str | None = Header(default=None),
) -> AuthContext:
    """Extracts auth context from HTTP headers with sensible plant floor defaults."""
    user_id = x_user_id or "ANON_WORKER"
    role_str = (x_user_role or "worker").lower()
    plant_id = x_plant_id or "bsl_bokaro"

    try:
        role = UserRole(role_str)
    except ValueError:
        role = UserRole.WORKER

    return AuthContext(user_id=user_id, role=role, plant_id=plant_id)


def require_role(*allowed_roles: UserRole) -> Callable:
    """Dependency factory checking that the caller holds one of the required roles."""
    def _dependency(auth: AuthContext = Depends(get_current_auth)) -> AuthContext:
        if auth.role not in allowed_roles and auth.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied for role '{auth.role.value}'. Requires {[r.value for r in allowed_roles]}",
            )
        return auth
    return _dependency
