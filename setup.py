import sys
from pathlib import Path

USE_CX_FREEZE = False
if 'cx_freeze' in sys.argv:
    USE_CX_FREEZE = True
    sys.argv.remove('cx_freeze')

if USE_CX_FREEZE:
    from cx_Freeze import setup, Executable
else:
    from setuptools import setup

setup_data = dict(
    entry_points={
        'console_scripts':[
            'wwb_scanner-ui = wwb_scanner.ui.pyside.main:run',
        ],
    },
)

if USE_CX_FREEZE:
    exe_base = None
    if sys.platform == 'win32':
        exe_base = "Win32GUI"
    ui_script_path = Path('.') / 'wwb_scanner' / 'ui' / 'pyside' / 'main.py'
    setup_data['executables'] = [
        Executable(str(ui_script_path), base=exe_base, targetName='rtlsdr-wwb-scanner'),
    ]
    deps = [
        'numpy', 'scipy', 'rtlsdr', 'PySide2',
    ]

    # https://github.com/anthony-tuininga/cx_Freeze/issues/233#issuecomment-348078191
    excludes = ['scipy.spatial.cKDTree']

    setup_data['options'] = {
        'build_exe':{'packages':deps, 'excludes':excludes},
    }

setup(**setup_data)
