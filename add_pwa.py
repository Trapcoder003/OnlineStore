import os
import sys

# --- THE CODE TO INJECT INTO <HEAD> ---
head_code = """
    <!-- PWA & FAVICONS -->
    <link rel="manifest" href="{% static 'manifest.json' %}">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <link rel="apple-touch-icon" sizes="180x180" href="{% static 'images/apple-touch-icon.png' %}">
    <link rel="icon" type="image/png" sizes="32x32" href="{% static 'images/favicon-32x32.png' %}">
    <link rel="icon" type="image/png" sizes="16x16" href="{% static 'images/favicon-16x16.png' %}">
"""

# --- THE CODE TO INJECT BEFORE </BODY> ---
body_code = """
<script>
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register("{% static 'js/sw.js' %}")
        .then(registration => console.log('ServiceWorker registered successfully:', registration.scope))
        .catch(error => console.log('ServiceWorker registration failed:', error));
    });
  }
</script>
"""

IGNORE_DIRS = ['venv', 'env', '.git', '__pycache__', 'node_modules', 'staticfiles', 'static']

print("🚀 Starting PWA injection script...")
print(f"📍 Currently looking in directory: {os.getcwd()}\n")

updated_files = 0
skipped_files = 0
found_html = 0

for root, dirs, files in os.walk('.'):
    # Skip ignored folders
    dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
    
    for file in files:
        if file.endswith('.html'):
            found_html += 1
            filepath = os.path.join(root, file)
            print(f"🔍 Found file: {filepath}")
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check if already injected
                if 'manifest.json' in content and 'serviceWorker' in content:
                    print(f"   ⏭️ Skipped (already updated)")
                    skipped_files += 1
                    continue

                # Inject into <head>
                if '</head>' in content and 'manifest.json' not in content:
                    content = content.replace('</head>', f"{head_code}\n</head>")

                # Inject before </body>
                if '</body>' in content and 'serviceWorker' not in content:
                    content = content.replace('</body>', f"{body_code}\n</body>")

                # Save the file
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"   ✅ Updated successfully!")
                updated_files += 1
                
            except Exception as e:
                print(f"   ❌ Error reading/writing this file: {e}")

print(f"\n🎉 Done! Found {found_html} HTML files. Updated {updated_files}, Skipped {skipped_files}.")