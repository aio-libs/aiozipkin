import os
import re
import sys

from setuptools import find_packages, setup  # type: ignore


if sys.version_info < (3, 6, 0):
    raise RuntimeError("aiozipkin does not support Python earlier than 3.6.0")


def read(f: str) -> str:
    return open(os.path.join(os.path.dirname(__file__), f)).read().strip()


install_requires = ["aiohttp>=3.7.2"]


def read_version() -> str:
    regexp = re.compile(r'^__version__\W*=\W*"([\d.abrc]+)"')
    init_py = os.path.join(os.path.dirname(__file__), "aiozipkin", "__init__.py")
    with open(init_py) as f:
        for line in f:
            match = regexp.match(line)
            if match is not None:
                return match.group(1)
        else:
            msg = "Cannot find version in aiozipkin/__init__.py"
            raise RuntimeError(msg)


classifiers = [
    "License :: OSI Approved :: MIT License",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Operating System :: POSIX",
    "Development Status :: 5 - Production/Stable",
    "Framework :: AsyncIO",
]


setup(
    name="aiozipkin",
    version=read_version(),
    description=(
        "Distributed tracing instrumentation " "for asyncio application with zipkin"
    ),
    long_description="\n\n".join((read("README.rst"), read("CHANGES.rst"))),
    classifiers=classifiers,
    platforms=["POSIX"],
    author="Nikolay Novik",
    author_email="nickolainovik@gmail.com",
    url="https://github.com/aio-libs/aiozipkin",
    download_url="https://pypi.python.org/pypi/aiozipkin",
    license="Apache 2",
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=install_requires,
    keywords=["zipkin", "distributed-tracing", "tracing"],
    zip_safe=True,
    include_package_data=True,
)
