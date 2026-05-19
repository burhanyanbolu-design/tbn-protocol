"""
TBN LangChain — Governance layer for LangChain AI agents.
Wraps any LangChain agent with TBN Protocol identity, enforcement, and audit.

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0.
"""

from setuptools import setup, find_packages

setup(
    name="tbn-langchain",
    version="0.1.0",
    description="TBN Protocol governance integration for LangChain agents",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Burhan Yanbolu",
    author_email="burhan@hardinai.co.uk",
    url="https://github.com/burhanyanbolu-design/tbn-protocol",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "langchain>=0.1.0",
        "tbn-protocol>=0.1.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Programming Language :: Python :: 3",
        "Topic :: Security",
        "Topic :: Software Development :: Libraries",
    ],
    keywords="ai governance langchain agents tbn trust enforcement",
)
