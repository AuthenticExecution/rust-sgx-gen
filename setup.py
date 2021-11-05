import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as f:
    requirements = f.readlines()

setuptools.setup(
    name="rust-sgx-gen",
    version="0.2",
    author="Gianluca Scopelliti",
    author_email="gianlu.1033@gmail.com",
    description="Rust code generator for the Authentic Execution framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gianlu33/rust-sgx-gen",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': ['rust-sgx-gen = rustsgxgen.generator:__main']
    },
    include_package_data=True,
)
