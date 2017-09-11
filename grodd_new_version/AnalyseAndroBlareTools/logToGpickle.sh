#!/bin/sh
if [ -z $1 ]
then
    echo 'Usage : '$0' /fullPATH/<file_name>'
else
    grep BLARE $1 > $1.tmp
    echo "BLARE"
    logparser/logcleaner/logcleaner.sh $1.tmp
    echo "CLEANED"
    logparser/logconverter.py -i $1.tmp --o_type gpickle
    echo "PICKLED"
    rm $1.tmp
    echo "Done."
fi
