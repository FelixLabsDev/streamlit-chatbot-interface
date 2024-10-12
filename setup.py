from setuptools import setup, find_packages

setup(
<<<<<<< Updated upstream
    name="chatbot_view",
    version="0.1",
    packages=find_packages(),
=======
    name="streamlit_view",
    version="1.0.5",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
>>>>>>> Stashed changes
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
