from setuptools import setup, find_packages

setup(
    name='rustsgxgen',
    version='0.1',
    packages=find_packages(),
    install_requires=['toml', 'colorlog'],
    entry_points={
        'console_scripts': ['rust-sgx-gen = rustsgxgen.generator:__main']
    },
    include_package_data=True,
    author='Gianluca Scopelliti',
    author_email='gianlu.1033@gmail.com'
)
