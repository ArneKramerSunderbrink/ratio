import io

from setuptools import find_packages
from setuptools import setup

with io.open("README.md", "rt", encoding="utf8") as f:
    readme = f.read()

setup(
    name="ratio",
    version="1.0.0",
    maintainer="Arne Kramer-Sunderbrink",
    maintainer_email="herr-kramer-sunderbrink@t-online.de",
    description="RATIO tool.",
    long_description=readme,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=["flask"],
    extras_require={"test": ["pytest", "coverage"]},
)
