# -*- mode: python -*-

block_cipher = None


a = Analysis(['correlator.py'],
             pathex=['/Users/bgrivna/proj/corewall/correlator/app'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='Correlator',
          debug=False,
          strip=False,
          upx=True,
          console=False , icon='icons/correlator.icns')
app = BUNDLE(exe,
             name='Correlator.app',
             icon='icons/correlator.icns',
             bundle_identifier=None)
