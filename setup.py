import glob
import os

from setuptools import find_packages, setup


with open("README.md") as f:
    LONG_DESCRIPTION = f.read()


PACKAGE_DATA = [p[8:] for p in glob.glob("netviel/js/**/*", recursive=True)]
PACKAGE_DATA = [f for f in PACKAGE_DATA if os.path.isfile(os.path.join("netviel", f))]


setup(
    name="netviel",
    version="0.2",
    author="David M. Straub <straub@protonmail.com>",
    author_email="straub@protonmail.com",
    url="https://github.com/DavidMStraub/netviel",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=find_packages(),
    package_data={"netviel": PACKAGE_DATA},
    install_requires=["flask", "flask-restful", "bleach"],
)
