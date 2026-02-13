"""HTML sanitization utilities for template content.

Strips dangerous HTML elements and attributes to prevent XSS attacks
while preserving safe structural HTML used in templates.
"""

import re
from html import escape as html_escape


# Tags that are completely removed (including their content)
DANGEROUS_TAGS_WITH_CONTENT = [
    'script', 'iframe', 'object', 'embed', 'applet', 'form',
    'input', 'textarea', 'select', 'button', 'link', 'meta',
    'base', 'noscript',
]

# Event handler attributes that are stripped
EVENT_HANDLER_RE = re.compile(
    r'\s+on\w+\s*=\s*(?:"[^"]*"|\'[^\']*\'|[^\s>]+)',
    re.IGNORECASE
)

# javascript: and data: URIs in attributes
DANGEROUS_URI_RE = re.compile(
    r'(href|src|action|formaction|xlink:href|poster|data)\s*=\s*["\']?\s*(?:javascript|data|vbscript)\s*:',
    re.IGNORECASE
)

# Style expressions that can execute code (IE-specific but defense-in-depth)
STYLE_EXPRESSION_RE = re.compile(
    r'expression\s*\(|behavior\s*:|url\s*\(\s*["\']?\s*javascript:|-moz-binding',
    re.IGNORECASE
)


def sanitize_html(html_content: str) -> str:
    """Sanitize HTML content by removing dangerous elements and attributes.

    Removes:
    - <script>, <iframe>, <object>, <embed>, <applet>, <form> tags and their content
    - All on* event handler attributes (onclick, onerror, onload, etc.)
    - javascript:, data:, vbscript: URIs in href/src attributes
    - CSS expressions and behaviors

    Preserves:
    - Safe structural HTML (div, span, h1-h6, p, img, etc.)
    - CSS classes and styles (without dangerous expressions)
    - Template placeholders ({{field_name}})
    """
    if not html_content:
        return html_content

    result = html_content

    # 1. Remove dangerous tags and their content
    for tag in DANGEROUS_TAGS_WITH_CONTENT:
        # Match opening tag with content and closing tag
        pattern = re.compile(
            rf'<{tag}[\s>].*?</{tag}\s*>',
            re.IGNORECASE | re.DOTALL
        )
        result = pattern.sub('', result)

        # Match self-closing variants
        pattern_self = re.compile(
            rf'<{tag}\s[^>]*/?\s*>',
            re.IGNORECASE
        )
        result = pattern_self.sub('', result)

        # Match opening tags without closing (malformed)
        pattern_open = re.compile(
            rf'<{tag}\s*>',
            re.IGNORECASE
        )
        result = pattern_open.sub('', result)

    # 2. Remove event handler attributes (on*)
    result = EVENT_HANDLER_RE.sub('', result)

    # 3. Remove dangerous URI schemes in attributes
    result = DANGEROUS_URI_RE.sub(r'\1=""', result)

    # 4. Remove CSS expressions in style attributes
    result = STYLE_EXPRESSION_RE.sub('/* removed */', result)

    return result


def sanitize_css(css_content: str) -> str:
    """Sanitize CSS content by removing dangerous directives.

    Removes:
    - @import rules (can load external resources)
    - CSS expressions and behaviors
    - url() with javascript: or data: schemes
    """
    if not css_content:
        return css_content

    result = css_content

    # Remove @import rules
    result = re.sub(r'@import\s+[^;]+;?', '/* import removed */', result, flags=re.IGNORECASE)

    # Remove CSS expressions
    result = STYLE_EXPRESSION_RE.sub('/* removed */', result)

    # Remove javascript: and data: in url()
    result = re.sub(
        r'url\s*\(\s*["\']?\s*(?:javascript|data|vbscript)\s*:[^)]*\)',
        'url(/* removed */)',
        result,
        flags=re.IGNORECASE,
    )

    return result


def escape_text(text: str) -> str:
    """Escape text for safe insertion into HTML.

    Converts special characters to HTML entities:
    - & -> &amp;
    - < -> &lt;
    - > -> &gt;
    - " -> &quot;
    - ' -> &#x27;
    """
    return html_escape(text, quote=True)
