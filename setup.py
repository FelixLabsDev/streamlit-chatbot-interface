from setuptools import setup, find_packages

setup(
    name="chatbot_view",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "streamlit",
        "openai",
        "python-dotenv",
    ],
)
