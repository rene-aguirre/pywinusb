import os
try:
    from setuptools import setup, find_packages
except ImportError:
    import sys
    from distutils.core import setup
    print "The Setuptools package is not in your Python packages path.\n" \
            "As an alternative copy the ./pywinusb sub-folder content to your " \
            "Python packages path (i.e. C:\Python26\Lib\site\packages\)"
    sys.exit(1)
VERSION = '0.2.9'
README = os.path.join(os.path.dirname(__file__), 'README.txt')
CHANGES = os.path.join(os.path.dirname(__file__), 'CHANGES.txt')
long_description = open(README).read() + open(CHANGES).read() + 'nn'
setup(name='pywinusb',
      version = VERSION,
      description=("A package that simplifies USB/HID communications on windows"),
      long_description=long_description,
      classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Win32 (MS Windows)",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "License :: OSI Approved :: BSD License",
        "Topic :: System :: Hardware",
        "Topic :: System :: Hardware :: Hardware Drivers",
        "Topic :: Scientific/Engineering :: Human Machine Interfaces",
        "Topic :: Software Development :: Embedded Systems",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
        "Intended Audience :: Developers",
        ],
      keywords='hid usb usages',
      author='Rene F. Aguirre',
      author_email='rene.f.aguirre@gmail.com',
      url='http://code.google.com/p/pywinusb',
      license='BSD',
      packages=find_packages(),
      package_data = {
          # for all packages
          ''         : ['*.txt', '*.rst', 'examples/*.py'],
          },
      include_package_data = True,
      namespace_packages=['pywinusb']
      )

