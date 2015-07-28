# rtlsdr-wwb-scanner

##RF Scanner and Exporter for use with Shure Wireless Workbench

Allows wide-band RF scans to be performed by an inexpensive [RTL-SDR][osmosdr-wiki] device.  The scan data can then be exported as a CSV file formatted for use in WWB.

###Installation

* Download and install *librtlsdr* following the directions [here][osmosdr-wiki]
* Install the python wrapper [pyrtlsdr][pyrtlsdr]
* Install [Kivy](http://kivy.org/#download) and [Kivy Garden](http://kivy-garden.github.io/).
    * After that, you'll need to "garen install" the "filebrowser" and "tickline" packages:
        * `garden install filebrowser`
        * `garden install tickline`

This project relies heavily upon the numpy and scipy libraries.  Installation for those can be found [here][scipy-install].

This project is not yet configured with distutils, so you will either need to download the source tarball or clone the [repository](https://github.com/nocarryr/rtlsdr-wwb-scanner).  Cloning would be recommended as this is still in the early stages of development.

###Usage

Well... at the moment I'm performing all tests, scans, import/export functions, etc manually in the python interpreter so this section will be difficult until main scripts and entry points have been created.  Check back soon!

To use the Kivy interface run the "kivyapp.py" script in the project root.


[osmosdr-wiki]: http://sdr.osmocom.org/trac/wiki/rtl-sdr
[pyrtlsdr]: https://github.com/roger-/pyrtlsdr
[scipy-install]: http://www.scipy.org/install.html
