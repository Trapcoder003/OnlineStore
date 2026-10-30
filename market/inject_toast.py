import os, re, shutil, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FOLDERS = [
    os.path.join(ROOT, "shopApp/templates/pages"),
    os.path.join(ROOT, "shopApp/templates/staff"),
    # add your base template folder here if base.html lives elsewhere:
    # os.path.join(ROOT, "shopApp/templates"),
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
    if m:  # load must come after extends
        return content[: m.end()] + "\n{% load static %}" + content[m.end():]
    return "{% load static %}\n" + content


def process_file(path):
    with open(path, encoding="utf-8") as f:
        original = f.read()
    content = original

    # remove old flash blocks
    content = re.sub(r"{%\s*if\s+messages\s*%}.*?{%\s*endif\s*%}", "", content, flags=re.DOTALL)
    # remove old inline toast divs
    content = re.sub(r'<div[^>]*\bid=["\']toast["\'][^>]*>.*?</div>', "", content, flags=re.DOTALL)

    # inject hidden message container after <body ...>
    if '<div id="django-messages"' not in content:
        content, n = re.subn(
            r"<body([^>]*)>",
            lambda m: f"<body{m.group(1)}>\n{HIDDEN_DIV}",
            content,
            count=1,
        )
        if n == 0:
            print(f"⚠️  no <body> tag in {path} (probably a child template, fine)")

    # inject toast script before </body>
    if "js/toast.js" not in content:
        content = content.replace("</body>", f"{SCRIPT_TAG}</body>")

    # make sure {% load static %} exists if we now reference {% static %}
    content = ensure_load_static(content)

    if content == original:
        print(f"— no change: {path}")
        return
    if DRY:
        print(f"[dry-run] would update: {path}")
        return

    shutil.copy2(path, path + ".bak")  # keep a backup
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