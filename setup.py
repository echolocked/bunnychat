from setuptools import setup, find_packages

setup(
    name="bunnychat",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "openai>=1.59.8",
        "python-dotenv>=1.0.0",
        "flask>=3.0.0",
        "markdown>=3.5.0",
        "pygments>=2.17.0",  # For code highlighting
    ],
    entry_points={
        'console_scripts': [
            'bunnychat=src.main:main',
            'bunnychat-web=src.web.app:main',
        ],
    },
) 