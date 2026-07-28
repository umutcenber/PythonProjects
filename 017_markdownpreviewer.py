import markdown
import webbrowser
import os

print("=" * 40)
print("     MARKDOWN PREVIEWER")
print("=" * 40)

file_path = input("Enter Markdown file path: ").strip()

if not os.path.exists(file_path):
    print("❌ File not found.")
    exit()

if not file_path.endswith(".md"):
    print("❌ Please select a Markdown (.md) file.")
    exit()

with open(file_path, "r", encoding="utf-8") as file:
    md_text = file.read()

html = markdown.markdown(md_text)

html_page = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Markdown Preview</title>
</head>
<body style="font-family:Arial;padding:40px;">
{html}
</body>
</html>
"""

output = "preview.html"

with open(output, "w", encoding="utf-8") as file:
    file.write(html_page)

webbrowser.open(output)

print("✅ Preview opened in your browser!")