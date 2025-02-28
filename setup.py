from setuptools import setup, find_packages

setup(
    name="bunnychat",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "openai>=1.59.8",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        'console_scripts': [
            'bunnychat=src.main:main',
        ],
    },
) 