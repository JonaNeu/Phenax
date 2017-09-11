# lance un log, en créant un nouveau fichier avec le nom du fichier passé en
# paramètre et se terminant en .blarelog
if [ ! -d logs ]
then
    mkdir logs
fi
cat /proc/kmsg >> /data/data/org.blareids.logger/logs/$1.blarelog 
