import os
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy import String, Integer, Text, BigInteger
from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# The Base class is a declarative base that is used to create all the models in the application.
class Base(DeclarativeBase):
    pass

# The User model represents the user data that will be stored in the database.
class User(SQLAlchemyBaseUserTableUUID, Base):
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    lms_security_key: Mapped[str] = mapped_column(String(255))
    moodle_user_id: Mapped[int] = mapped_column(Integer, nullable=True)

# The Resource model represents the resources that will be stored in the database.
class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(Integer, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    fileurl: Mapped[str] = mapped_column(Text, nullable=False)
    mimetype: Mapped[str] = mapped_column(String(100), nullable=True)
    time_modified: Mapped[int] = mapped_column(BigInteger, nullable=True)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)  # Path where the resource is stored locally


engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


# Purpose: This function sets up a user database interface using the session created by get_async_session.
# used in routes or other parts of your application that need to work specifically with user data, like logging in, registering, or updating a user's information.

async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)
