import setuptools
from os.path import join, dirname

with open(join(dirname(__file__), 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(
    name='credit_semaphore',
    version='0.1.2',
    description='Asynchronous Semaphore Based on Credits for Efficient Credit-Based API Throttling',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='HangukQuant',
    license_files = ('license.txt',),
    url="https://github.com/hangukquant/credit_semaphore",
    download_url="https://pypi.org/project/credit-semaphore/",
    install_requires=[
        'opencv-python'
    ],
    author_email='',
    packages=setuptools.find_packages()
)