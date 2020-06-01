from setuptools import setup, find_packages

with open("README.rst", "rt", encoding="utf8") as f:
    readme = f.read()

setup(
    name="eth2",
    description="Eth2 API",
    version="0.0.4",
    long_description=readme,
    long_description_content_type="text/x-rst",
    author="protolambda",
    author_email="proto+pip@protolambda.com",
    url="https://github.com/protolambda/eth2.py",
    python_requires=">=3.8, <4",
    license="MIT",
    packages=find_packages(),
    tests_require=[],
    extras_require={
        "testing": ["pytest"],
        "linting": ["flake8"],
        "docs": ["sphinx", "sphinx-autodoc-typehints", "pallets_sphinx_themes", "sphinx_issues"]
    },
    install_requires=[
        "remerkleable>=0.1.16",
        "eth2spec>=0.11.2",
        "trio>=0.15.0,<0.16.0",
        "httpx>=0.12.1,<0.13.0",
    ],
    include_package_data=True,
    keywords=["eth2", "ethereum", "serenity", "api"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Operating System :: OS Independent",
    ],
)
