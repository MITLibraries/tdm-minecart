import re
from setuptools import find_packages, setup


with open('LICENSE') as f:
    license = f.read()

with open('requirements.in') as f:
    install_requires = f.read().splitlines()

with open('minecart/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        f.read(), re.MULTILINE).group(1)


setup(
    name='minecart',
    version=version,
    license=license,
    author='Mike Graves',
    author_email='mgraves@mit.edu',
    packages=find_packages(exclude=['tests']),
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'minecart = minecart.cli:main',
        ]
    }
)
