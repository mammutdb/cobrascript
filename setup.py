# -*- coding: utf-8 -*-

from setuptools import setup

setup(name='cobrascript',
      description='Python syntax translator to Javascript.',
      long_description='Python syntax translator to Javascript.',
      version='0.1.2',
      url='https://github.com/niwibe/cobrascript',
      license='BSD License',
      platforms=['unix', 'linux', 'osx', 'cygwin', 'win32'],
      author='Andrey Antukh',
      author_email='niwi@niwi.be',
      entry_points={"console_scripts": ["cobrascript = cobra.base:main"]},
      classifiers=['Development Status :: 3 - Alpha',
                   'Intended Audience :: Developers',
                   'Environment :: Console',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: POSIX',
                   'Operating System :: Microsoft :: Windows',
                   'Operating System :: MacOS :: MacOS X',
                   'Topic :: Software Development :: Libraries',
                   'Topic :: Utilities',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.3',],
      install_requires=[],
      packages=['cobra'],
      zip_safe=False)
