import resend
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings


class ResendBackend(BaseEmailBackend):
    """
    Minimal Django email backend using Resend HTTP API.
    Works on PythonAnywhere free tier — no SMTP needed.
    """

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently)
        resend.api_key = getattr(settings, "RESEND_API_KEY", "")

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        sent = 0
        for message in email_messages:
            try:
                html_body = None
                text_body = message.body or ""

                for content, mimetype in getattr(message, "alternatives", []):
                    if mimetype == "text/html":
                        html_body = content
                        break

                params = {
                    "from": message.from_email or settings.DEFAULT_FROM_EMAIL,
                    "to": list(message.to),
                    "subject": message.subject,
                }
                if html_body:
                    params["html"] = html_body
                    params["text"] = text_body
                else:
                    params["text"] = text_body

                resend.Emails.send(params)
                sent += 1

            except Exception as e:
                if not self.fail_silently:
                    raise
                print(f"Resend failed: {e}")

        return sent