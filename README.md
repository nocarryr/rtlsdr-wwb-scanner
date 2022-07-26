# rtlsdr-wwb-scanner

RF Scanner and Exporter for use with Shure Wireless Workbench

Allows wide-band RF scans to be performed by an inexpensive [RTL-SDR][osmosdr-wiki] device.
The scan data can then be exported as a CSV file formatted for use in WWB.

## Installation

### librtlsdr

The `librtlsdr` library is required and must be installed separately.
Installation documentation for various platforms can be found on the [osmocom wiki][osmosdr-wiki]
and in the [pyrtlsdr project][pyrtlsdr].

### Install via pip

```bash
pip install rtlsdr-wwb-scanner
```

It is recommended however to install into a virtual environment such as
[virtualenv](https://pypi.org/project/virtualenv/) or Python's built-in
[venv](https://docs.python.org/3.8/library/venv.html) module.


```bash
# Create the environment using the built-in venv module
python3 -m venv /path/to/new/virtual/environment

# Activate it using <virtual-environment-path>/bin/activate
source /path/to/new/virtual/environment/bin/activate

# Install rtlsdr-wwb-scanner and its dependencies in the virtual environment
python -m pip install rtlsdr-wwb-scanner
```

*Note* for Windows users: The `bin` directory should be replaced with `Scripts`
making the "activate" command `<virtual-environment-path>/Scripts/activate`


## Dependencies

These packages are required, but should be collected and installed automatically:

* Numpy: https://numpy.org
* Scipy: https://scipy.org/scipylib/index.html
* pyrtlsdr: https://github.com/roger-/pyrtlsdr
* PySide2: https://pypi.org/project/PySide2/

## Usage

After installation, the user interface can be launched by:

```bash
wwb_scanner-ui
```

If a virtual environment was used, it must either be activated (see above) or
the `wwb_scanner-ui` script must be executed by its absolute file name:

```bash
/path/to/new/virtual/environment/bin/wwb_scanner-ui
```

Or for Windows:

```bash
/path/to/new/virtual/environment/Scripts/wwb_scanner-ui
```

For convenience, a shortcut may be created to launch the above script directly.


[osmosdr-wiki]: http://sdr.osmocom.org/trac/wiki/rtl-sdr
[pyrtlsdr]: https://github.com/roger-/pyrtlsdr
[scipy-install]: http://www.scipy.org/install.html
