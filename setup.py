from setuptools import setup, find_packages

setup(
    name="fastapi-project",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn[standard]",
    ],
    python_requires=">=3.7",
)