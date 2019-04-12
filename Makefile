# =============================================================================
# @file    Makefile
# @brief   Linux & OSX makefile to help create a Hold It! application
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

about-file := ABOUT.html
help-file  := holdit/data/help.html

# Main build targets.

build: | dependencies build-$(platform)

# Platform-specific instructions.
#
# Note: I wanted to name the application file with a space ("Hold It"), but
# it turns out to be ridiculously complicated to get GNU make to handle
# spaces in file names used in shell commands.  (I.e., it's okay to have a
# target with an escaped space in this Makefile, but you have to do batshit
# insane hacks to refer to file names when you write the actions.  See for
# example https://stackoverflow.com/q/35617602/743730) So I gave up and
# called the executable HoldIt.

build-darwin: dist/HoldIt.app $(about-file) $(help-file) # NEWS.html

build-linux: dist/HoldIt
	(cd dist; tar czf HoldIt-$(release)-$(distro)-$(linux_vers).tar.gz holdit)

dist/HoldIt.app: $(help-file) $(about-file)
	pyinstaller --clean pyinstaller-$(platform).spec
	sed -i '' -e 's/0.0.0/$(release)/' 'dist/HoldIt.app/Contents/Info.plist'
	rm -f 'dist/HoldIt.app/Contents/Info.plist.bak'
	rm -f dist/holdit

dist/holdit dist/HoldIt.exe:
	pyinstaller --clean pyinstaller-$(platform).spec

dependencies:;
	pip3 install -r requirements.txt

# Component files placed in the installers.

$(about-file): README.md
	pandoc --standalone --quiet -f gfm -H $(github-css) -o README.html README.md
	inliner -n < README.html > ABOUT.html
	rm -f README.html

$(help-file): holdit/data/help.md
	pandoc --standalone --quiet -f gfm -H $(github-css) -o help-tmp.html $<
	inliner -n < help-tmp.html > $@
	rm -f help-tmp.html

NEWS.html: NEWS.md
	pandoc --standalone --quiet -f gfm -H $(github-css) -o NEWS.html NEWS.md
	inliner -n < NEWS.html > NEWS-inlined.html
	mv NEWS-inlined.html NEWS.html

# Miscellaneous directives.

clean: clean-dist clean-html

clean-dist:;
	-rm -fr dist/HoldIt.app dist/holdit dist/holdit.exe build

clean-html:;
	-rm -fr ABOUT.html NEWS.html

.PHONY: html clean clean-dist clean-html
