import setuptools

from shippy.constants import VERSION_STRING

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="shippy",
    version=VERSION_STRING,
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
    packages=setuptools.find_packages(exclude=("tests",)),
    python_requires=">=3.6",
    install_requires=["clint", "requests", "requests-toolbelt", "sentry-sdk"],
)