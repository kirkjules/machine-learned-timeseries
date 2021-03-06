from setuptools import setup, find_packages

setup(
    name='htp',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'Requests',
        'Pandas'
    ],
    scripts=["bin/htp"],
    entry_points={
        "console_scripts": [
            "candles=htp.api.scripts.candles:clickData",
            "analyse=htp.analyse.scripts.analyse:clickIndicator"],
    }
)
