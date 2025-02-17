from setuptools import setup, find_packages

setup(
    name="async-ebpf-agent",
    version="0.1.0",
    description="Async eBPF agent to track process executions and system metrics",
    author="Your Name",
    author_email="your.email@example.com",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "sqlalchemy[asyncio]>=2.0",
        "aiosqlite>=0.18.0",
        "pydantic>=2.0",
        "toml>=0.10.2",
        "asyncio>=3.4.3",
        "psutil=6.1.1",
        "matplotlib=3.10.0",
        "python-dotenv=1.0.1",
        "pyarrow=19.0.0",
        "duckdb=1.2.0"
    ],
    extras_require={
        "dev": ["pytest>=7.0", "pytest-asyncio>=0.21.0"]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "async-ebpf-agent=main:main",
        ],
    },
)
