# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('c:\\Users\\RedBlack-PC\\Desktop\\OnnNotaFiscalEletronica\\SimpleNFE/ui', 'ui'), ('c:\\Users\\RedBlack-PC\\Desktop\\OnnNotaFiscalEletronica\\SimpleNFE/modules', 'modules')]
binaries = []
hiddenimports = ['tkinter', 'email', 'imaplib', 'xml.etree.ElementTree', 'PyPDF2', 'pdfminer', 'pdfminer.high_level', 'requests']
tmp_ret = collect_all('tkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['c:\\Users\\RedBlack-PC\\Desktop\\OnnNotaFiscalEletronica\\SimpleNFE/app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SimpleNFE',
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
    icon='NONE',
)
