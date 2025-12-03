#!/usr/bin/env python3
"""
Simple markdown to PDF converter using markdown-pdf.
"""

import markdown_pdf
from pathlib import Path
import sys


def convert_markdown_to_pdf(markdown_file, pdf_file):
    """Convert markdown file to PDF."""

    try:
        print(f"Converting {markdown_file} to PDF...")

        # Read markdown content
        with open(markdown_file, "r", encoding="utf-8") as f:
            markdown_content = f.read()

        # Convert markdown to PDF
        markdown_pdf.MarkdownPdf(
            paper_size="A4", margin="2cm", font_size=11, font_family="Arial"
        ).convert(markdown_content, pdf_file)

        print(f"PDF successfully created: {pdf_file}")
        return True

    except Exception as e:
        print(f"Error converting to PDF: {e}")
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
        print(f"📊 File size: {pdf_file.stat().st_size / 1024:.1f} KB")
    else:
        print("\n❌ PDF conversion failed!")
        sys.exit(1)
