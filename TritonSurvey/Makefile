# Document build (LaTeX) lives under docs/ and does not touch the repo root.
#
# Usage (run inside docs/):
#   make
#   make draft
#   make debug
#   make clean
#   make distclean
#   make SHELL_ESCAPE=1
#   make ENGINE=lualatex
#
# Requirements:
#   - latexmk in PATH (TeX Live / MiKTeX)
#   - GNU Make (on Windows: e.g. MSYS2, Git-Bash, or MinGW make)

TEX_MAIN := TritonSurvey.tex
OUTDIR   := build
ENGINE   := xelatex
SHELL_ESCAPE ?= 0
REPORT_SCRIPT := tools/report.py
REPORT_OUT := $(OUTDIR)/doc-report.txt
REPORT_SECTIONS_OUT := $(OUTDIR)/doc-report-sections.txt

LATEXMK := latexmk

# Pick latexmk engine switch from ENGINE=...
ifeq ($(ENGINE),xelatex)
  ENGINE_FLAG := -xelatex
else ifeq ($(ENGINE),lualatex)
  ENGINE_FLAG := -lualatex
else
  $(error Unsupported ENGINE='$(ENGINE)'. Use ENGINE=xelatex or ENGINE=lualatex)
endif

# latexmk does not have a dedicated -shell-escape flag; use -latexoption instead.
ifeq ($(SHELL_ESCAPE),1)
  SHELL_ESCAPE_FLAG := -latexoption=-shell-escape
else
  SHELL_ESCAPE_FLAG :=
endif

RELEASE_FLAGS := $(ENGINE_FLAG) -outdir=$(OUTDIR) -synctex=1 -file-line-error \
	-interaction=nonstopmode -halt-on-error -silent $(SHELL_ESCAPE_FLAG)

DEBUG_FLAGS := $(ENGINE_FLAG) -outdir=$(OUTDIR) -synctex=1 -file-line-error \
	-interaction=errorstopmode -halt-on-error $(SHELL_ESCAPE_FLAG)

.PHONY: all debug draft clean distclean view

all:
	@mkdir -p $(OUTDIR)
	@sh -c 'set -e; \
		LOG="$(OUTDIR)/latexmk-$${TEX_MAIN%.tex}.log"; \
		START=$$(date +%s); \
		echo "[build] $(TEX_MAIN)  (ENGINE=$(ENGINE), shell-escape=$(SHELL_ESCAPE))"; \
		$(LATEXMK) $(RELEASE_FLAGS) "$(TEX_MAIN)" >"$$LOG" 2>&1; EC=$$?; \
		END=$$(date +%s); ELAPSED=$$((END-START)); \
		RUNS=$$(grep -E "Latexmk: Run number [0-9]+ of rule" "$$LOG" 2>/dev/null | wc -l | tr -d " "); \
		[ -n "$$RUNS" ] || RUNS="?"; \
		if [ "$$EC" -eq 0 ]; then \
			echo "[ok] $(OUTDIR)/$${TEX_MAIN%.tex}.pdf  ($$RUNS runs, $${ELAPSED}s)"; \
			rm -f "$$LOG"; \
			if command -v python >/dev/null 2>&1; then \
				python -B "$(REPORT_SCRIPT)" --main "$(TEX_MAIN)" --out "$(REPORT_OUT)" --out-sections "$(REPORT_SECTIONS_OUT)"; \
			else \
				echo "[report] python not found, skipping"; \
			fi; \
		else \
			echo "[fail] Exit $$EC  ($${ELAPSED}s)"; \
			echo "[fail] See: $$LOG"; \
			exit $$EC; \
		fi' TEX_MAIN="$(TEX_MAIN)"

