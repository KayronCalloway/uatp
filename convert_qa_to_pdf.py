#!/usr/bin/env python3
"""
Convert TECHNICAL_QA_ENTERPRISE_BUYERS.md to PDF
"""

import markdown
from weasyprint import HTML, CSS
from pathlib import Path


def convert_md_to_pdf():
    """Convert markdown to PDF with proper formatting"""

    # Read markdown file
    md_file = Path("docs/TECHNICAL_QA_ENTERPRISE_BUYERS.md")
    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()

    # Convert markdown to HTML
    html_content = markdown.markdown(
        md_content, extensions=["extra", "codehilite", "tables", "fenced_code"]
    )

    # Add CSS styling
    css_styling = """
    <style>
        @page {
            size: letter;
            margin: 0.75in;
            @bottom-right {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 9pt;
                color: #666;
            }
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            font-size: 10pt;
            line-height: 1.6;
            color: #333;
        }

        h1 {
            font-size: 24pt;
            font-weight: bold;
            color: #1a1a1a;
            margin-top: 0.5in;
            margin-bottom: 0.25in;
            border-bottom: 2pt solid #333;
            padding-bottom: 0.1in;
            page-break-before: always;
        }

        h1:first-of-type {
            page-break-before: avoid;
        }

        h2 {
            font-size: 18pt;
            font-weight: bold;
            color: #2a2a2a;
            margin-top: 0.3in;
            margin-bottom: 0.15in;
            border-bottom: 1pt solid #666;
            padding-bottom: 0.05in;
        }

        h3 {
            font-size: 14pt;
            font-weight: bold;
            color: #333;
            margin-top: 0.2in;
            margin-bottom: 0.1in;
        }

        h4 {
            font-size: 12pt;
            font-weight: bold;
            color: #444;
            margin-top: 0.15in;
            margin-bottom: 0.08in;
        }

        p {
            margin: 0.08in 0;
            text-align: justify;
        }

        pre {
            background-color: #f6f8fa;
            border: 1pt solid #d1d5da;
            border-radius: 3pt;
            padding: 0.1in;
            font-family: 'Courier New', Courier, monospace;
            font-size: 9pt;
            line-height: 1.4;
            overflow-x: auto;
            margin: 0.1in 0;
            page-break-inside: avoid;
        }

        code {
            background-color: #f6f8fa;
            border: 1pt solid #d1d5da;
            border-radius: 2pt;
            padding: 1pt 3pt;
            font-family: 'Courier New', Courier, monospace;
            font-size: 9pt;
        }

        pre code {
            background-color: transparent;
            border: none;
            padding: 0;
        }

        ul, ol {
            margin: 0.08in 0;
            padding-left: 0.25in;
        }

        li {
            margin: 0.04in 0;
        }

        table {
            border-collapse: collapse;
            width: 100%;
            margin: 0.1in 0;
            font-size: 9pt;
        }

        th, td {
            border: 1pt solid #ddd;
            padding: 0.05in;
            text-align: left;
        }

        th {
            background-color: #f0f0f0;
            font-weight: bold;
        }

        blockquote {
            border-left: 3pt solid #ddd;
            padding-left: 0.15in;
            margin: 0.1in 0;
            color: #666;
            font-style: italic;
        }

        hr {
            border: none;
            border-top: 1pt solid #ddd;
            margin: 0.2in 0;
        }

        a {
            color: #0366d6;
            text-decoration: none;
        }

        .page-break {
            page-break-after: always;
        }
    </style>
    """

    # Create complete HTML document
    html_doc = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>UATP Technical Q&A for Enterprise Buyers</title>
        {css_styling}
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Convert HTML to PDF
    output_file = Path("docs/TECHNICAL_QA_ENTERPRISE_BUYERS.pdf")

    print(f"Converting {md_file} to PDF...")
    print(f"Output: {output_file}")

    HTML(string=html_doc).write_pdf(output_file, stylesheets=[CSS(string=css_styling)])

    print(f"✅ PDF created successfully!")
    print(f"📄 File size: {output_file.stat().st_size / 1024:.1f} KB")

    return output_file


if __name__ == "__main__":
    try:
        pdf_file = convert_md_to_pdf()
        print(f"\n✅ SUCCESS: PDF generated at {pdf_file}")
    except ImportError as e:
        print(f"\n❌ ERROR: Missing required library")
        print(f"Please install: pip install markdown weasyprint")
        print(f"Error details: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
