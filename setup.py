import sys

from setuptools import setup, find_packages

def convert_readme():
    try:
        import pypandoc
    except ImportError:
        return read_rst()
    rst = pypandoc.convert_file('README.md', 'rst')
    with open('README.rst', 'w') as f:
        f.write(rst)
    return rst

def read_rst():
    try:
        with open('README.rst', 'r') as f:
            rst = f.read()
    except IOError:
        rst = None
    return rst

def get_long_description():
    if {'sdist', 'bdist_wheel'} & set(sys.argv):
        long_description = convert_readme()
    else:
        long_description = read_rst()
    return long_description

setup(
    name = "rtlsdr-wwb-scanner",
    version = "0.0.1",
    author = "Matthew Reid",
    author_email = "matt@nomadic-recording.com",
    url='https://github.com/nocarryr/rtlsdr-wwb-scanner',
    description = "SDR Scanner",
    license='GPLv2',
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    install_requires=[
        'numpy',
        'scipy',
        'pyrtlsdr>=0.2.6',
        'tinydb',
        'json-object-factory',
        'Cython',
        'kivy',
    ],
    setup_requires=['pypandoc'],
    long_description=get_long_description(),
    entry_points={
        'console_scripts':[
            'wwb_scanner-ui = wwb_scanner.ui.kivyui.main:run',
        ],
    },
    platforms=['any'],
    classifiers = [
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
)
