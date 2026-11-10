from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class CustomerCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=32)

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_names(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Поле не может быть пустым")
        return value


class TokenRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    customer_id: str


class CustomerPatch(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=32)

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_optional_names(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Поле не может быть пустым")
        return value


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    customer_id: str
    email: EmailStr
    first_name: str
    last_name: str
    phone: str | None
    account_status: str
    registered_at: datetime
    updated_at: datetime | None
    profile_version: int


class CustomerPatchResponse(CustomerResponse):
    changed_fields: list[str]
