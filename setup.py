from setuptools import setup, find_packages

setup(
    name="streamlit_view",
    version="1.0.2",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "streamlit",
        "openai",
        "python-dotenv",
    ],
)
