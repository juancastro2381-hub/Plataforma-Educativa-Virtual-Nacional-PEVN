"""
PEVN Backend — Institutional News Domain Service (Phase 15 - DECISION-15-03)

Authoritative business logic for school highlights, cultural events, student achievements,
and institutional community news.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.interfaces import AuditEvent, AuditEventType, IAuditService
from app.audit.service import audit_service
from app.core.logging import get_logger
from app.exceptions.errors import NotFoundError
from app.models.communication import PublishingStatus
from app.models.news import InstitutionalNews, NewsCategory

if TYPE_CHECKING:
    from app.schemas.news import NewsCreateRequest, NewsUpdateRequest

_logger = get_logger(__name__)


class NewsService:
    """
    Domain service for Institutional News and Community Content.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit: IAuditService = audit_service,
    ) -> None:
        self._session = session
        self._audit = audit

    async def create_news(
        self,
        *,
        institution_id: uuid.UUID,
        author_user_id: uuid.UUID,
        payload: NewsCreateRequest,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> InstitutionalNews:
        """
        Create a new institutional news item.
        """
        published_at = datetime.now(UTC) if payload.status == PublishingStatus.PUBLICADO else None

        news = InstitutionalNews(
            institution_id=institution_id,
            author_user_id=author_user_id,
            title=payload.title.strip(),
            summary=payload.summary.strip(),
            content=payload.content.strip(),
            category=payload.category,
            cover_image_url=payload.cover_image_url.strip() if payload.cover_image_url else None,
            status=payload.status,
            published_at=published_at,
        )
        self._session.add(news)
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.NEWS_CREATED,
                actor_id=str(author_user_id),
                actor_ip=actor_ip,
                target_id=str(news.id),
                target_type="InstitutionalNews",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={
                    "title": news.title,
                    "category": news.category.value,
                    "status": news.status.value,
                },
            ),
            session=self._session,
        )

        return await self.get_news_by_id(news_id=news.id, institution_id=institution_id)

    async def update_news(
        self,
        *,
        news_id: uuid.UUID,
        institution_id: uuid.UUID,
        payload: NewsUpdateRequest,
        actor_id: uuid.UUID,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> InstitutionalNews:
        """
        Modify existing news item fields.
        """
        news = await self.get_news_by_id(news_id=news_id, institution_id=institution_id)

        if payload.title is not None:
            news.title = payload.title.strip()
        if payload.summary is not None:
            news.summary = payload.summary.strip()
        if payload.content is not None:
            news.content = payload.content.strip()
        if payload.category is not None:
            news.category = payload.category
        if payload.cover_image_url is not None:
            news.cover_image_url = payload.cover_image_url.strip() if payload.cover_image_url else None
        if payload.status is not None:
            news.status = payload.status
            if payload.status == PublishingStatus.PUBLICADO and news.published_at is None:
                news.published_at = datetime.now(UTC)

        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.NEWS_UPDATED,
                actor_id=str(actor_id),
                actor_ip=actor_ip,
                target_id=str(news.id),
                target_type="InstitutionalNews",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
            ),
            session=self._session,
        )

        return news

    async def publish_news(
        self,
        *,
        news_id: uuid.UUID,
        institution_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> InstitutionalNews:
        """
        Publish news item.
        """
        news = await self.get_news_by_id(news_id=news_id, institution_id=institution_id)
        news.status = PublishingStatus.PUBLICADO
        news.published_at = datetime.now(UTC)
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.NEWS_PUBLISHED,
                actor_id=str(actor_id),
                actor_ip=actor_ip,
                target_id=str(news.id),
                target_type="InstitutionalNews",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
            ),
            session=self._session,
        )
        return news

    async def get_news_by_id(
        self,
        *,
        news_id: uuid.UUID,
        institution_id: uuid.UUID,
    ) -> InstitutionalNews:
        """
        Retrieve news item validating tenant boundary (Anti-IDOR).
        """
        stmt = (
            select(InstitutionalNews)
            .options(selectinload(InstitutionalNews.author))
            .where(
                InstitutionalNews.id == news_id,
                InstitutionalNews.institution_id == institution_id,
            )
        )
        news = (await self._session.execute(stmt)).scalar_one_or_none()
        if not news:
            raise NotFoundError("Noticia institucional no encontrada.")
        return news

    async def list_news(
        self,
        *,
        institution_id: uuid.UUID,
        category: NewsCategory | None = None,
        status: PublishingStatus | None = PublishingStatus.PUBLICADO,
    ) -> list[InstitutionalNews]:
        """
        List news items for the educational institution.
        """
        query = (
            select(InstitutionalNews)
            .options(selectinload(InstitutionalNews.author))
            .where(InstitutionalNews.institution_id == institution_id)
        )
        if category:
            query = query.where(InstitutionalNews.category == category)
        if status:
            query = query.where(InstitutionalNews.status == status)

        query = query.order_by(InstitutionalNews.created_at.desc())
        result = await self._session.execute(query)
        return list(result.scalars().all())
