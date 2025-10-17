import logging
import os
from pathlib import Path

import boto3
import jinja2
from botocore.exceptions import ClientError

from tuto.auth.exceptions import (
    EmailDeliveryError,
    EmailTemplateError,
    SystemConfigurationError,
)

logger = logging.getLogger(__name__)

# AWS SES configuration
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "ap-northeast-1")
SES_CONFIG_SET = os.environ.get("AUTH_SES_CONFIG_SET", "")
DEFAULT_FROM_EMAIL = os.environ.get("AUTH_FROM_EMAIL", "noreply@example.com")


def _get_ses_client():
    """Get SES client instance"""
    return boto3.client("sesv2", region_name=AWS_REGION)


def _render_template(template_name: str, **kwargs) -> str:
    """Render email template using jinja2"""
    try:
        # Get template directory relative to this file
        template_dir = Path(__file__).parent.parent / "templates" / "auth"

        if not template_dir.exists():
            raise EmailTemplateError(
                f"Template directory not found: {template_dir}",
                template_name=template_name,
                error_code="TEMPLATE_DIR_NOT_FOUND",
            )

        loader = jinja2.FileSystemLoader(template_dir, encoding="UTF-8")
        env = jinja2.Environment(loader=loader)

        template = env.get_template(template_name)
        return template.render(**kwargs)

    except jinja2.exceptions.TemplateNotFound:
        raise EmailTemplateError(
            f"Email template not found: {template_name}",
            template_name=template_name,
            error_code="TEMPLATE_NOT_FOUND",
        )
    except jinja2.exceptions.TemplateSyntaxError as e:
        raise EmailTemplateError(
            f"Template syntax error in {template_name}: {e}",
            template_name=template_name,
            error_code="TEMPLATE_SYNTAX_ERROR",
            details={"line_number": e.lineno, "error_detail": str(e)},
        )
    except jinja2.exceptions.UndefinedError as e:
        raise EmailTemplateError(
            f"Template variable error in {template_name}: {e}",
            template_name=template_name,
            error_code="TEMPLATE_VARIABLE_ERROR",
            details={"error_detail": str(e)},
        )


def _send_email(
    to_email: str,
    subject: str,
    body_text: str,
    from_email: str = None,
    config_set: str = None,
) -> str:
    """Send email using AWS SES"""
    # Validate configuration
    sender_email = from_email or DEFAULT_FROM_EMAIL
    if not sender_email or sender_email == "noreply@example.com":
        raise SystemConfigurationError(
            "FROM email address not properly configured",
            config_key="AUTH_FROM_EMAIL",
            error_code="MISSING_FROM_EMAIL",
        )

    # Validate input parameters
    if not to_email or "@" not in to_email:
        raise EmailDeliveryError(
            f"Invalid recipient email address: {to_email}",
            recipient_email=to_email,
            error_code="INVALID_EMAIL",
        )

    try:
        ses_client = _get_ses_client()

        email_params = {
            "FromEmailAddress": sender_email,
            "Destination": {
                "ToAddresses": [to_email],
            },
            "Content": {
                "Simple": {
                    "Subject": {
                        "Data": subject,
                        "Charset": "UTF-8",
                    },
                    "Body": {
                        "Text": {
                            "Data": body_text,
                            "Charset": "UTF-8",
                        },
                    },
                },
            },
        }

        # Add configuration set if provided
        if config_set or SES_CONFIG_SET:
            email_params["ConfigurationSetName"] = config_set or SES_CONFIG_SET

        response = ses_client.send_email(**email_params)
        message_id = response.get("MessageId")

        logger.info(f"Email sent successfully to {to_email}. MessageId: {message_id}")
        return message_id

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]

        # Map SES error codes to more specific exceptions
        if error_code in ["MessageRejected", "MailFromDomainNotVerified"]:
            raise EmailDeliveryError(
                f"Email delivery rejected: {error_message}",
                recipient_email=to_email,
                ses_error_code=error_code,
                error_code="DELIVERY_REJECTED",
            )
        elif error_code == "SendingQuotaExceeded":
            raise EmailDeliveryError(
                "Daily sending quota exceeded",
                recipient_email=to_email,
                ses_error_code=error_code,
                error_code="QUOTA_EXCEEDED",
            )
        elif error_code == "SendingPausedException":
            raise EmailDeliveryError(
                "Email sending is paused for your account",
                recipient_email=to_email,
                ses_error_code=error_code,
                error_code="SENDING_PAUSED",
            )
        else:
            raise EmailDeliveryError(
                f"SES error: {error_message}",
                recipient_email=to_email,
                ses_error_code=error_code,
                error_code="SES_ERROR",
            )

    except Exception as e:
        logger.error(f"Unexpected error sending email to {to_email}: {e}")
        raise EmailDeliveryError(
            f"Unexpected error sending email: {e}",
            recipient_email=to_email,
            error_code="UNEXPECTED_ERROR",
        )


