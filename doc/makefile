MKHTML=mkdoc
MKHTML_OPT=--param toc.section.depth=1 --target=html --stylesheet=single-file
MKDOC=mkdoc
MKDOC_OPT=--param toc.section.depth=1 --target=pdf --stylesheet=standard
VAL=xmlproc_parse

SRC=./

all: pdf html

pdf: ${SRC}user_manual.pdf

html: ${SRC}user_manual.html

#${SRC}valid:  ${SRC}*.xml
#	${VAL} ${SRC}*.xml && touch ${SRC}valid

${SRC}user_manual.html: ${SRC}*.xml
	${MKHTML} ${MKHTML_OPT} ${SRC}user_manual.xml

${SRC}user_manual.pdf: ${SRC}*.xml
	${MKDOC} ${MKDOC_OPT} ${SRC}user_manual.xml
	rm -f fop.log

clean:
	rm -f ${SRC}valid *.html *.pdf fop.log
