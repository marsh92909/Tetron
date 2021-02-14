# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['tetron.py'],
             pathex=['C:\\Users\\Marshall\\Desktop\\Tetron'],
             binaries=[],
             datas=[
                 ('C:\\Users\\Marshall\\Desktop\\Tetron\\Sounds\\*.ogg', '.\\Sounds'),
                 ('C:\\Users\\Marshall\\Desktop\\Tetron\\Sounds\\*.wav', '.\\Sounds'),
                 ('C:\\Users\\Marshall\\Desktop\\Tetron\\*.png', '.'),
                 ('C:\\Users\\Marshall\\Desktop\\Tetron\\*.ico', '.')
                 ],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='Tetron',
          debug=True,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          icon='icon.ico')
