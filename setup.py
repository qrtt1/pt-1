from setuptools import setup, find_packages

setup(
    name="pt-1",
    version="0.2.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn[standard]",
        "python-dotenv",  # CLI config management
        "requests",       # CLI API client
    ],
    entry_points={
        "console_scripts": [
            "pt1=pt1_cli.cli:main",
        ],
    },
    python_requires=">=3.7",
)