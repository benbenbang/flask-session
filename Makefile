.EXPORT_ALL_VARIABLES:
# customized
PY_CACHE_DIR = `find . -type d -name __pycache__`
# sphinx doc
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SPINXAUTODOC  ?= sphinx-apidoc
SOURCEDIR     = docs/source
BUILDDIR      = docs/build

# ------------------------------------
# Customized func / var define
# ------------------------------------

ifeq (,$(shell which poetry))
HAS_POETRY=False
else
HAS_POETRY=True
endif

define cleanPyCache
@while read pyCD; \
do \
	if [ -n "$$pyCD" ]; then \
		rm -r $$pyCD; \
	fi \
done <<< $(PY_CACHE_DIR)
endef

# ------------------------------------
# Build package
# ------------------------------------

.PHONY: build_pkg
build_pkg:
	@echo "Start to build pkg"
ifeq (True,$(HAS_POETRY))
	@poetry version $(shell git describe --tags --abbrev=0);\
	poetry build
else
	echo "To build the package, you need to have poetry first"
	exit 1
endif

.PHONY: clean
## Remove cache and *.egg-info directories after build or installation
clean:
	@-rm -r dist
	@-$(call cleanPyCache)

clean-pyc:
	@-find . -name '*.pyc' -exec rm -f {} +
	@-find . -name '*.pyo' -exec rm -f {} +
	@-find . -name '*~' -exec rm -f {} +

.PHONY: build
## Clean up cache from previous built, and build the package
build: clean clean-pyc build_pkg

# ------------------------------------
# Build doc
# ------------------------------------

.PHONY: sphinx
## Show sphinx helps
sphinx:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: autodoc
## Clean up bulit docs and build api doc
autodoc:
	@-mkdir -p docs/source/_static
	@-cd docs/source; \
	find -f *.rst ! -name index.rst -delete; \
	cd -
	@$(SPINXAUTODOC) -f -o docs/source ./ ./tests/* ./datamodel/*

.PHONY: html
## Build html files
html:
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: clean_rst
## Clean rst files
clean_rst:
	@-cd docs/source; \
	find -f *.rst ! -name index.rst -delete

.PHONY: doc
## Clean up previous built, run autodoc and build html files
doc: clean autodoc html

# ------------------------------------
# Default
# ------------------------------------

.DEFAULT_GOAL := help

help:
	@echo "$$(tput bold)Available rules:$$(tput sgr0)"
	@echo
	@sed -n -e "/^## / { \
		h; \
		s/.*//; \
		:doc" \
		-e "H; \
		n; \
		s/^## //; \
		t doc" \
		-e "s/:.*//; \
		G; \
		s/\\n## /---/; \
		s/\\n/ /g; \
		p; \
	}" ${MAKEFILE_LIST} \
	| LC_ALL='C' sort --ignore-case \
	| awk -F '---' \
		-v ncol=$$(tput cols) \
		-v indent=19 \
		-v col_on="$$(tput setaf 6)" \
		-v col_off="$$(tput sgr0)" \
	'{ \
		printf "%s%*s%s ", col_on, -indent, $$1, col_off; \
		n = split($$2, words, " "); \
		line_length = ncol - indent; \
		for (i = 1; i <= n; i++) { \
			line_length -= length(words[i]) + 1; \
			if (line_length <= 0) { \
				line_length = ncol - indent - length(words[i]) - 1; \
				printf "\n%*s ", -indent, " "; \
			} \
			printf "%s ", words[i]; \
		} \
		printf "\n"; \
	}' \
	| more $(shell test $(shell uname) = Darwin && echo '--no-init --raw-control-chars')
