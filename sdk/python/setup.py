"""
UATP Python SDK Setup
"""

from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="uatp",
    version="0.2.1",
    author="Kayron Calloway",
    author_email="Kayron@houseofcalloway.com",
    description="Cryptographic proof that AI made a decision, with this reasoning, at this time",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/KayronCalloway/uatp",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security :: Cryptography",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "pynacl>=1.5.0",  # Ed25519 signatures
        "cryptography>=41.0.0",  # Key encryption
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "mypy>=0.991",
        ],
    },
    keywords=["ai", "cryptography", "audit", "proof", "signatures", "ed25519"],
    project_urls={
        "Bug Reports": "https://github.com/KayronCalloway/uatp/issues",
        "Source": "https://github.com/KayronCalloway/uatp",
        "Documentation": "https://github.com/KayronCalloway/uatp/tree/main/sdk/python",
    },
)
