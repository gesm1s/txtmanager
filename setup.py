from setuptools import setup

APP = ["teksterstatning_gui.py"]
OPTIONS = {
    "iconfile": "Txtmanager.icns",
    "plist": {
        "CFBundleName": "Txtmanager",
        "CFBundleDisplayName": "Txtmanager",
        "CFBundleIdentifier": "com.gesm.txtmanager",
        "CFBundleVersion": "1.4.1",
        "CFBundleShortVersionString": "1.4.1",
        "LSMinimumSystemVersion": "15.0",
    },
}

setup(
    app=APP,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
