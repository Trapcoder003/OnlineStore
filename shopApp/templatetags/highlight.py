from django import template
from django.utils.html import escape, mark_safe
import re

register = template.Library()


@register.filter(name="highlight")
def highlight(text, term):
    """Wrap each occurrence of `term` in <mark>…</mark> inside `text`."""
    text = str(text)
    if not term:
        return escape(text)

    pattern = re.compile(re.escape(term), re.IGNORECASE)
    safe_text = escape(text)

    return mark_safe(
        pattern.sub(lambda m: f"<mark>{escape(m.group(0))}</mark>", safe_text)
    )