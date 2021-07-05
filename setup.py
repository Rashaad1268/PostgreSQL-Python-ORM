import setuptools
import pathlib

# The text of the README file
README = pathlib.Path(r"C:\Users\Rushda Niyas\Desktop\Rashaad\Programming\postgres_orm\Readme.md").read_text()

# This call to setup() does all the work
setuptools.setup(
    name="pg_orm",
    version="0.5.1",
    description="An ORM for PostgreSQL",
    long_description=README,
    packages=setuptools.find_packages(),
    long_description_content_type="text/markdown",
    url="https://github.com/Rashaad1268/PostgreSQL-Python-ORM",
    author="Rashaad",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
    ],
    include_package_data=True,
    install_requires=["psycopg2", "asyncpg"],
)
