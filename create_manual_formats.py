#!/usr/bin/env python3
"""
Create different formats of the comprehensive manual.
"""

import re
from pathlib import Path


def create_clean_text_version():
    """Create a clean text version of the manual."""

    manual_path = Path("docs/COMPREHENSIVE_SYSTEM_MANUAL.md")
    output_path = Path("docs/UATP_Capsule_Engine_Manual.txt")

    if not manual_path.exists():
        print(f"❌ Manual not found at {manual_path}")
        return False

    print("📝 Creating clean text version...")

    with open(manual_path, encoding="utf-8") as f:
        content = f.read()

    # Clean up markdown formatting for text version
    clean_content = content

    # Remove markdown links but keep the text
    clean_content = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", clean_content)

    # Convert headers to plain text with visual separation
    clean_content = re.sub(
        r"^# (.+)$", r"\n\1\n" + "=" * 80 + "\n", clean_content, flags=re.MULTILINE
    )
    clean_content = re.sub(
        r"^## (.+)$", r"\n\1\n" + "-" * 60 + "\n", clean_content, flags=re.MULTILINE
    )
    clean_content = re.sub(
        r"^### (.+)$", r"\n\1\n" + "~" * 40 + "\n", clean_content, flags=re.MULTILINE
    )
    clean_content = re.sub(
        r"^#### (.+)$", r"\n\1:\n", clean_content, flags=re.MULTILINE
    )

    # Remove bold/italic formatting
    clean_content = re.sub(r"\*\*([^*]+)\*\*", r"\1", clean_content)
    clean_content = re.sub(r"\*([^*]+)\*", r"\1", clean_content)

    # Clean up code blocks
    clean_content = re.sub(r"```[a-zA-Z]*\n", "\n--- CODE ---\n", clean_content)
    clean_content = re.sub(r"```", "\n--- END CODE ---\n", clean_content)

    # Clean up inline code
    clean_content = re.sub(r"`([^`]+)`", r"\1", clean_content)

    # Add header
    header = """
UATP CAPSULE ENGINE - COMPREHENSIVE SYSTEM MANUAL
===============================================

Version: 1.0
Date: July 9, 2025
Status: Complete Technical Implementation

This is the complete technical and strategic documentation for the
UATP (Unified Agent Trust Protocol) Capsule Engine system.

===============================================

"""

    final_content = header + clean_content

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_content)

    print(f"✅ Text manual created: {output_path}")
    print(f"   File size: {output_path.stat().st_size / 1024:.1f} KB")
    return True


