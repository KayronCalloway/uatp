from setuptools import find_packages, setup

setup(
    name="uatp_capsule_engine",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    description="UATP Capsule Engine - cryptographic provenance for AI decisions.",
    author="Kayron Calloway",
    author_email="Kayron@houseofcalloway.com",
    url="https://github.com/KayronCalloway/uatp",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
