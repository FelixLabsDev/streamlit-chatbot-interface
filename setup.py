from setuptools import setup, find_packages

setup(
    name="streamlit_view",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "streamlit",
        "openai",
        "python-dotenv",
    ],
)
