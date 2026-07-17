from sqlalchemy.dialects import postgresql

from app.enums.roles import UserRole
from app.models.users import User


def test_user_role_column_binds_to_postgres_values() -> None:
    role_column = User.__table__.c.role.type
    processor = role_column.bind_processor(postgresql.dialect())

    assert processor(UserRole.MEMBER) == "member"
    assert processor(UserRole.ADMIN) == "admin"
    assert processor(UserRole.OWNER) == "owner"
