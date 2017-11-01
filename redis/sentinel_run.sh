#!/bin/bash
configfile="/etc/redis.conf"
function start(){
  redis-server $1 --sentinel
}

cat >> ${configfile} << EOF
dir "/data"
port 26379
sentinel monitor mymaster ${master_ip} ${master_port} ${vote}
sentinel down-after-milliseconds mymaster 3000
sentinel failover-timeout mymaster 180
EOF
start ${configfile}
