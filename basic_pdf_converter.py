#!/usr/bin/env python3
"""
Basic markdown to PDF converter.
"""

import markdown_pdf
from pathlib import Path
import sys
import re


def clean_markdown_content(content):
    """Clean markdown content to avoid PDF conversion issues."""

    # Remove complex anchor links and references
    content = re.sub(r"\[([^\]]+)\]\(#[^)]+\)", r"\1", content)

    # Simplify table formatting
    content = re.sub(r"\|\s*-+\s*\|", "|---|", content)

    # Remove complex code blocks with language specifiers
    content = re.sub(r"```(\w+)\n", "```\n", content)

    # Remove HTML comments
    content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)

    return content


def convert_markdown_to_pdf(markdown_file, pdf_file):
    """Convert markdown file to PDF."""

    try:
        print(f"Converting {markdown_file} to PDF...")

        # Read markdown content
        with open(markdown_file, "r", encoding="utf-8") as f:
            markdown_content = f.read()

        # Clean content
        clean_content = clean_markdown_content(markdown_content)

        # Create PDF converter
        converter = markdown_pdf.MarkdownPdf()

        # Basic CSS styling
        custom_css = """
        body {
            font-family: Arial, sans-serif;
            font-size: 11px;
            line-height: 1.5;
            color: #333;
            margin: 2cm;
        }
        
        h1 {
            color: #2c3e50;
            font-size: 20px;
            margin-top: 25px;
            margin-bottom: 15px;
            page-break-before: always;
        }
        
        h1:first-child {
            page-break-before: avoid;
        }
        
        h2 {
            color: #34495e;
            font-size: 16px;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        
        h3 {
            color: #34495e;
            font-size: 14px;
            margin-top: 15px;
            margin-bottom: 8px;
        }
        
        pre {
            background-color: #f5f5f5;
            padding: 10px;
            margin: 10px 0;
            font-size: 9px;
            border-radius: 3px;
            overflow-x: auto;
        }
        
        code {
            background-color: #f5f5f5;
            padding: 2px 4px;
            font-size: 9px;
            border-radius: 2px;
        }
        
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 10px 0;
            font-size: 9px;
        }
        
        th, td {
            border: 1px solid #ddd;
            padding: 5px;
            text-align: left;
        }
        
        th {
            background-color: #f5f5f5;
            font-weight: bold;
        }
        """

        # Create a section with the cleaned markdown content
        section = markdown_pdf.Section(clean_content)

        # Add section to PDF
        converter.add_section(section, user_css=custom_css)

        # Save PDF
        converter.save(pdf_file)

        print(f"PDF successfully created: {pdf_file}")
        return True

    except Exception as e:
        print(f"Error converting to PDF: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    # File paths
    markdown_file = Path(
        "/Users/kay/uatp-capsule-engine/UATP_Capsule_Engine_System_Guide.md"
    )
    pdf_file = Path(
        "/Users/kay/uatp-capsule-engine/UATP_Capsule_Engine_System_Guide.pdf"
    )

    # Convert markdown to PDF
    success = convert_markdown_to_pdf(markdown_file, pdf_file)

    if success:
        print(f"\n✅ PDF conversion completed successfully!")
        print(f"📄 PDF file: {pdf_file}")
        if pdf_file.exists():
            print(f"📊 File size: {pdf_file.stat().st_size / 1024:.1f} KB")
    else:
        print("\n❌ PDF conversion failed!")
        sys.exit(1)