def send_temporary_password_email(
    email: str, username: str, temporary_password: str
) -> str:
    """
    Send temporary password to user via email using SES and jinja2 template.

    :param email: User's email address
    :param username: User's username
    :param temporary_password: The temporary password to send
    :return: SES Message ID if successful
    :raises EmailTemplateError: If template rendering fails
    :raises EmailDeliveryError: If email delivery fails
    :raises SystemConfigurationError: If system configuration is invalid
    """
    # Validate input parameters
    if not email or not email.strip():
        raise EmailDeliveryError(
            "Email address is required", error_code="MISSING_EMAIL"
        )

    if not username or not username.strip():
        raise EmailDeliveryError("Username is required", error_code="MISSING_USERNAME")

    if not temporary_password or not temporary_password.strip():
        raise EmailDeliveryError(
            "Temporary password is required", error_code="MISSING_TEMPORARY_PASSWORD"
        )

    try:
        # Render email content from template
        body_text = _render_template(
            "temporary_password.j2",
            username=username,
            temporary_password=temporary_password,
        )

        subject = "Temporary Password Notification"

        # Send email
        message_id = _send_email(to_email=email, subject=subject, body_text=body_text)

        logger.info(
            f"Temporary password email sent to {username} ({email}). MessageId: {message_id}"
        )
        return message_id

    except (EmailTemplateError, EmailDeliveryError, SystemConfigurationError):
        # Re-raise custom exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error sending temporary password email: {e}")
        raise EmailDeliveryError(
            f"Unexpected error sending temporary password email: {e}",
            recipient_email=email,
            error_code="UNEXPECTED_ERROR",
        )


def send_password_reset_notification(
    email: str, username: str, success: bool = True
) -> str | None:
    """
    Send password reset success notification.

    :param email: User's email address
    :param username: User's username
    :param success: Whether the password reset was successful
    :return: SES Message ID if successful, None if skipped
    :raises EmailTemplateError: If template rendering fails
    :raises EmailDeliveryError: If email delivery fails
    :raises SystemConfigurationError: If system configuration is invalid
    """
    if not success:
        # Don't send notification for failed resets
        logger.info(
            f"Skipping notification for failed password reset: {username} ({email})"
        )
        return None

    # Validate input parameters
    if not email or not email.strip():
        raise EmailDeliveryError(
            "Email address is required", error_code="MISSING_EMAIL"
        )

    if not username or not username.strip():
        raise EmailDeliveryError("Username is required", error_code="MISSING_USERNAME")

    try:
        # Render email content from template
        body_text = _render_template("password_reset_success.j2", username=username)

        subject = "[シゴトin] パスワード変更完了のお知らせ"

        # Send email
        message_id = _send_email(to_email=email, subject=subject, body_text=body_text)

        logger.info(
            f"Password reset notification sent to {username} ({email}). MessageId: {message_id}"
        )
        return message_id

    except (EmailTemplateError, EmailDeliveryError, SystemConfigurationError):
        # Re-raise custom exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error sending password reset notification: {e}")
        raise EmailDeliveryError(
            f"Unexpected error sending password reset notification: {e}",
            recipient_email=email,
            error_code="UNEXPECTED_ERROR",
        )
