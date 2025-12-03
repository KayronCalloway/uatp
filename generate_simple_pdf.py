#!/usr/bin/env python3
"""
Generate PDF version of the comprehensive manual using Python libraries.
"""

import sys
from pathlib import Path


def generate_pdf_with_markdown2():
    """Generate PDF using markdown2 and weasyprint."""

    try:
        import markdown2
        import weasyprint
    except ImportError:
        print("❌ Required libraries not installed. Install with:")
        print("   pip install markdown2 weasyprint")
        return False

    manual_path = Path("docs/COMPREHENSIVE_SYSTEM_MANUAL.md")
    output_path = Path("docs/UATP_Capsule_Engine_Manual.pdf")

    if not manual_path.exists():
        print(f"❌ Manual not found at {manual_path}")
        return False

    print("📚 Generating PDF using Python libraries...")

    # Read the markdown file
    with open(manual_path, encoding="utf-8") as f:
        markdown_content = f.read()

    # Convert markdown to HTML
    html_content = markdown2.markdown(
        markdown_content, extras=["fenced-code-blocks", "tables", "header-ids", "toc"]
    )

    # Add CSS styling
    css_style = """
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #2c3e50;
            margin-top: 30px;
            margin-bottom: 15px;
        }
        h1 {
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 5px;
        }
        code {
            background-color: #f8f9fa;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        }
        pre {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            border-left: 4px solid #3498db;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }
        th, td {
            border: 1px solid #bdc3c7;
            padding: 8px 12px;
            text-align: left;
        }
        th {
            background-color: #ecf0f1;
            font-weight: bold;
        }
        blockquote {
            border-left: 4px solid #3498db;
            padding-left: 20px;
            margin-left: 0;
            font-style: italic;
            color: #7f8c8d;
        }
        .page-break {
            page-break-before: always;
        }
    </style>
    """

    # Create complete HTML document
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>UATP Capsule Engine - Comprehensive System Manual</title>
        {css_style}
    </head>
    <body>
        <h1>UATP Capsule Engine</h1>
        <h2>Comprehensive System Manual</h2>
        <p><strong>Version:</strong> 1.0<br>
        <strong>Date:</strong> July 9, 2025<br>
        <strong>Status:</strong> Complete Technical Implementation</p>

        <div class="page-break"></div>

        {html_content}
    </body>
    </html>
    """

    # Generate PDF
    try:
        weasyprint.HTML(string=full_html).write_pdf(str(output_path))
        print(f"✅ PDF manual generated successfully: {output_path}")
        print(f"   File size: {output_path.stat().st_size / (1024*1024):.2f} MB")
        return True
    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
        return False


def generate_pdf_with_reportlab():
    """Generate PDF using reportlab."""

    try:
        from reportlab.lib.colors import Color
        from reportlab.lib.pagesizes import A4, letter
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer
    except ImportError:
        print("❌ reportlab not installed. Install with:")
        print("   pip install reportlab")
        return False

    manual_path = Path("docs/COMPREHENSIVE_SYSTEM_MANUAL.md")
    output_path = Path("docs/UATP_Capsule_Engine_Manual.pdf")

    if not manual_path.exists():
        print(f"❌ Manual not found at {manual_path}")
        return False

    print("📚 Generating PDF using reportlab...")

    # Read the markdown file
    with open(manual_path, encoding="utf-8") as f:
        content = f.read()

    # Create PDF document
    doc = SimpleDocTemplate(str(output_path), pagesize=A4)

    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=24,
        spaceAfter=30,
        textColor=Color(0.2, 0.2, 0.2),
    )

    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=20,
        textColor=Color(0.1, 0.1, 0.1),
    )

    # Build content
    story = []

    # Title page
    story.append(Paragraph("UATP Capsule Engine", title_style))
    story.append(Paragraph("Comprehensive System Manual", heading_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Version: 1.0", styles["Normal"]))
    story.append(Paragraph("Date: July 9, 2025", styles["Normal"]))
    story.append(
        Paragraph("Status: Complete Technical Implementation", styles["Normal"])
    )
    story.append(PageBreak())

    # Process markdown content (basic conversion)
    lines = content.split("\n")

    for line in lines:
        if line.startswith("# "):
            story.append(Paragraph(line[2:], heading_style))
            story.append(Spacer(1, 12))
        elif line.startswith("## "):
            story.append(Paragraph(line[3:], styles["Heading2"]))
            story.append(Spacer(1, 6))
        elif line.startswith("### "):
            story.append(Paragraph(line[4:], styles["Heading3"]))
            story.append(Spacer(1, 6))
        elif line.strip():
            # Clean up markdown formatting for reportlab
            clean_line = line.replace("**", "<b>").replace("**", "</b>")
            clean_line = clean_line.replace("*", "<i>").replace("*", "</i>")
            clean_line = clean_line.replace("`", '<font name="Courier">')
            clean_line = clean_line.replace("`", "</font>")

            story.append(Paragraph(clean_line, styles["Normal"]))
            story.append(Spacer(1, 6))

    # Build PDF
    try:
        doc.build(story)
        print(f"✅ PDF manual generated successfully: {output_path}")
        print(f"   File size: {output_path.stat().st_size / (1024*1024):.2f} MB")
        return True
    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
        return False


def main():
    """Main function to generate PDF manual."""

    print("📖 UATP Capsule Engine Manual PDF Generator")
    print("=" * 50)

    # Try weasyprint first (better formatting)
    print("🔄 Attempting PDF generation with weasyprint...")
    success = generate_pdf_with_markdown2()

    if not success:
        print("🔄 Attempting PDF generation with reportlab...")
        success = generate_pdf_with_reportlab()

    if not success:
        print("\n❌ PDF generation failed with all methods.")
        print("\n💡 Alternative options:")
        print("1. Install pandoc: brew install pandoc")
        print("2. Install Python libraries: pip install markdown2 weasyprint")
        print("3. Install reportlab: pip install reportlab")
        print("4. Use online converter with docs/COMPREHENSIVE_SYSTEM_MANUAL.md")
        return False

    print("\n🎉 PDF manual generation complete!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
