"""
PEVN Backend — Email Delivery Service
Handles institutional email notifications and onboarding invitations.
Enforces accurate delivery statuses (EMAIL_SENT, EMAIL_NOT_CONFIGURED, EMAIL_SEND_FAILED)
and never logs raw tokens or secrets.
"""

from __future__ import annotations

import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import StrEnum

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

_logger = get_logger(__name__)


class EmailDeliveryStatus(StrEnum):
    """Authoritative delivery status for platform email dispatch."""

    EMAIL_SENT = "EMAIL_SENT"
    EMAIL_NOT_CONFIGURED = "EMAIL_NOT_CONFIGURED"
    EMAIL_SEND_FAILED = "EMAIL_SEND_FAILED"


class EmailService:
    """Service responsible for dispatching system emails via SMTP."""

    _mock_delivery_status: EmailDeliveryStatus | None = None

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    @classmethod
    def set_mock_status(cls, status: EmailDeliveryStatus | None) -> None:
        """Testing utility to force an email delivery status."""
        cls._mock_delivery_status = status

    def is_configured(self) -> bool:
        """Check if SMTP delivery is fully configured and enabled."""
        if self._mock_delivery_status is not None:
            return self._mock_delivery_status == EmailDeliveryStatus.EMAIL_SENT

        return bool(
            self._settings.EMAIL_DELIVERY_ENABLED
            and self._settings.SMTP_HOST
            and self._settings.SMTP_HOST.strip()
        )

    async def send_invitation_email(
        self,
        *,
        recipient_email: str,
        recipient_name: str,
        role_label: str,
        jurisdiction_label: str | None = None,
        activation_url: str,
    ) -> EmailDeliveryStatus:
        """
        Send an account activation invitation email.

        Never logs raw invitation tokens or passwords.
        Returns explicit EmailDeliveryStatus.
        """
        if self._mock_delivery_status is not None:
            _logger.info(
                "Email delivery mock status active",
                status=self._mock_delivery_status.value,
                recipient=recipient_email,
            )
            return self._mock_delivery_status

        if not self.is_configured():
            _logger.info(
                "SMTP email delivery is not configured; skipping email dispatch",
                recipient=recipient_email,
                role=role_label,
            )
            return EmailDeliveryStatus.EMAIL_NOT_CONFIGURED

        # Construct email message
        subject = f"Invitación de Activación de Cuenta — {role_label} PEVN"
        sender_email = self._settings.EMAILS_FROM_EMAIL
        sender_name = self._settings.EMAILS_FROM_NAME

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{sender_name} <{sender_email}>"
        msg["To"] = recipient_email

        jurisdiction_text = (
            f" para la jurisdicción {jurisdiction_label}"
            if jurisdiction_label
            else ""
        )

        text_content = (
            f"Estimado(a) {recipient_name},\n\n"
            "Se ha generado una cuenta institucional como "
            f"{role_label}{jurisdiction_text} en la Plataforma Educativa "
            "Virtual Nacional (PEVN).\n\n"
            "Para activar su cuenta y configurar su contraseña personal, "
            "acceda al siguiente enlace:\n"
            f"{activation_url}\n\n"
            "Este enlace es de uso único y tiene una validez de 48 horas.\n"
            "Si usted no esperaba esta invitación, por favor ignore este mensaje.\n\n"
            "Ministerio de Educación Nacional — PEVN"
        )

        btn_act_style = (
            "background-color: #2563EB; color: #FFFFFF; padding: 12px 24px; "
            "border-radius: 6px; text-decoration: none; font-weight: bold; "
            "display: inline-block;"
        )
        url_act_style = (
            "font-size: 0.8125rem; font-family: monospace; background-color: #F1F5F9; "
            "padding: 10px; border-radius: 4px; word-break: break-all;"
        )
        footer_act_style = (
            "font-size: 0.8125rem; color: #94A3B8; margin-top: 30px; "
            "border-top: 1px solid #E2E8F0; padding-top: 15px;"
        )

        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{subject}</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #1E293B; background-color: #F8FAFC; padding: 20px;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #FFFFFF; border-radius: 8px; border: 1px solid #E2E8F0; padding: 30px;">
    <h2 style="color: #0F172A; margin-top: 0;">Activación de Cuenta PEVN</h2>
    <p>Estimado(a) <strong>{recipient_name}</strong>,</p>
    <p>Se ha generado una cuenta institucional con el rol de <strong>{role_label}</strong>{jurisdiction_text} en la <strong>Plataforma Educativa Virtual Nacional (PEVN)</strong>.</p>
    <p>Para activar su cuenta y definir su contraseña personal segura, haga clic en el siguiente botón:</p>
    <div style="text-align: center; margin: 30px 0;">
      <a href="{activation_url}" style="{btn_act_style}">Activar Mi Cuenta</a>
    </div>
    <p style="font-size: 0.875rem; color: #64748B;">Si el botón no funciona, copie y pegue la siguiente dirección en su navegador:</p>
    <p style="{url_act_style}">{activation_url}</p>
    <p style="{footer_act_style}">
      * Este enlace de activación es de un solo uso y expirará en 48 horas.<br>
      Plataforma Educativa Virtual Nacional — Ministerio de Educación Nacional de Colombia.
    </p>
  </div>
