import itertools

from setuptools import find_packages, setup

with open("README.rst") as f:
    description = f.read()


install_requires = [
    "buvar",
    "aiohttp",
    "attrs>=19.1",
    "structlog",
    "orjson",
    "pendulum",
    "prance[osv,icu,cli]",
]
extras_require = {
    "tests": [
        "pytest>=4.6",
        "pytest-cov>=^2.7,<3.0",
        "pytest-asyncio>=0.11.0",
        "pytest-benchmark>=3.2.2<4.0",
        "mock>=3.0<4.0",
        "pytest-mock>=1.10<2.0",
        "pytest-watch>=4.2<5.0",
        "pytest-randomly>=3.1<4.0",
        "pytest-doctestplus>=0.5<1.0",
        "pytest-aiohttp",
        "pytest-anything",
        "pdbpp",
    ],
}
extras_require["all"] = list(itertools.chain(extras_require.values()))
entry_points = {"pytest11": ["buvar_aiohttp = buvar_aiohttp.testing"]}

setup_kwargs = {
    "name": "buvar_aiohttp",
    "version": "0.2.0",
    "description": "Asyncio plugin for buvar",
    "long_description": description,
    "long_description_content_type": "text/x-rst",
    "author": "Oliver Berger",
    "author_email": "diefans@gmail.com",
    "url": "https://gitlab.com/diefans/buvar",
    "package_dir": {"": "src"},
    "packages": find_packages("src"),
    "include_package_data": True,
    # "package_data": {"": ["*"]},
    "install_requires": install_requires,
    "extras_require": extras_require,
    "entry_points": entry_points,
    "python_requires": ">=3.7,<4.0",
    "classifiers": [
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Framework :: AsyncIO",
        "License :: OSI Approved :: Apache Software License",
        "License :: OSI Approved :: MIT License",
    ],
}
setup(**setup_kwargs)
