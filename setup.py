import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mussels",
    version="0.1.0",
    author="Micah Snyder",
    author_email="micasnyd@cisco.com",
    copyright="Copyright (C) 2019 Cisco Systems, Inc. and/or its affiliates. All rights reserved.",
    description="Mussels Build System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Cisco-Talos/mussels",
    packages=setuptools.find_packages(),
    entry_points={
        "console_scripts": [
            "mussels = mussels.__main__:cli",
            "msl = mussels.__main__:cli",
        ]
    },
    install_requires=[
        "click>=7.0",
        "coloredlogs>=10.0",
        "colorama",
        "requests",
        "patch",
        "gitpython",
        "pyyaml",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
