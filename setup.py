#!/usr/bin/python

from distutils.core import setup

setup( name = "python-xapp",
       version = "1.0.1",
       description = "Python Xapp Library.",
       maintainer = "Linux Mint",
       maintainer_email = "root@linuxmint.com",
       url = "http://github.com/linuxmint/python-xapp",
       packages = ['xapp', 'xapp.pkgCache'],
       classifiers = [
                "License :: OSI Approved :: GNU Lesser General Public License v2 (LGPLv2)",
                "Programming Language :: Python :: 2.6",
                "Programming Language :: Python :: 2.7",
                "Programming Language :: Python :: 3",
                "Topic :: Desktop Environment",
                ],
     )

