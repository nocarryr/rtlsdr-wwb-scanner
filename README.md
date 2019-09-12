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

(Further usage information will be added soon)


[osmosdr-wiki]: http://sdr.osmocom.org/trac/wiki/rtl-sdr
[pyrtlsdr]: https://github.com/roger-/pyrtlsdr
[scipy-install]: http://www.scipy.org/install.html