def create_html_version():
    """Create HTML version with inline CSS."""

    manual_path = Path("docs/COMPREHENSIVE_SYSTEM_MANUAL.md")
    output_path = Path("docs/UATP_Capsule_Engine_Manual.html")

    if not manual_path.exists():
        print(f"❌ Manual not found at {manual_path}")
        return False

    print("🌐 Creating HTML version...")

    with open(manual_path, encoding="utf-8") as f:
        content = f.read()

    # Basic markdown to HTML conversion
    html_content = content

    # Convert headers
    html_content = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html_content, flags=re.MULTILINE)
    html_content = re.sub(
        r"^## (.+)$", r"<h2>\1</h2>", html_content, flags=re.MULTILINE
    )
    html_content = re.sub(
        r"^### (.+)$", r"<h3>\1</h3>", html_content, flags=re.MULTILINE
    )
    html_content = re.sub(
        r"^#### (.+)$", r"<h4>\1</h4>", html_content, flags=re.MULTILINE
    )

    # Convert bold/italic
    html_content = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", html_content)
    html_content = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", html_content)

    # Convert code blocks
    html_content = re.sub(
        r"```([a-zA-Z]*)\n(.*?)```",
        r'<pre><code class="\1">\2</code></pre>',
        html_content,
        flags=re.DOTALL,
    )

    # Convert inline code
    html_content = re.sub(r"`([^`]+)`", r"<code>\1</code>", html_content)

    # Convert links
    html_content = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', html_content
    )

    # Convert line breaks
    html_content = html_content.replace("\n", "<br>\n")

    # Create full HTML document
    full_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UATP Capsule Engine - Comprehensive System Manual</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #ffffff;
        }}

        h1, h2, h3, h4, h5, h6 {{
            color: #2c3e50;
            margin-top: 30px;
            margin-bottom: 15px;
        }}

        h1 {{
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            font-size: 2.5em;
        }}

        h2 {{
            border-bottom: 2px solid #bdc3c7;
            padding-bottom: 5px;
            font-size: 2em;
        }}

        h3 {{
            color: #34495e;
            font-size: 1.5em;
        }}

        h4 {{
            color: #34495e;
            font-size: 1.2em;
        }}

        code {{
            background-color: #f8f9fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9em;
            color: #e74c3c;
        }}

        pre {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            overflow-x: auto;
            border-left: 4px solid #3498db;
            margin: 20px 0;
        }}

        pre code {{
            background-color: transparent;
            padding: 0;
            color: #333;
        }}

        strong {{
            color: #2c3e50;
            font-weight: 600;
        }}

        em {{
            color: #7f8c8d;
        }}

        a {{
            color: #3498db;
            text-decoration: none;
        }}

        a:hover {{
            text-decoration: underline;
        }}

        .header {{
            text-align: center;
            border-bottom: 2px solid #3498db;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}

        .toc {{
            background-color: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}

        @media print {{
            body {{
                font-size: 12pt;
            }}

            h1, h2, h3 {{
                page-break-after: avoid;
            }}

            pre {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>UATP Capsule Engine</h1>
        <h2>Comprehensive System Manual</h2>
        <p><strong>Version:</strong> 1.0 | <strong>Date:</strong> July 9, 2025 | <strong>Status:</strong> Complete Technical Implementation</p>
    </div>

    {html_content}

    <footer style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #bdc3c7; text-align: center; color: #7f8c8d;">
        <p>UATP Capsule Engine Manual - Generated on July 9, 2025</p>
    </footer>
</body>
</html>
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    print(f"✅ HTML manual created: {output_path}")
    print(f"   File size: {output_path.stat().st_size / 1024:.1f} KB")
    return True


def create_pdf_instructions():
    """Create instructions for PDF conversion."""

    instructions = """
# Converting UATP Manual to PDF

## Method 1: Using Browser (Recommended)
1. Open the HTML manual: docs/UATP_Capsule_Engine_Manual.html
2. Press Ctrl+P (or Cmd+P on Mac)
3. Select "Save as PDF" as destination
4. Choose "More settings" and select:
   - Paper size: A4 or Letter
   - Margins: Normal
   - Options: Headers and footers (unchecked)
5. Click "Save"

## Method 2: Install Pandoc (Best Quality)
```bash
# macOS
brew install pandoc

# Ubuntu/Debian
sudo apt-get install pandoc

# Windows
choco install pandoc

# Then generate PDF
pandoc docs/COMPREHENSIVE_SYSTEM_MANUAL.md -o docs/UATP_Manual.pdf --pdf-engine=xelatex --toc
```

## Method 3: Online Converters
1. Go to https://pandoc.org/try/
2. Upload docs/COMPREHENSIVE_SYSTEM_MANUAL.md
3. Select "from: markdown" and "to: pdf"
4. Click "Convert"

## Method 4: Python Libraries
```bash
pip install markdown2 weasyprint
python3 generate_simple_pdf.py
```

The HTML version is already optimized for printing and PDF conversion.
"""

    with open("docs/PDF_CONVERSION_INSTRUCTIONS.md", "w") as f:
        f.write(instructions)

    print("✅ PDF conversion instructions created: docs/PDF_CONVERSION_INSTRUCTIONS.md")


def main():
    """Main function to create all manual formats."""

    print("📖 UATP Capsule Engine Manual Format Generator")
    print("=" * 60)

    # Create docs directory if it doesn't exist
    Path("docs").mkdir(exist_ok=True)

    success_count = 0

    # Create text version
    if create_clean_text_version():
        success_count += 1

    # Create HTML version
    if create_html_version():
        success_count += 1

    # Create PDF instructions
    create_pdf_instructions()
    success_count += 1

    print("\n" + "=" * 60)
    print("📋 Generation Summary:")
    print(f"✅ {success_count} formats created successfully")
    print()
    print("📁 Available formats:")
    print("   • docs/COMPREHENSIVE_SYSTEM_MANUAL.md (Original)")
    print("   • docs/UATP_Capsule_Engine_Manual.txt (Clean text)")
    print("   • docs/UATP_Capsule_Engine_Manual.html (Web/Print)")
    print("   • docs/PDF_CONVERSION_INSTRUCTIONS.md (PDF guide)")
    print()
    print("🖨️  For PDF: Open the HTML file and print to PDF")
    print("📱 For mobile: Use the HTML version")
    print("📄 For text editor: Use the TXT version")

    return success_count > 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
