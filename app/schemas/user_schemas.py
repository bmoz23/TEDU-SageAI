import uuid
from typing import Optional

import fastapi_users


class UserBase(fastapi_users.schemas.BaseUser[uuid.UUID]):
    first_name: str
    last_name: str
    lms_security_key: str
    moodle_user_id: Optional[int]
    

class UserRead(UserBase):
    pass


class UserCreate(fastapi_users.schemas.BaseUserCreate, UserBase):
    pass


class UserUpdate(fastapi_users.schemas.BaseUserUpdate, UserBase):
    pass
