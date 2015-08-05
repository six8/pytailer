from distutils.core import setup


setup(
    name='tailer',
    packages=['tailer'],
    package_dir={'': 'src'},
    version=open('VERSION.txt').read().strip(),
    author='Mike Thornton',
    author_email='six8@devdetails.com',
    url='http://github.com/six8/pytailer',
    download_url='http://github.com/six8/pytailer',
    license='MIT',
    keywords=['tail', 'head'],
    description='Python tail is a simple implementation of GNU tail and head.',
    classifiers=[
        "Programming Language :: Python",
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Operating System :: POSIX",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        'Topic :: System :: Logging',
        'Topic :: Text Processing',
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: System Shells",
        "Topic :: System :: Systems Administration",
    ],
    long_description=open('README.rst').read(),
    entry_points={
        'console_scripts': [
            'pytail = tailer:main',
        ],
    },
)
