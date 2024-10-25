from setuptools import setup, find_packages

setup(
    name="streamlit_view",
    version="1.1.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "streamlit",
        "openai",
        "python-dotenv",
    ],
    entry_points={
        'console_scripts': [
            'streamlit-chat-ui=streamlit_view.streamlit_chat_ui:main',
        ],
    },
)
