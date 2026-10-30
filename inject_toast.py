import os, re, shutil, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FOLDERS = [
    os.path.join(ROOT, "shopApp/templates/pages"),
    os.path.join(ROOT, "shopApp/templates/staff"),
]
DRY = "--dry-run" in sys.argv

HIDDEN_DIV = """
<!-- HIDDEN DJANGO MESSAGES -->
<div id="django-messages" style="display:none;">
  {% for m in messages %}<div data-msg="{{ m }}" data-tag="{{ m.tags }}"></div>{% endfor %}
</div>
"""

SCRIPT_TAG = "<script src=\"{% static 'js/toast.js' %}\"></script>\n"

def ensure_load_static(content):
    if re.search(r"{%\s*load\s+[^%]*\bstatic\b", content):
        return content
    m = re.search(r"{%\s*extends\s+[^%]*%}", content)
    if m:
        return content[: m.end()] + "\n{% load static %}" + content[m.end():]
    return "{% load static %}\n" + content

def process_file(path):
    with open(path, encoding="utf-8") as f:
        original = f.read()
    content = original
    content = re.sub(r"{%\s*if\s+messages\s*%}.*?{%\s*endif\s*%}", "", content, flags=re.DOTALL)
    content = re.sub(r'<div[^>]*\bid=["\']toast["\'][^>]*>.*?</div>', "", content, flags=re.DOTALL)
    if '<div id="django-messages"' not in content:
        content, n = re.subn(r"<body([^>]*)>",
                             lambda m: f"<body{m.group(1)}>\n{HIDDEN_DIV}",
                             content, count=1)
        if n == 0:
            print(f"  no <body> tag in {path}")
    if "js/toast.js" not in content:
        content = content.replace("</body>", f"{SCRIPT_TAG}</body>")
    content = ensure_load_static(content)
    if content == original:
        print(f"— no change: {path}")
        return
    if DRY:
        print(f"[dry-run] would update: {path}")
        return
    shutil.copy2(path, path + ".bak")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Updated: {path}")

for folder in FOLDERS:
    if not os.path.isdir(folder):
        print(f"⚠️  missing folder: {folder}")
        continue
    for name in sorted(os.listdir(folder)):
        if name.endswith(".html") and not name.startswith("_"):
            process_file(os.path.join(folder, name))
