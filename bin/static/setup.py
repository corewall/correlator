"""
A distutils script to make a standalone .exe of superdoodle for
Windows platforms.  You can get py2exe from
http://py2exe.sourceforge.net/.  Use this command to build the .exe
and collect the other needed files:

    python setup.py py2exe

A distutils script to make a standalone .app of superdoodle for
Mac OS X.  You can get py2app from http://undefined.org/python/py2app.
Use this command to build the .app and collect the other needed files:

   python setup.py py2app
"""


####  this is used for building on Windows
####  without this we'll get some ugly looking controls

manifest = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1"
manifestVersion="1.0">
<assemblyIdentity
    version="0.64.1.0"
    processorArchitecture="x86"
    name="Controls"
    type="win32"
/>
<description>CORRELATOR UI</description>
<dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.Windows.Common-Controls"
            version="6.0.0.0"
            processorArchitecture="X86"
            publicKeyToken="6595b64144ccf1df"
            language="*"
        />
    </dependentAssembly>
</dependency>
</assembly>
"""
            
#### end windows crap


VERSION = 1.3
NAME = "Correlator"
DESCRIPTION = "CORRELATOR UI v"+str(VERSION)

from distutils.core import setup, Distribution
import sys, glob, os

#####    MAC   ######
# RUN WITH: python setup.py py2app -a
#
if sys.platform == 'darwin':
    import py2app
    os.system('export DYLD_LIBRARY_PATH=./lib/xerces/:.:$DYLD_LIBRARY_PATH')

    opts = dict(argv_emulation=True,
                   dist_dir="")
    setup(app=['correlator.py'],
          name = NAME,
          options=dict(py2app=opts),
          data_files = [(".", ["libwx_macud-2.8.0.dylib", "libwx_macud_gizmos-2.8.0.dylib", "libcore.dylib", "py_correlator.so", "images", "tmp", "help", "db", "icons", "lib"]),
                        ("images", glob.glob("images\\*.*")), ("db", glob.glob("db\\*.*")), ("tmp", glob.glob("tmp\\*.*")), ("lib", glob.glob("lib\\*.*")), ("icons", glob.glob("icons\\*.*")), ("help", glob.glob("help\\*.*"))],
          )
