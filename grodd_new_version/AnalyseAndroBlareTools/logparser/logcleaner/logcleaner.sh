#!/bin/sh

sed -i -e 's/> itag\[\(-*[0-9 ]*\)\]/> \{\1\}/g' $1
sed -i -e 's/}select.*$/}/g' $1
sed -i -e 's/> (null)/> {0}/g' $1
sed -i -e 's/}failed.*$/}/g' $1
sed -i -e "s/}.\+$/}/g" $1
sed -i -e 's/^.* > file \/dev\/cpuctl\/tasks .*$//g' $1
sed -i -e 's/re-initialized>/re-initialized/g' $1
sed -i -e '/^$/d' $1
sed -i -e 's/\(process .*\)\]/\1/g' $1 
sed -i -e 's/\([^ >\n\t]\)\[/\1/g' $1
sed -i -e "s/'//g" $1
sed -i -e 's/ #/#/g' $1
sed -i -e 's/Binder Thread/BinderThread/' $1
sed -i -e 's/> process \([0-9]\)/> process a\1/g' $1
sed -i -e 's/\] process \([0-9]\)/\] process a\1/g' $1
grep -v '> file /proc/.*/oom_adj' $1 | grep -v "> {}$" | grep -v "> file /sys/power/wake_" | grep -v "/dev/cpuctl/bg_non_interactive/tasks" | grep -v "\[BLARE\]" | uniq -s 42 > .tmp.log
#uniq -s 42 $1 > tmp.log
mv .tmp.log $1



