"""
PEVN Backend — Institutional News API Endpoints (Phase 15 - DECISION-15-03)

REST Controller for school life highlights, community events, and academic projects.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import (
    AuthContextDep,
    ClientIpDep,
    CurrentUserDep,
    SessionDep,
    require_permission,
)
from app.core.logging import correlation_id_ctx
from app.core.security.interfaces import SystemRole
from app.exceptions.errors import AuthorizationError
from app.models.communication import PublishingStatus
from app.models.news import NewsCategory
from app.schemas.news import (
    InstitutionalNewsResponse,
    NewsCreateRequest,
    NewsListResponse,
    NewsUpdateRequest,
)
from app.services.news_service import NewsService

router = APIRouter(prefix="/news", tags=["News"])


def _resolve_institution_id(
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id_override: uuid.UUID | None = None,
) -> uuid.UUID:
    if (
        SystemRole.SUPERADMIN in auth.roles
        or SystemRole.NATIONAL_ADMIN in auth.roles
        or auth.scope.is_national()
    ) and institution_id_override:
        return institution_id_override
    if current_user.institution_id:
        return current_user.institution_id
    raise AuthorizationError("Contexto institucional no disponible.")


@router.post(
    "",
    response_model=InstitutionalNewsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear noticia institucional",
    description="Redacta y publica una novedad de vida escolar o logro formativo.",
    dependencies=[Depends(require_permission("news", "create"))],
)
async def create_news(
    payload: NewsCreateRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> InstitutionalNewsResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = NewsService(session=db)
    news = await service.create_news(
        institution_id=target_institution_id,
        author_user_id=current_user.id,
        payload=payload,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    return InstitutionalNewsResponse.model_validate(news)


@router.get(
    "/{news_id}",
    response_model=InstitutionalNewsResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar noticia institucional",
    dependencies=[Depends(require_permission("news", "read"))],
)
async def get_news(
    news_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> InstitutionalNewsResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    service = NewsService(session=db)
    news = await service.get_news_by_id(news_id=news_id, institution_id=target_institution_id)
    return InstitutionalNewsResponse.model_validate(news)


@router.put(
    "/{news_id}",
    response_model=InstitutionalNewsResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar noticia",
    dependencies=[Depends(require_permission("news", "update"))],
)
async def update_news(
    news_id: uuid.UUID,
    payload: NewsUpdateRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> InstitutionalNewsResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = NewsService(session=db)
    news = await service.update_news(
        news_id=news_id,
        institution_id=target_institution_id,
        payload=payload,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    return InstitutionalNewsResponse.model_validate(news)


@router.post(
    "/{news_id}/publish",
    response_model=InstitutionalNewsResponse,
    status_code=status.HTTP_200_OK,
    summary="Publicar noticia",
    dependencies=[Depends(require_permission("news", "publish"))],
)
async def publish_news(
    news_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> InstitutionalNewsResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = NewsService(session=db)
    news = await service.publish_news(
        news_id=news_id,
        institution_id=target_institution_id,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    return InstitutionalNewsResponse.model_validate(news)


@router.get(
    "",
    response_model=NewsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar noticias institucionales",
    dependencies=[Depends(require_permission("news", "read"))],
)
async def list_news(
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    category: Annotated[NewsCategory | None, Query()] = None,
    status_filter: Annotated[PublishingStatus | None, Query(alias="status")] = PublishingStatus.PUBLICADO,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> NewsListResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    service = NewsService(session=db)
    items = await service.list_news(
        institution_id=target_institution_id,
        category=category,
        status=status_filter,
    )
    return NewsListResponse(
        items=[InstitutionalNewsResponse.model_validate(n) for n in items],
        total=len(items),
    )
