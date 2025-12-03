#!/usr/bin/env python3
"""
Generate PDF version of the comprehensive system manual.
"""

import os
import sys
from pathlib import Path


def generate_pdf_manual():
    """Generate PDF from the comprehensive manual using pandoc."""

    manual_path = Path("docs/COMPREHENSIVE_SYSTEM_MANUAL.md")
    output_path = Path("docs/UATP_Capsule_Engine_Manual.pdf")

    if not manual_path.exists():
        print(f"❌ Manual not found at {manual_path}")
        return False

    # Check if pandoc is installed
    pandoc_check = os.system("which pandoc > /dev/null 2>&1")
    if pandoc_check != 0:
        print("❌ pandoc is not installed. Please install it first:")
        print("   On macOS: brew install pandoc")
        print("   On Ubuntu: sudo apt-get install pandoc")
        print("   On Windows: choco install pandoc")
        return False

    # Check if wkhtmltopdf is available for better PDF generation
    wkhtmltopdf_check = os.system("which wkhtmltopdf > /dev/null 2>&1")

    print("📚 Generating PDF manual...")

    # Create pandoc command with comprehensive options
    pandoc_cmd = [
        "pandoc",
        str(manual_path),
        "-o",
        str(output_path),
        "--from=markdown",
        "--to=pdf",
        "--pdf-engine=xelatex",  # Use xelatex for better Unicode support
        "--variable=documentclass:article",
        "--variable=geometry:margin=1in",
        "--variable=fontsize:11pt",
        "--variable=linestretch:1.2",
        "--table-of-contents",
        "--toc-depth=3",
        "--number-sections",
        "--highlight-style=github",
        "--variable=colorlinks:true",
        "--variable=linkcolor:blue",
        "--variable=urlcolor:blue",
        "--variable=toccolor:black",
        "--standalone",
    ]

    # Add title page information
    title_options = [
        "--metadata=title:UATP Capsule Engine - Comprehensive System Manual",
        "--metadata=author:Claude Code Assistant",
        "--metadata=date:July 9, 2025",
        "--metadata=subject:UATP Capsule Engine Documentation",
        "--metadata=keywords:UATP,Capsule,Engine,AI,Attribution,Economics",
    ]

    pandoc_cmd.extend(title_options)

    # Execute pandoc command
    result = os.system(" ".join(pandoc_cmd))

    if result == 0:
        print(f"✅ PDF manual generated successfully: {output_path}")
        print(f"   File size: {output_path.stat().st_size / (1024*1024):.2f} MB")
        return True
    else:
        print("❌ PDF generation failed. Trying alternative method...")

        # Fallback: Try with basic options
        basic_cmd = [
            "pandoc",
            str(manual_path),
            "-o",
            str(output_path),
            "--from=markdown",
            "--to=pdf",
            "--table-of-contents",
            "--number-sections",
        ]

        fallback_result = os.system(" ".join(basic_cmd))

        if fallback_result == 0:
            print(f"✅ PDF manual generated with basic formatting: {output_path}")
            return True
        else:
            print("❌ PDF generation failed with both methods")
            return False


def generate_html_manual():
    """Generate HTML version as fallback."""

    manual_path = Path("docs/COMPREHENSIVE_SYSTEM_MANUAL.md")
    output_path = Path("docs/UATP_Capsule_Engine_Manual.html")

    print("🌐 Generating HTML manual as fallback...")

    pandoc_cmd = [
        "pandoc",
        str(manual_path),
        "-o",
        str(output_path),
        "--from=markdown",
        "--to=html5",
        "--standalone",
        "--table-of-contents",
        "--toc-depth=3",
        "--number-sections",
        "--highlight-style=github",
        "--css=https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.2.0/github-markdown-light.min.css",
        "--metadata=title:UATP Capsule Engine - Comprehensive System Manual",
        "--variable=margin-left:auto",
        "--variable=margin-right:auto",
        "--variable=max-width:1000px",
    ]

    result = os.system(" ".join(pandoc_cmd))

    if result == 0:
        print(f"✅ HTML manual generated successfully: {output_path}")
        return True
    else:
        print("❌ HTML generation failed")
        return False


def main():
    """Main function to generate manual in multiple formats."""

    print("📖 UATP Capsule Engine Manual Generator")
    print("=" * 50)

    # Try to generate PDF first
    pdf_success = generate_pdf_manual()

    # Generate HTML as fallback or additional format
    html_success = generate_html_manual()

    print("\n" + "=" * 50)
    print("📋 Generation Summary:")

    if pdf_success:
        print("✅ PDF manual: docs/UATP_Capsule_Engine_Manual.pdf")
    else:
        print("❌ PDF manual: Failed to generate")

    if html_success:
        print("✅ HTML manual: docs/UATP_Capsule_Engine_Manual.html")
    else:
        print("❌ HTML manual: Failed to generate")

    if not pdf_success and not html_success:
        print("\n💡 Alternative options:")
        print("1. Install pandoc: brew install pandoc (macOS)")
        print("2. Use online converter: https://pandoc.org/try/")
        print("3. Copy docs/COMPREHENSIVE_SYSTEM_MANUAL.md to a markdown viewer")
        return False

    print("\n🎉 Manual generation complete!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
