from setuptools import setup, find_packages

setup(
    name="oracle-focus-agent",
    version="1.0.0",
    description="Oracle FOCUS to Umbrella BYOD Transfer Agent",
    author="David O",
    packages=find_packages(),
    install_requires=[
        "oci>=2.100.0",
        "boto3>=1.26.0",
        "PyYAML>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "oracle-focus-agent=oracle_focus_agent.cli:main",
        ],
    },
    python_requires=">=3.8",
)
