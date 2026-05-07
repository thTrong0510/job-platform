# app/models/db_types.py
"""
SQLite không hỗ trợ tốt BigInteger autoincrement + RETURNING clause.
BigIntegerPK tự động dùng Integer trên SQLite và BigInteger trên MySQL/PostgreSQL.
"""
from sqlalchemy import BigInteger, Integer
from sqlalchemy.types import TypeDecorator
import sqlalchemy.dialects.sqlite as sqlite_dialect


class BigIntegerPK(TypeDecorator):
    """
    Primary key type tương thích cả MySQL (BIGINT) lẫn SQLite (INTEGER).
    SQLite yêu cầu PK là INTEGER (không phải BIGINT) để autoincrement hoạt động đúng.
    """
    impl = BigInteger
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(Integer())
        return dialect.type_descriptor(BigInteger())