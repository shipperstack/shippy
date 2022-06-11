from setuptools import setup, find_packages
from distutils.util import convert_path

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read version file
main_ns = {}
ver_path = convert_path("shippy/version.py")
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)

setup(
    name="shipper-shippy",
    version=main_ns["__version__"],
    author="Eric Park",
    author_email="me@ericswpark.com",
    description="Client-side tool to interface with shipper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ericswpark/shippy",
    project_urls={
        "Bug Tracker": "https://github.com/ericswpark/shippy/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=("tests",)),
    python_requires=">=3.7",
    install_requires=[
        "requests",
        "semver",
        "sentry-sdk",
        "humanize",
        "rich",
    ],
    entry_points={
        "console_scripts": [
            "shippy=shippy.__main__:main",
        ]
    },
    include_package_data=False,
)
