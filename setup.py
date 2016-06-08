from setuptools import setup, find_packages

setup(
    name='hydrogen',
    version='0.0.1-alpha',
    description='Hydrogen',
    url='http://github.com/yowtzu/hydrogen',
    author='Yow Tzu Lim',
    author_email='yowtzu.lim@gmail.com',
    packages=find_packages(),
    license='BSD',
    long_description=open('README.md').read(),
    tests_requires=['nose'],
    test_suite='nose.collector',
    include_package_data=True
)
