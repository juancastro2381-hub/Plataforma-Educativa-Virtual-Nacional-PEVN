"""
PEVN Backend — Authentication API Endpoints

Handles login, token rotation, logout, password recovery, and user profile inspection.

SECURITY:
  - Refresh tokens delivered via HttpOnly, SameSite=Strict cookies
  - Access tokens short-lived (15 minutes)
  - Account enumeration defense on password reset
  - Full audit logging of all authentication events
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Cookie, Header, Request, Response, status

from app.api.deps import (
    ClientIpDep,
    CurrentUserDep,
    SessionDep,
    SettingsDep,
)
from app.exceptions.errors import AuthenticationError
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    PasswordChangeRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    TokenRefreshResponse,
    UserMeResponse,
)
from app.schemas.invitation import (
    AcceptInvitationRequest,
    AcceptInvitationResponse,
    VerifyInvitationRequest,
    VerifyInvitationResponse,
)
from app.services.auth_service import auth_service
from app.services.rector_onboarding_service import RectorOnboardingService

router = APIRouter(prefix="/auth", tags=["Authentication"])

REFRESH_COOKIE_NAME = "pevn_refresh_token"
REFRESH_COOKIE_PATH = "/api/v1/auth"
REFRESH_MAX_AGE_SECONDS = 7 * 24 * 60 * 60  # 7 days


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión",
    description=(
        "Autentica las credenciales del usuario, emite un access token JWT y "
        "establece una cookie HttpOnly con el refresh token."
    ),
)
async def login(
    credentials: LoginRequest,
    request: Request,
    response: Response,
    db: SessionDep,
    settings: SettingsDep,
    client_ip: ClientIpDep,
    user_agent: Annotated[str | None, Header()] = None,
) -> LoginResponse:
    correlation_id = getattr(request.state, "correlation_id", None)

    user, access_token, raw_refresh_token = await auth_service.authenticate_user(
        db=db,
        username_or_email=credentials.username,
        password=credentials.password,
        client_ip=client_ip,
        user_agent=user_agent,
        correlation_id=correlation_id,
    )

    # Set Secure HttpOnly cookie for the rotating refresh token
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_refresh_token,
        max_age=REFRESH_MAX_AGE_SECONDS,
        httponly=True,
        secure=settings.is_production,
        samesite="strict",
        path=REFRESH_COOKIE_PATH,
    )

    user_response = auth_service.build_user_me_response(user)
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",  # noqa: S106
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_response,
    )


@router.post(
    "/refresh",
    response_model=TokenRefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotar token de sesión",
    description=(
        "Lee el refresh token desde la cookie HttpOnly, rota la familia de tokens "
        "y emite un nuevo access token."
    ),
)
async def refresh_token(
    request: Request,
    response: Response,
    db: SessionDep,
    settings: SettingsDep,
    client_ip: ClientIpDep,
    pevn_refresh_token: Annotated[str | None, Cookie()] = None,
    x_refresh_token: Annotated[str | None, Header()] = None,
    user_agent: Annotated[str | None, Header()] = None,
) -> TokenRefreshResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    raw_token = pevn_refresh_token or x_refresh_token

    if not raw_token:
        raise AuthenticationError("Refresh token ausente en la solicitud.")

    _user, new_access_token, new_raw_refresh_token = (
        await auth_service.rotate_refresh_token(
            db=db,
            raw_refresh_token=raw_token,
            client_ip=client_ip,
            user_agent=user_agent,
            correlation_id=correlation_id,
        )
    )

    # Update HttpOnly cookie with the newly rotated refresh token
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=new_raw_refresh_token,
        max_age=REFRESH_MAX_AGE_SECONDS,
        httponly=True,
        secure=settings.is_production,
        samesite="strict",
        path=REFRESH_COOKIE_PATH,
    )

    return TokenRefreshResponse(
        access_token=new_access_token,
        token_type="bearer",  # noqa: S106
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Cerrar sesión",
    description=(
        "Revoca la familia de refresh tokens activa y elimina la cookie de sesión."
    ),
)
async def logout(
    request: Request,
    response: Response,
    db: SessionDep,
    client_ip: ClientIpDep,
    pevn_refresh_token: Annotated[str | None, Cookie()] = None,
    x_refresh_token: Annotated[str | None, Header()] = None,
) -> dict[str, str]:
    correlation_id = getattr(request.state, "correlation_id", None)
    raw_token = pevn_refresh_token or x_refresh_token

    if raw_token:
        await auth_service.revoke_refresh_token(
            db=db,
            raw_refresh_token=raw_token,
            client_ip=client_ip,
            correlation_id=correlation_id,
        )

    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
    )
    return {"message": "Sesión cerrada correctamente."}


@router.post(
    "/password/change",
    status_code=status.HTTP_200_OK,
    summary="Cambiar contraseña",
    description=(
        "Permite a un usuario autenticado actualizar su contraseña tras "
        "verificar su contraseña actual."
    ),
)
async def change_password(
    payload: PasswordChangeRequest,
    current_user: CurrentUserDep,
    request: Request,
    response: Response,
    db: SessionDep,
    client_ip: ClientIpDep,
) -> dict[str, str]:
    correlation_id = getattr(request.state, "correlation_id", None)

    await auth_service.change_password(
        db=db,
        user=current_user,
        current_password=payload.current_password,
        new_password=payload.new_password,
        client_ip=client_ip,
        correlation_id=correlation_id,
    )

    # Invalidate session cookie on password change
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
    )
    return {
        "message": (
            "Contraseña actualizada exitosamente. " "Inicie sesión con su nueva clave."
        )
    }


@router.post(
    "/password/reset/request",
    status_code=status.HTTP_200_OK,
    summary="Solicitar recuperación de contraseña",
    description=(
        "Inicia el flujo de recuperación de contraseña generando un token "
        "de uso único con respuesta en tiempo constante."
    ),
)
async def request_password_reset(
    payload: PasswordResetRequest,
    request: Request,
    db: SessionDep,
    client_ip: ClientIpDep,
) -> dict[str, str]:
    correlation_id = getattr(request.state, "correlation_id", None)

    await auth_service.request_password_reset(
        db=db,
        email=payload.email,
        client_ip=client_ip,
        correlation_id=correlation_id,
    )

    # Generic constant response to prevent account enumeration
    return {
        "message": (
            "Si la dirección de correo electrónico se encuentra registrada, "
            "se han enviado las instrucciones de recuperación."
        )
    }


@router.post(
    "/password/reset/confirm",
    status_code=status.HTTP_200_OK,
    summary="Confirmar restablecimiento de contraseña",
    description=(
        "Completa el restablecimiento de contraseña utilizando un "
        "token de un solo uso."
    ),
)
async def confirm_password_reset(
    payload: PasswordResetConfirmRequest,
    request: Request,
    db: SessionDep,
    client_ip: ClientIpDep,
) -> dict[str, str]:
    correlation_id = getattr(request.state, "correlation_id", None)

    await auth_service.confirm_password_reset(
        db=db,
        raw_reset_token=payload.token,
        new_password=payload.new_password,
        client_ip=client_ip,
        correlation_id=correlation_id,
    )
    return {
        "message": (
            "Contraseña restablecida satisfactoriamente. "
            "Puede iniciar sesión con su nueva clave."
        )
    }


@router.get(
    "/me",
    response_model=UserMeResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener perfil del usuario autenticado",
    description=(
        "Devuelve la información de identidad, roles asignados, permisos y "
        "alcance organizacional del usuario en sesión."
    ),
)
async def get_my_profile(
    current_user: CurrentUserDep,
) -> UserMeResponse:
    return auth_service.build_user_me_response(current_user)


@router.post(
    "/verify-invitation",
    response_model=VerifyInvitationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validar token de invitación de Rector",
    description="Valida si el token recibido en el enlace de invitación es válido y no ha expirado.",
)
async def verify_invitation_endpoint(
    payload: VerifyInvitationRequest,
    db: SessionDep,
) -> VerifyInvitationResponse:
    onboarding_service = RectorOnboardingService(session=db)
    result = await onboarding_service.verify_invitation(token=payload.token)
    return VerifyInvitationResponse(**result)


@router.post(
    "/accept-invitation",
    response_model=AcceptInvitationResponse,
    status_code=status.HTTP_200_OK,
    summary="Aceptar invitación y definir contraseña de Rector",
    description="Canjea el token de un solo uso, establece la contraseña con Argon2id y activa la cuenta.",
)
async def accept_invitation_endpoint(
    payload: AcceptInvitationRequest,
    db: SessionDep,
    request: Request,
    client_ip: ClientIpDep,
) -> AcceptInvitationResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    onboarding_service = RectorOnboardingService(session=db)
    user = await onboarding_service.accept_invitation(
        token=payload.token,
        password=payload.password,
        password_confirmation=payload.password_confirmation,
        client_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()

    return AcceptInvitationResponse(
        message="Onboarding completado exitosamente. La cuenta ha sido activada y vinculada a la institución.",
        user_id=user.id,
        email=user.email,
        is_active=user.is_active,
    )

