from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="agent-oci-to-umbrella",
    version="1.0.0",
    description="OCI to Umbrella BYOD Transfer Agent",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="David O",
    url="https://github.com/pileus-cloud/agent-oci-to-umbrella",
    packages=find_packages(),
    install_requires=[
        "oci>=2.100.0",
        "boto3>=1.26.0",
        "PyYAML>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "agent-oci-to-umbrella=agent_oci_to_umbrella.cli:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Monitoring",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: POSIX :: Linux",
    ],
)
