#!/bin/bash

# translate the README.md into different TeX documents using different parameters
# compile those documents into pdfs using XeLaTeX
# the main readme TeX file will be in the directory readme
# others will be in the directory examples

source env/bin/activate

if [[ ! -d ./examples ]]; then mkdir ./examples; fi

# main readme TeX file: article in the readme/ directory with unnumbered headers and french quotes
md2tex README.md -c -t ./readme/readme_article_template.tex -o ./readme/README.tex -d article -u -f

# all other examples are in the examples/ dir
# complete document of class book with unnumbered headers and french quotes
md2tex README.md -c -t ./readme/readme_book_template.tex -o ./examples/README_book.tex -d book -u -f
# complete document of class article with numbered headers
md2tex README.md -c -t ./readme/readme_article_template.tex -o ./examples/README_article_numbered.tex
# complete document of class article with default template and numbered headers
md2tex README.md -c -o ./examples/README_article_default_template_numbered.tex
# complete document of class book with default params
md2tex README.md -c -o ./examples/README_book_default_template.tex -d book
# base transformation: partial file (body only) with anglo-saxon quotes and numbered headers
md2tex README.md -o ./examples/README_partial_base.tex  # this one won't be compiled

# compile all complete tex files
cd readme && xelatex -synctex=1 -shell-escape -interaction=nonstopmode -8bit README.tex > /dev/null
cd ../examples
for f in *.tex ; do
  echo "xelatex is compiling $f"
	if [[ "$f" != "README_partial_base.tex" ]] && [[ "$f" =~ ^.*\.tex$ ]]; then
		xelatex -synctex=1 -shell-escape -interaction=nonstopmode -8bit "$f" > /dev/null
	fi;
done;

echo "conversions and compilations finished!"
