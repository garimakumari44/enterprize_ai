from typing import Literal

from pydantic import BaseModel


class Token(BaseModel):
    """
    Authentication response returned after
    successful login or registration.
    """

    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"


class RefreshTokenRequest(BaseModel):
    """
    Request schema for refreshing an access token.
    """

    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """
    Response after refreshing an access token.
    """

    access_token: str
    token_type: Literal["bearer"] = "bearer"


class TokenPayload(BaseModel):
    """
    Decoded JWT payload.
    """

    sub: str
    type: Literal["access", "refresh"]
    jti: str
    exp: int