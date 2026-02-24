"""Setup for Ms-MASA: Polymarket Agent Specialist."""

from setuptools import setup, find_packages

setup(
    name="ms-masa",
    version="0.1.0",
    description="Polymarket Agent Specialist - Low-token agent framework for building on Polymarket",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Ms-MASA",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "httpx>=0.24.0",
    ],
    extras_require={
        "full": [
            "pydantic>=2.0.0",
            "python-dotenv>=1.0.0",
            "openai>=1.0.0",
            "py-clob-client",
        ],
    },
    entry_points={
        "console_scripts": [
            "ms-masa=ms_masa.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Libraries",
    ],
)
