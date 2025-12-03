from setuptools import find_packages, setup

setup(
    name="uatp_capsule_engine",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    description="UATP Capsule Engine for universal attribution, trust, and economic justice.",
    author="UATP Foundation",
    author_email="contact@uatp.org",
    url="https://github.com/UATP/capsule-engine",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
