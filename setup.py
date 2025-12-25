from setuptools import setup, find_packages

setup(
    name="pt-1",
    version="0.3.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn[standard]",
        "python-dotenv",
        "requests",
        "python-multipart",  # For file uploads
        "pydantic",
    ],
    entry_points={
        "console_scripts": [
            "pt1=pt1_cli.cli:main",
            "pt1-server=pt1_server.main:run_server",
        ],
    },
    python_requires=">=3.7",
    description="PT-1: Remote PowerShell execution system with CLI and Server components",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/pt-1",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: System :: Systems Administration",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
