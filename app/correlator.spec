# -*- mode: python -*-
a = Analysis(['correlator.py'],
             pathex=['c:\\Users\\bgrivna\\proj\\corewall\\correlator\\app'],
             hiddenimports=[],
             hookspath=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name=os.path.join('dist', 'correlator.exe'),
          icon='icons\\correlator.ico',
          debug=False,
          strip=None,
          upx=True,
          console=False )
