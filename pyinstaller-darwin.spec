# -*- mode: python -*-
# =============================================================================
# @file    pyinstaller-darwin.spec
# @brief   Spec file for PyInstaller for macOS
# @author  Michael Hucka
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/holdit
# =============================================================================

import imp
import os
import sys

# The list must contain tuples: ('file', 'destination directory').
data_files = [ ('holdit/holdit.ini', 'holdit'),
               ('holdit/data/client_secrets.json', 'holdit/data'),
               ('holdit/data/default_template.docx', 'holdit/data'),
               ('holdit/data/help.html', 'holdit/data') ]

configuration = Analysis(['holdit/__main__.py'],
                         pathex = ['.'],
                         binaries = [],
                         datas = data_files,
                         hiddenimports = ['apiclient'],
                         hookspath = [],
                         runtime_hooks = [],
                         excludes = [],
                         win_no_prefer_redirects = False,
                         win_private_assemblies = False,
                         cipher = None,
                        )

application_pyz    = PYZ(configuration.pure,
                         configuration.zipped_data,
                         cipher = None,
                        )

executable         = EXE(application_pyz,
                         configuration.scripts,
                         configuration.binaries,
                         configuration.zipfiles,
                         configuration.datas,
                         name = 'holdit',
                         debug = True,
                         strip = False,
                         upx = True,
                         runtime_tmpdir = None,
                         console = False,
                        )

app             = BUNDLE(executable,
                         name = 'HoldIt.app',
                         icon = 'dev/icons/holdit.icns',
                         bundle_identifier = None,
                         info_plist = {'NSHighResolutionCapable': 'True'},
                        )