</body>
</html>"""  # noqa: E501

        msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        def _send_sync() -> None:
            host = self._settings.SMTP_HOST
            port = self._settings.SMTP_PORT
            with smtplib.SMTP(host, port, timeout=10) as server:
                if self._settings.SMTP_TLS:
                    server.starttls()
                if self._settings.SMTP_USER and self._settings.SMTP_PASSWORD:
                    server.login(self._settings.SMTP_USER, self._settings.SMTP_PASSWORD)
                server.send_message(msg)

        try:
            await asyncio.to_thread(_send_sync)
            _logger.info(
                "Email invitation sent successfully",
                recipient=recipient_email,
                role=role_label,
            )
            return EmailDeliveryStatus.EMAIL_SENT
        except Exception as exc:
            _logger.warning(
                "Failed to deliver invitation email",
                recipient=recipient_email,
                error=str(exc),
            )
            return EmailDeliveryStatus.EMAIL_SEND_FAILED

    async def send_password_reset_email(
        self,
        *,
        recipient_email: str,
        reset_url: str,
        recipient_name: str | None = None,
    ) -> EmailDeliveryStatus:
        """
        Send a password reset email via SMTP.

        Never logs raw reset tokens or passwords.
        Returns explicit EmailDeliveryStatus.
        """
        if self._mock_delivery_status is not None:
            _logger.info(
                "Email delivery mock status active for password reset",
                status=self._mock_delivery_status.value,
                recipient=recipient_email,
            )
            return self._mock_delivery_status

        if not self.is_configured():
            _logger.info(
                "SMTP email delivery is not configured; skipping password reset email",
                recipient=recipient_email,
            )
            return EmailDeliveryStatus.EMAIL_NOT_CONFIGURED

        subject = "Restablecimiento de Contraseña — PEVN"
        sender_email = self._settings.EMAILS_FROM_EMAIL
        sender_name = self._settings.EMAILS_FROM_NAME
        name_display = recipient_name or recipient_email

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{sender_name} <{sender_email}>"
        msg["To"] = recipient_email

        text_content = (
            f"Estimado(a) {name_display},\n\n"
            "Hemos recibido una solicitud para restablecer su contraseña en la "
            "Plataforma Educativa Virtual Nacional (PEVN).\n\n"
            f"Para definir su nueva contraseña, acceda al siguiente enlace:\n"
            f"{reset_url}\n\n"
            "Este enlace es de uso único y tiene una validez de 1 hora.\n"
            "Si usted no solicitó este cambio, por favor ignore este mensaje.\n\n"
            "Ministerio de Educación Nacional — PEVN"
        )

        btn_style = (
            "background-color: #2563EB; color: #FFFFFF; padding: 12px 24px; "
            "border-radius: 6px; text-decoration: none; font-weight: bold; "
            "display: inline-block;"
        )
        url_box_style = (
            "font-size: 0.8125rem; font-family: monospace; background-color: #F1F5F9; "
            "padding: 10px; border-radius: 4px; word-break: break-all;"
        )
        footer_style = (
            "font-size: 0.8125rem; color: #94A3B8; margin-top: 30px; "
            "border-top: 1px solid #E2E8F0; padding-top: 15px;"
        )

        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{subject}</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #1E293B; background-color: #F8FAFC; padding: 20px;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #FFFFFF; border-radius: 8px; border: 1px solid #E2E8F0; padding: 30px;">
    <h2 style="color: #0F172A; margin-top: 0;">Restablecimiento de Contraseña PEVN</h2>
    <p>Estimado(a) <strong>{name_display}</strong>,</p>
    <p>Hemos recibido una solicitud para restablecer la contraseña de su cuenta en la <strong>Plataforma Educativa Virtual Nacional (PEVN)</strong>.</p>
    <p>Para continuar con el restablecimiento, haga clic en el siguiente botón:</p>
    <div style="text-align: center; margin: 30px 0;">
      <a href="{reset_url}" style="{btn_style}">Restablecer Mi Contraseña</a>
    </div>
    <p style="font-size: 0.875rem; color: #64748B;">Si el botón no funciona, copie y pegue la siguiente dirección en su navegador:</p>
    <p style="{url_box_style}">{reset_url}</p>
    <p style="{footer_style}">
      * Este enlace de recuperación es de un solo uso y expirará en 1 hora.<br>
      Plataforma Educativa Virtual Nacional — Ministerio de Educación Nacional de Colombia.
    </p>
  </div>
</body>
</html>"""  # noqa: E501

        msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        def _send_sync() -> None:
            host = self._settings.SMTP_HOST
            port = self._settings.SMTP_PORT
            with smtplib.SMTP(host, port, timeout=10) as server:
                if self._settings.SMTP_TLS:
                    server.starttls()
                if self._settings.SMTP_USER and self._settings.SMTP_PASSWORD:
                    server.login(self._settings.SMTP_USER, self._settings.SMTP_PASSWORD)
                server.send_message(msg)

        try:
            await asyncio.to_thread(_send_sync)
            _logger.info(
                "Password reset email sent successfully",
                recipient=recipient_email,
            )
            return EmailDeliveryStatus.EMAIL_SENT
        except Exception as exc:
            _logger.warning(
                "Failed to deliver password reset email",
                recipient=recipient_email,
                error=str(exc),
            )
            return EmailDeliveryStatus.EMAIL_SEND_FAILED
