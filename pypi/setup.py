from setuptools import setup, find_packages

setup(
    name="tbn-protocol",
    version="0.1.0",
    author="Burhan Yanbolu",
    author_email="burhan@hardinai.co.uk",
    description="TBN Protocol — Trust infrastructure for AI agents. Think HTTPS for bots.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/burhanyanbolu-design/tbn-protocol",
    project_urls={
        "Homepage": "https://tbn.hardinai.co.uk",
        "Documentation": "https://tbn.hardinai.co.uk",
        "Bug Tracker": "https://github.com/burhanyanbolu-design/tbn-protocol/issues",
    },
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
        "Topic :: Security :: Cryptography",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
        "Development Status :: 4 - Beta",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "cryptography>=38.0.0",
    ],
    keywords="ai agents trust protocol security cryptography bots tbn",
)
