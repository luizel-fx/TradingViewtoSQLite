from setuptools import setup, find_packages

setup(
    name="tradingview-to-sqlite",
    version="0.1.0",
    author="Luiz E. Lima",
    description="Scrape TradingView futures price data and persist to a local SQLite database.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/luizel-fx/TradingViewtoSQLite",
    packages=find_packages(include=["tradingview_to_sqlite", "tradingview_to_sqlite.*"]),
    python_requires=">=3.9",
    install_requires=[
        "pandas",
        "numpy",
        "SQLAlchemy",
        "requests",
        "websocket-client",
        "price-loaders @ git+https://github.com/batprem/price-loaders.git@fix/default-return-data-to-numerical",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
