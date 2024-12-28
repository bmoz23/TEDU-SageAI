import os
import uuid
from typing import Optional
from fastapi import Depends, Request, BackgroundTasks
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, models, InvalidPasswordException
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from .schemas.user_schemas import UserCreate
from .database.db import User, get_user_db
from fastapi import HTTPException, status
from .utils.lms_client import LMSClient
from dotenv import load_dotenv

load_dotenv()
SECRET = os.environ.get("SECRET", "")



class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET


    async def on_after_register(
            self, user: User, request: Optional[Request] = None, background_tasks: BackgroundTasks = None
    ):
        if not user.lms_security_key:
            raise HTTPException(
                status_code=400,
                detail="LMS security key is required to register."
            )

        # Fetch the Moodle user ID using LMSClient
        try:
            lms_client = LMSClient(user.lms_security_key)
            site_info = lms_client.call_api("core_webservice_get_site_info")
            moodle_user_id = site_info.get("userid")

            if not moodle_user_id:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to fetch Moodle user ID during registration."
                )

            # Update the user in the database
            user.moodle_user_id = moodle_user_id
            await self.user_db.update(
                user,  # Pass the user object
                update_dict={"moodle_user_id": moodle_user_id}
            )

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching Moodle user ID: {str(e)}"
            )





    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {
              user.id}. Verification token: {token}")

    async def validate_password(self, password: str, user: UserCreate | User) -> None:
        if len(password) < 8:
            raise InvalidPasswordException(
                reason="Password should be at least 8 characters"
            )
        if user.email in password:
            raise InvalidPasswordException(
                reason="Password should not contain e-mail"
            )


# provide an instance of UserManager, which is a custom class used to manage user-related operations in a FastAPI application that uses the FastAPI Users library.
async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


# listen for tokens at a specific endpoint (e.g., /auth/jwt/login) where users will log in and receive their tokens
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


#
def get_jwt_strategy() -> JWTStrategy[models.UP, models.ID]:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)


