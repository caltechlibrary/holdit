# =============================================================================
# @file    Makefile
# @brief   Makefile for some steps in creating a Holdit! application
# @author  Michael Hucka
# @date    2018-09-13
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/holdit
# =============================================================================

# Variables.

release	   := $(shell egrep 'version.*=' holdit/__version__.py | awk '{print $$3}' | tr -d "'")
platform   := $(shell python3 -c 'import sys; print(sys.platform)')
distro	   := $(shell python3 -c 'import platform; print(platform.dist()[0].lower())')
linux_vers := $(shell python3 -c 'import platform; print(platform.dist()[1].lower())' | cut -f1-2 -d'.')
macos_vers := $(shell sw_vers -productVersion 2>/dev/null | cut -f1-2 -d'.' || true)
github-css := dev/github-css/github-markdown-css.html

# Main build targets.

build: | dependencies build-$(platform)

# Platform-specific instructions.

build-darwin: dist/Holdit.app ABOUT.html # NEWS.html
#	packagesbuild dev/installer-builders/macos/packages-config/Holdit.pkgproj
#	mv dist/Holdit-mac.pkg dist/Holdit-$(release)-macos-$(macos_vers).pkg 

build-linux: dist/holdit
	(cd dist; tar czf Holdit-$(release)-$(distro)-$(linux_vers).tar.gz holdit)

dist/Holdit.app:
	pyinstaller --clean pyinstaller-$(platform).spec
	sed -i '' -e 's/0.0.0/$(release)/' dist/Holdit.app/Contents/Info.plist
	rm -f dist/Holdit.app/Contents/Info.plist.bak

dist/holdit dist/Holdit.exe:
	pyinstaller --clean pyinstaller-$(platform).spec

dependencies:;
	pip3 install -r requirements.txt

# Component files placed in the installers.

ABOUT.html: README.md
	pandoc --standalone --quiet -f gfm -H $(github-css) -o README.html README.md
	inliner -n < README.html > ABOUT.html

NEWS.html: NEWS.md
	pandoc --standalone --quiet -f gfm -H $(github-css) -o NEWS.html NEWS.md
	inliner -n < NEWS.html > NEWS-inlined.html
	mv NEWS-inlined.html NEWS.html

# Miscellaneous directives.

clean: clean-dist clean-html

clean-dist:;
	-rm -fr dist/Holdit.app dist/holdit dist/holdit.exe build

clean-html:;
	-rm -fr ABOUT.html NEWS.html

.PHONY: html clean clean-dist clean-html
