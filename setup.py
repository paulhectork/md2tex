from setuptools import setup, find_packages

setup(
    name="md2tex",
    version="0.1.0",
    author="Paul, Hector Kervegan",
    license="GNU GPL-3.0 license",
    summary="a python CLI to convert markdown to latex",
    description="a simple and customizable markdown to (la)tex command line interface conversion tool ",
    home_page="https://github.com/paulhectork/md2tex",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["click==8.1.3"],
    entry_points={
        "console_scripts": [
            "md2tex=md2tex:md2tex"
        ]
    }
)
