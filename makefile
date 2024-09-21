bump_patch:
	source ./bump.awk > new_version.py && mv new_version.py version.py

package:
	rm -rf build && python3 package_setup.py clean && python3 package_setup.py bdist_wheel

install:
	pip3 install dist/`ls -1t dist/|head -1` --force-reinstall --upgrade --no-deps

