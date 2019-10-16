from setuptools import setup, find_packages


with open("README.md") as f:
    LONG_DESCRIPTION = f.read()


setup(
    name="netviel",
    version="0.1.1",
    author="David M. Straub <straub@protonmail.com>",
    author_email="straub@protonmail.com",
    url='https://github.com/DavidMStraub/netviel',
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=find_packages(),
    install_requires=["flask", "flask-restful", "flask-cors", "bleach"],
)
