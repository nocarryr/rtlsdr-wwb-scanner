from setuptools import setup

setup(
    entry_points={
        'console_scripts':[
            'wwb_scanner-ui = wwb_scanner.ui.pyside.main:run',
        ],
    },
)
