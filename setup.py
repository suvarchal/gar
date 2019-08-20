import setuptools

with open('README.rst', 'rt') as fh:
    long_description = fh.read()

setuptools.setup(
    name="gar",
    version="0.0.1",
    author="Suvarchal K. Cheedela",
    author_email="suvarchal.kumar@gmail.com",
    description="Archiving for users and groups",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/suvarchal/gar",
    packages=setuptools.find_packages(),
    python_requires='>=3.3',
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        gar=gar.command_line:cli_copy
    ''',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT",
        "Operating System :: Linux",
    ],
)
