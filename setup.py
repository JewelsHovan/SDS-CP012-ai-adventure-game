from setuptools import setup, find_packages

setup(
    name="ai-adventure-game",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "langchain",
        "openai",
        "pydantic",
    ],
    python_requires=">=3.10",
)
