#!/bin/bash

if [ "$1" = "" -o "$1" = "--help" -o "$1" = "-h" ]; then
        echo "Convert old format projmane (before 0.10.0) to new format"
        echo 
        echo "USAGE: projman_convert_format.sh <old_format_file.xml> <new_format_file.xml>"
        echo "       projman_convert_format.sh -d <old_format_files_in_directory>"
else
    if [ "$1" = "-d" ]; then
	for i in `ls $2` ; do
	    echo xsltproc -o $2/$i.new xslt/convert.xml $2/$i
	    xsltproc -o $2/$i.new xslt/convert.xml $2/$i
	    mv $2/$i.new $2/$i
	done
    else
	echo xsltproc -o $2 xslt/convert.xml $1
	xsltproc -o $2 xslt/convert.xml $1
    fi
fi