from setuptools import setup, find_packages

setup(
    name="huffman-encode",
    version="0.1",
    packages=find_packages(),
    py_modules=["main"],
    install_requires=[
        "click",
        "bitarray"
    ],
    entry_points={
        "console_scripts": [
            "encode = main:encode",
            "decode = main:decode",
        ],
    },
)