from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

class useradd(BaseModel):
    login: str = Field(min_length=3, max_length=64, description="Уникальный логин пользователя")
    password: str = Field(min_length=6, max_length=128, description="Пароль минимум 6 символов")
    email: EmailStr = Field(description="Email пользователя")

    @field_validator("login")
    @classmethod
    def validate_login(cls, v: str) -> str:
        if sum(1 for char in v if char.isalpha()) < 3:
            raise ValueError("Логин должен содержать как минимум 3 буквы")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(char.isupper() for char in v):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
        if not any(char.isdigit() for char in v):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        return v

class loginreq(BaseModel):
    login: str = Field(min_length=3, max_length=64, description="Логин")
    password: str = Field(min_length=6, max_length=128, description="Пароль")
    model_config = ConfigDict(json_schema_extra={"example": {"login": "tester", "password": "tester"}})

class useresp(BaseModel):
    id: int
    login: str
    email: str
    model_config = ConfigDict(from_attributes=True)

class tokenresp(BaseModel):
    access_token: str = Field(description="JWT-токен для заголовка Authorization")
    token_type: str = Field(default="bearer", description="Тип токена авторизации")

class msgresp(BaseModel):
    message: str = Field(description="Информационное сообщение")


