#!/bin/bash
template="/tmp/configfile"
configfile="/etc/redis.conf"
defaultport=6379
function start_master(){
  cp -a ${template} ${configfile}
  redis-server ${configfile} --appendfilename "${HOSTNAME}.aof" --dbfilename "${HOSTNAME}.rdb"
}

function start_slave(){
  cp -a ${template} ${configfile}
  redis-server ${configfile} --slaveof $1 ${defaultport} --appendfilename "${HOSTNAME}.aof" --dbfilename "${HOSTNAME}.rdb"
}


redis-cli -h ${sentinel_ip} -p ${sentinel_port} info
if [ $? -ne 0 ];then
 if [ ${HOSTNAME} = "${master}" ];then
    start_master
 else
    start_slave "${master}.${service_name}"
 fi
else
 master_ip=$(redis-cli -h ${sentinel_ip} -p ${sentinel_port} info Sentinel | tail -n 1 | awk -F ',' '{print $3}' | awk -F '=' '{print $2}' | awk -F ':' '{print $1}')
 my_ip=$(ip a | grep -w "inet" | grep -v '127.0.0.1' | awk '{print $2}' | awk -F '/' '{print $1}')
 if [ ${my_ip} != ${master_ip} ];then
   start_slave "${master_ip}"
 else
   start_master
 fi
fi
