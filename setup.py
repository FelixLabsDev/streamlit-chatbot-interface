from setuptools import setup, find_packages

setup(
    name="streamlit_view",
    version="1.2.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,  # Include non-code files specified in MANIFEST.in (optional)
    install_requires=[
        "streamlit",
        "python-dotenv",
    ],
    entry_points={
        'console_scripts': [
            'streamlit-chat-ui=streamlit_view.streamlit_chat_ui:main',
        ],
    },
)
