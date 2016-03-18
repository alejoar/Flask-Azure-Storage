"""
Flask-Azure-Storage
-------------
Flask extension that provides integration with Azure Storage.
"""
from setuptools import setup


setup(
    name='Flask-Azure-Storage',
    version='0.1.1',
    url='https://github.com/alejoar/Flask-Azure-Storage',
    license='MIT',
    author='Alejo Arias',
    author_email='alejoar@gmail.com',
    description='Flask extension that provides integration with Azure Storage',
    long_description=__doc__,
    py_modules=['flask_azure_storage'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask',
        'azure-storage'
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