draft:
	@mkdir -p $(OUTDIR)
	@sh -c 'set -e; \
		COUNT=$$(ls -1 *.tex 2>/dev/null | wc -l | tr -d " "); \
		if [ "$$COUNT" -ne 1 ]; then \
			echo "[fail] Draft mode requires exactly one main .tex in docs/; found $$COUNT."; \
			echo "[fail] Please keep only one top-level .tex file in docs/."; \
			exit 2; \
		fi; \
		MAIN=$$(ls -1 *.tex); \
		BASE=$${MAIN%.tex}; \
		WRAP="$(OUTDIR)/$${BASE}-draft.tex"; \
		printf "\\\\def\\\\TRITONDRAFT{1}\\n\\\\input{../%s}\\n" "$$MAIN" > "$$WRAP"; \
		LOG="$(OUTDIR)/latexmk-$${BASE}-draft.log"; \
		START=$$(date +%s); \
		echo "[build] $$WRAP  (ENGINE=$(ENGINE), shell-escape=$(SHELL_ESCAPE))"; \
		$(LATEXMK) $(RELEASE_FLAGS) "$$WRAP" >"$$LOG" 2>&1; EC=$$?; \
		END=$$(date +%s); ELAPSED=$$((END-START)); \
		RUNS=$$(grep -E "Latexmk: Run number [0-9]+ of rule" "$$LOG" 2>/dev/null | wc -l | tr -d " "); \
		[ -n "$$RUNS" ] || RUNS="?"; \
		if [ "$$EC" -eq 0 ]; then \
			echo "[ok] $(OUTDIR)/$${BASE}-draft.pdf  ($$RUNS runs, $${ELAPSED}s)"; \
			rm -f "$$LOG"; \
			if command -v python >/dev/null 2>&1; then \
				python -B "$(REPORT_SCRIPT)" --main "$$MAIN" --out "$(REPORT_OUT)" --out-sections "$(REPORT_SECTIONS_OUT)"; \
			else \
				echo "[report] python not found, skipping"; \
			fi; \
		else \
			echo "[fail] Exit $$EC  ($${ELAPSED}s)"; \
			echo "[fail] See: $$LOG"; \
			exit $$EC; \
		fi'

debug:
	mkdir -p $(OUTDIR)
	@echo "[debug] $(TEX_MAIN)  (ENGINE=$(ENGINE), shell-escape=$(SHELL_ESCAPE))"
	$(LATEXMK) $(DEBUG_FLAGS) $(TEX_MAIN)
	@sh -c 'if command -v python >/dev/null 2>&1; then \
		python -B "$(REPORT_SCRIPT)" --main "$(TEX_MAIN)" --out "$(REPORT_OUT)" --out-sections "$(REPORT_SECTIONS_OUT)"; \
	else \
		echo "[report] python not found, skipping"; \
	fi'

# Remove LaTeX intermediates while keeping the PDF.
clean:
	@echo "[clean] Removing intermediates (keeping PDF)..."
	@$(LATEXMK) -c -outdir=$(OUTDIR) $(TEX_MAIN) >/dev/null 2>&1 || true
	@if ls $(OUTDIR)/*-draft.tex >/dev/null 2>&1; then \
		for f in $(OUTDIR)/*-draft.tex; do $(LATEXMK) -c -outdir=$(OUTDIR) "$$f" >/dev/null 2>&1 || true; done; \
	fi
	@rm -f $(OUTDIR)/latexmk-*.log
	@rm -rf $(OUTDIR)/_minted-* _minted-*

# Remove everything under build/, including the PDF.
distclean:
	@echo "[distclean] Removing build/ (including PDF)..."
	@$(LATEXMK) -C -outdir=$(OUTDIR) $(TEX_MAIN) >/dev/null 2>&1 || true
	@rm -rf $(OUTDIR)

# Windows preview helper.
view:
ifeq ($(OS),Windows_NT)
	@cmd.exe /C "start \"\" \"$(OUTDIR)\\TritonSurvey.pdf\""
else
	@sh -c 'command -v xdg-open >/dev/null 2>&1 && xdg-open "$(OUTDIR)/TritonSurvey.pdf" || open "$(OUTDIR)/TritonSurvey.pdf"'
endif
