from setuptools import setup, find_packages

setup(
        author='Ana Nelson',
        author_email='ana@ananelson.com',
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Environment :: Console",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: BSD License",
            "Topic :: Office/Business :: Groupware",
            ],
        description='Quickbooks import utilities',
        install_requires = [
            'python-quickbooks',
            'stripe'
            ],
        name='quickbats',
        url='https://improv.org',
        packages=find_packages(),
        version='0.0.1.0'
    )
