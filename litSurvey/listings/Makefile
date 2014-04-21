### Makefile ---
#
# This file generates files required to use the listings package.
#
# $Id: Makefile 127 2014-03-04 19:54:08Z j_hoffmann $
#
# (c) 2007 Brooks Moses
# (c) 2013 Jobst Hoffmann
#
# This file is distributed under the terms of the LaTeX Project Public
# License from CTAN archives in directory  macros/latex/base/lppl.txt.
# Either version 1.3 or, at your option, any later version.

# remember:
# $<: first element of list of dependees
# $^: list of (all) dependees
# $@: target

# formatting tools
LATEX = pdflatex
MAKEINDEX = makeindex
TEX = tex
# tarring options
ifneq "$(wildcard listings.version)" ""
include listings.version        # version and date of the package
endif
TAR_SRC = $(PACKAGE)-$(VERSION)_source.tar.gz
EXsvn = --exclude .svn --exclude auto --exclude contrib --exclude requests \
	--exclude support --exclude testing \
	--exclude *.gz --exclude *.txt

DISTRIBUTION_FILES = $(PACKAGE).pdf $(PACKAGE).dtx \
	$(PACKAGE).ins README Makefile \
	lstdrvrs.dtx lstdrvrs.ins lstdrvrs.pdf 


.SUFFIXES:                              # Delete the default suffixes
.SUFFIXES: .dtx .ins .pdf .sty          # Define our own suffix list

.PHONY: listings pdf pdf-devel tests all

listings: listings.sty

pdf: listings.pdf lstdrvrs.pdf

pdf-devel: listings-devel.pdf

all: listings pdf pdf-devel


listings.sty: listings.ins listings.dtx lstdrvrs.dtx
	$(TEX) $<

listings.pdf: listings.sty
	rm -f ltxdoc.cfg
	$(LATEX) ${<:.sty=.dtx}
	$(MAKEINDEX) -s gind.ist ${@:.pdf=}
	$(LATEX) ${<:.sty=.dtx}
	$(LATEX) ${<:.sty=.dtx}

listings-devel.pdf: listings.sty
	rm -rf ltxdoc.cfg
	echo "\AtBeginDocument{\AlsoImplementation}" > ltxdoc.cfg
	$(LATEX) -jobname=${@:.pdf=} ${<:.sty=.dtx}
	$(MAKEINDEX) -s gind.ist ${@:.pdf=}
	$(LATEX) -jobname=${@:.pdf=} ${<:.sty=.dtx}
	$(LATEX) -jobname=${@:.pdf=} ${<:.sty=.dtx}
	rm -rf ltxdoc.cfg

lstdrvrs.pdf: lstdrvrs.dtx
	rm -f ltxdoc.cfg
	$(LATEX) ${<:.sty=.dtx}
	$(MAKEINDEX) -s gind.ist lstdrvrs
	$(LATEX) ${<:.sty=.dtx}
	$(LATEX) ${<:.sty=.dtx}

## Testing targets
acm-tests:
	cd testing; make acm

fortran-tests:
	cd testing; make fortran

gap-tests:
	cd testing; make gap

hansl-tests:
	cd testing; make hansl

llvm-tests:
	cd testing; make llvm

lua-tests:
	cd testing; make lua

vbscript-tests:
	cd testing; make vbscript

tests:
	cd testing; make all

## Clean targets
clean:
	-rm -f  *~ *.aux *.lof *.log *.lot *.tmp *.toc
	-rm -f *.idx *.ind *.glg *.glo *.gls *.ilg *.out
	-rm -f *.bbl *.blg *.brf

clean-results:
	-rm -f *.cfg *.pdf *.prf *.sty

realclean:  clean clean-results

### create packed files
tar-src:
	@$(MAKE) realclean; \
	sed -i -e "s+fileversion{[a-z0-9\.\-]*}+fileversion{$(VERSION)}+g" \
	    -e "s+filedate{[0-9/]*}+filedate{$(DATE)}+g" \
	    -e "s+date{[0-9/]*\\\\enspace+date{$(DATE)\\\\enspace+g" \
	    -e "s+Version [a-z0-9\.\-]*\\\\+Version $(VERSION)\\\\+g" \
		listings.dtx; \
	sed -i -e "s+date{[0-9/]*\\\\enspace+date{$(DATE)\\\\enspace+g" \
	    -e "s+Version [a-z0-9\.\-]*\\\\+Version $(VERSION)\\\\+g" \
	    -e "s+\[[0-9/]* [a-z0-9\.\-]* listings+[$(DATE) $(VERSION) listings+g" \
		lstdrvrs.dtx; \
	cd ..; tar $(EXsvn) -czvf $(PACKAGE)/$(TAR_SRC) $(PACKAGE)

tar-dist: $(DISTRIBUTION_FILES)
	@$(MAKE) realclean; \
	sed -i -e "s+fileversion{[a-z0-9\.\-]*}+fileversion{$(VERSION)}+g" \
	    -e "s+filedate{[0-9/]*}+filedate{$(DATE)}+g" \
	    -e "s+date{[0-9/]*\\\\enspace+date{$(DATE)\\\\enspace+g" \
	    -e "s+Version [a-z0-9\.\-]*\\\\+Version $(VERSION)\\\\+g" \
		listings.dtx; \
	sed -i -e "s+date{[0-9/]*\\\\enspace+date{$(DATE)\\\\enspace+g" \
	    -e "s+Version [a-z0-9\.\-]*\\\\+Version $(VERSION)\\\\+g" \
	    -e "s+\[[0-9/]* [a-z0-9\.\-]* listings+[$(DATE) $(VERSION) listings+g" \
		lstdrvrs.dtx; \
	$(MAKE) listings.pdf; \
	$(MAKE) lstdrvrs.pdf; \
	tar cfvz $(PACKAGE)-$(VERSION).tgz $^;

## Documentation target
help::
	$(info Usage:)
	$(info )
	$(info make [all]	generates listings.sty and [all] the .pdf versions)
	$(info $(empty)		(user/developer) of the documentation)
	$(info )
	$(info make <file name>)
	$(info $(empty)		creates the corresponding file denoted by <file name>)
	$(info )
	$(info make help	shows this help)
	$(info )
	$(info make tests	performs a little test suite)
	$(info )
	$(info make clean	removes all intermediate files created by a LaTeX run)
	$(info )
	$(info make clean-results)
	$(info $(empty)		removes .cfg, .sty, and .pdf files)
	$(info )
	$(info make realclean)
	$(info $(empty)		performs clean and clean-results)
	$(info )
	$(info make tar-src)
	$(info $(empty)		generates a tarred version of the current directory)
	$(info )
	$(info make tar-dist)
	$(info $(empty)		generates a distributable version of the listings)
	$(info $(empty)		package)
	@echo ""					# prevents message "nothing to do ..."

### Makefile ends here ---
