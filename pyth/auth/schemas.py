from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserCreate(BaseModel):
    login: str = Field(min_length=3, max_length=64, description="Уникальный логин пользователя")
    password: str = Field(min_length=8, max_length=128, description="Пароль минимум 8 символов")
    email: EmailStr = Field(description="Email пользователя")

class LoginRequest(BaseModel):
    login: str = Field(min_length=3, max_length=64, description="Логин зарегистрированного пользователя")
    password: str = Field(min_length=8, max_length=128, description="Пароль пользователя")

class UserResponse(BaseModel):
    id: int
    login: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str = Field(description="JWT-токен для заголовка Authorization")
    token_type: str = Field(default="bearer", description="Тип токена авторизации")
