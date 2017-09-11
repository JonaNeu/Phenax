#!/bin/bash
if [ -z $1 ]
then
    echo 'Usage : '$0' /fullPATH/<file_name> (optional)[node name to colorize] '
    echo 'Example : '$0' logs/log1.log com.durak'
else
    grep BLARE $1 > $1.tmp
    echo "BLARE"
    ./logcleaner.sh $1.tmp
    echo "CLEANED"
    ./logparser/logconverter.py -i $1.tmp --o_type dot #gpickle
    echo "PICKLED"
    rm $1.tmp
    if [ ! -z "$2" ]
      then
	e=$(dirname "$1")
	f=$(basename "$1")
	sed  "/$2/a color=red" $e"/"$f.tmp.dot > $e"/"$f.tmp.dot.new
  mv $e"/"$f.tmp.dot.new $e"/"$f.tmp.dot
	echo "COLORIZED"
    fi
    echo "Done."
fi
