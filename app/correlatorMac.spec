# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['correlator.py'],
    pathex=[],
    binaries=[],
    datas=[('images/*', 'images'), ('icons/*', 'icons'), ('tmp/*', 'tmp')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Correlator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icons/correlator.icns'],
)
app = BUNDLE(
    exe,
    name='Correlator.app',
    icon='icons/correlator.icns',
    bundle_identifier=None,
    version='4.5.3'
)
