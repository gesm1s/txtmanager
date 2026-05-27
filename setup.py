from setuptools import setup

APP = ["teksterstatning_gui.py"]
OPTIONS = {
    "iconfile": "Txtmanager.icns",
    "plist": {
        "CFBundleName": "Txtmanager",
        "CFBundleDisplayName": "Txtmanager",
        "CFBundleIdentifier": "com.gesm.txtmanager",
        "CFBundleVersion": "1.4.8",
        "CFBundleShortVersionString": "1.4.8",
        "LSMinimumSystemVersion": "15.0",
    },
}

setup(
    app=APP,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
