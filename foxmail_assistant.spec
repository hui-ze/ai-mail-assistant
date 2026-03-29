# -*- mode: python ; coding: utf-8 -*-
# 邮件智能助手 - PyInstaller 打包配置

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # 包含资源文件
        ('assets', 'assets'),
    ],
    hiddenimports=[
        # PyQt5 相关
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        # 邮件相关
        'imaplib',
        'email',
        'email.mime',
        'email.mime.text',
        'email.mime.multipart',
        'imapclient',
        'chardet',
        # 数据库
        'sqlite3',
        # 加密
        'cryptography',
        'cryptography.fernet',
        # AI 相关
        'requests',
        'urllib3',
        'certifi',
        # 通知
        'plyer',
        'plyer.platforms.win.notification',
        # 日历
        'win32com',
        'win32com.client',
        # 标准库
        'json',
        'logging',
        'threading',
        'queue',
        'datetime',
        'pathlib',
        're',
        'os',
        'sys',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'test',
        'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='邮件智能助手',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 不显示命令行窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icons/app.ico',
    version_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='邮件智能助手',
)
