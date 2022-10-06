import setuptools

setuptools.setup(
    name='credit_semaphore',
    version='0.0.7',
    description='Asynchronous Semaphore Based on Credits for Efficient Credit-Based API Throttling',
    author='HangukQuant',
    install_requires=[
        'opencv-python'
    ],
    author_email='',
    packages=setuptools.find_packages()
)