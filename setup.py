#!/usr/bin/python3
import os
import setuptools
import setuptools.command.build_py

setuptools.setup(
    name='LinMoTube',
    version='1.2',
    description='LinMoTube',
    keywords='youtube',
    author='Jake Day',
    url='https://github.com/jakeday/LinMoTube',
    python_requires='>=3.8',
    install_requires=[
        'youtube-search-python',
        'python-mpv'
    ],
    include_package_data=True,
    data_files=[
        ('/usr/share/icons/hicolor/scalable/apps', ['linmotube/assets/linmotube.png']),
        ('/usr/share/applications', ['linmotube/assets/linmotube.desktop'])
    ],
    package_data={
        "": ["assets/*"]
    },
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'linmotube=linmotube',
        ],
    },
)
