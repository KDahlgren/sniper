# based on https://github.com/KDahlgren/pyLDFI/blob/master/Makefile

all: deps

deps: get-submodules orik

clean:
	rm -r lib/orik

cleanorik:
	rm -r lib/orik

orik:
	cd lib/orik ; python setup.py ;

get-submodules:
	git submodule init
	git submodule update
