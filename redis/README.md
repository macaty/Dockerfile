基于Kubernetes的redis主副加哨兵集群
---
## 用法:
> 将模板文件挂载到run.sh脚本中指定的$template变量指定的地址，设置redis容器启动命令为run.sh
> 所需环境变量:
```
 ${master}   redis集群中要设置为主的主机名
 ${service_name} k8s yaml 文件中的spec下的 servicename
 ${sentinel_ip}  sentinel集群对外暴露的service地址
 ${sentinel_port}  sentinel集群对外暴露的端口 
```
> 脚本：
```
    首先连接k8s集群sentinel service地址（判断集群是否第一次启动）
    如果没连上
      如果主机名为${master}变量所设置的则启动为主节点，否则启动为从节点
    如果连接成功
      从哨兵获取主节点ip地址，对比自己的ip,如果两个ip相等则成为主，否则成为slave
```
