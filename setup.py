import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mussels",
    version="0.0.1",
    author="Micah Snyder",
    author_email="micasnyd@cisco.com",
    copyright="Copyright (C) 2019 Cisco Systems, Inc. and/or its affiliates. All rights reserved.",
    description="Mussels Build System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Cisco-Talos/mussels",
    packages=setuptools.find_packages(),
    entry_points={"console_scripts": ["mussels = mussels.main:cli"]},
    install_requires=[
        "click>=7.0",
        "coloredlogs>=10.0",
        "requests",
        "patch",
        "gitpython",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache 2.0 License",
        "Operating System :: OS Independent",
    ],
)
