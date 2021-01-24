# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['tetron.py'],
             pathex=['C:\\Users\\Marshall Lee\\Desktop\\Tetron'],
             binaries=[],
             datas=[
                 ('C:\\Users\\Marshall Lee\\Desktop\\Tetron\\Sounds\\*.mp3', '.'),
                 ('C:\\Users\\Marshall Lee\\Desktop\\Tetron\\Sounds\\*.wav', '.'),
                 ('C:\\Users\\Marshall Lee\\Desktop\\Tetron\\*.png', '.'),
                 ('C:\\Users\\Marshall Lee\\Desktop\\Tetron\\*.ico', '.')
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
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False )
