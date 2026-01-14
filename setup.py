#!/usr/bin/env python3
"""
Setup script for mcp-echo
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mcp-echo",
    version="0.1.0",
    author="Bach Studio",
    author_email="contact@bachstudio.com",
    description="一个简单的MCP服务器，提供echo功能：输入什么就返回什么",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/BACH-AI-Tools/mcp-echo",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=[
        "mcp>=0.9.0",
    ],
    entry_points={
        "console_scripts": [
            "mcp-echo=mcp_echo.server:main",
        ],
    },
    keywords="mcp, echo, model-context-protocol, bachstudio",
    project_urls={
        "Bug Reports": "https://github.com/BACH-AI-Tools/mcp-echo/issues",
        "Source": "https://github.com/BACH-AI-Tools/mcp-echo",
    },
)
