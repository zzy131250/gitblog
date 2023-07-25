# [IPTables 学习实践](https://github.com/zzy131250/gitblog/issues/28)

> 搬运自老博客，发表时间：2019-06-12

# 概述
Iptables是一个配置Linux内核防火墙的命令行工具，是Netfilter项目的一部分。Iptables通过封包过滤的方式检测、修改、转发或丢弃IPv4数据包，过滤的方式则采用一系列默认和用户定义的规则。如果匹配到规则，则执行该规则的动作。注意，Iptables的规则是有顺序的，只会执行第一个匹配规则的动作。
![8cbddf6ff58c4308.png](https://github.com/zzy131250/gitblog/assets/7437470/38e96b68-d0df-4596-aba3-186f7ce671dc)

# 概念介绍
## 表（Table）
Iptables里面有多个表（Table），每个表都定义出自己的默认策略与规则，且每个表的用途都不相同。
Iptables主要包含的表：

- raw表：用于配置数据包，其中的数据包不会被系统跟踪
- filter表：存放所有与防火墙相关操作的默认表
- nat表：用于网络地址转换（来源、目的IP、port的转换）
- mangle表：用于对特殊封包的修改
![c017ffe532d4ad71.png](https://github.com/zzy131250/gitblog/assets/7437470/0a45ef67-4dde-40d1-a309-77ad79e59492)

## 链（Chain）
Iptables主要包含的链：

- INPUT链：作用于想要进入本机的封包
- OUTPUT链：作用于本机要发送的封包
- FORWARD链：作用于要转发的封包
- PREROUTING链：作用于路由判断之前
- POSTROUTING链：作用于路由判断之后

Iptables封包过滤过程（表与链的生效时机）如下图：
![f0c53008b78b4655.jpg](https://github.com/zzy131250/gitblog/assets/7437470/c48f2337-6f74-4eb9-96dc-05eb07645530)

## 规则（Rule）
位于Iptables上的一系列匹配规则，这些规则包括匹配条件与执行目标（跳转到链、内置目标ACCEPT，DROP，QUEUE和RETURN、扩展目标REJECT和LOG）。
在执行目标为跳转到链时，如果目标链的规则不能提供完全匹配，则会返回到调用链继续寻找匹配规则。
![38268c476c086c06.jpg](https://github.com/zzy131250/gitblog/assets/7437470/74a0b7c7-b15a-4bcf-b271-1c1f095ee387)

## 模块（Module）
模块可以用来扩展Iptables，如conntrack链接跟踪等。

# 实践
本实践通过配置Iptables规则达到Docker端口映射的目的。实践的机器为CentOS 7.6虚拟机，预先安装了Iptables（v1.4.21）和Docker（v18.09.6）。
Iptables规则可通过iptables -S -t [table]命令查看，最初的Iptables规则列表如下：

```
*nat
-P PREROUTING ACCEPT # PREROUTING链的默认规则为ACCEPT
-P INPUT ACCEPT
-P OUTPUT ACCEPT
-P POSTROUTING ACCEPT
-N DOCKER # 用户自定义的链
-A PREROUTING -m addrtype --dst-type LOCAL -j DOCKER
-A OUTPUT ! -d 127.0.0.0/8 -m addrtype --dst-type LOCAL -j DOCKER
-A POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE # 对源地址为172.17.0.0/16网段，出口网桥不是docker0的数据包做动态IP的SNAT
-A DOCKER -i docker0 -j RETURN
*filter
-P INPUT ACCEPT
-P FORWARD DROP
-P OUTPUT ACCEPT
-N DOCKER
-N DOCKER-ISOLATION-STAGE-1
-N DOCKER-ISOLATION-STAGE-2
-N DOCKER-USER
-A FORWARD -j DOCKER-USER
-A FORWARD -j DOCKER-ISOLATION-STAGE-1
-A FORWARD -o docker0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A FORWARD -o docker0 -j DOCKER
-A FORWARD -i docker0 ! -o docker0 -j ACCEPT
-A FORWARD -i docker0 -o docker0 -j ACCEPT
-A DOCKER-ISOLATION-STAGE-1 -i docker0 ! -o docker0 -j DOCKER-ISOLATION-STAGE-2
-A DOCKER-ISOLATION-STAGE-1 -j RETURN
-A DOCKER-ISOLATION-STAGE-2 -o docker0 -j DROP
-A DOCKER-ISOLATION-STAGE-2 -j RETURN
-A DOCKER-USER -j RETURN
```

通过docker run -p 8080:8080命令，我们添加了端口映射。现在，我们可以直接通过curl http://10.0.2.15:8080命令访问容器中的服务。其中，10.0.2.15是CentOS宿主机的IP。再次查看Iptables，规则列表变为：

```
*nat
-P PREROUTING ACCEPT
-P INPUT ACCEPT
-P OUTPUT ACCEPT
-P POSTROUTING ACCEPT
-N DOCKER
-A PREROUTING -m addrtype --dst-type LOCAL -j DOCKER
-A OUTPUT ! -d 127.0.0.0/8 -m addrtype --dst-type LOCAL -j DOCKER
-A POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE
-A POSTROUTING -s 172.17.0.2/32 -d 172.17.0.2/32 -p tcp -m tcp --dport 8080 -j MASQUERADE
-A DOCKER -i docker0 -j RETURN
-A DOCKER ! -i docker0 -p tcp -m tcp --dport 8080 -j DNAT --to-destination 172.17.0.2:8080
*filter
-P INPUT ACCEPT
-P FORWARD DROP
-P OUTPUT ACCEPT
-N DOCKER
-N DOCKER-ISOLATION-STAGE-1
-N DOCKER-ISOLATION-STAGE-2
-N DOCKER-USER
-A FORWARD -j DOCKER-USER
-A FORWARD -j DOCKER-ISOLATION-STAGE-1
-A FORWARD -o docker0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A FORWARD -o docker0 -j DOCKER
-A FORWARD -i docker0 ! -o docker0 -j ACCEPT
-A FORWARD -i docker0 -o docker0 -j ACCEPT
-A DOCKER -d 172.17.0.2/32 ! -i docker0 -o docker0 -p tcp -m tcp --dport 8080 -j ACCEPT
-A DOCKER-ISOLATION-STAGE-1 -i docker0 ! -o docker0 -j DOCKER-ISOLATION-STAGE-2
-A DOCKER-ISOLATION-STAGE-1 -j RETURN
-A DOCKER-ISOLATION-STAGE-2 -o docker0 -j DROP
-A DOCKER-ISOLATION-STAGE-2 -j RETURN
-A DOCKER-USER -j RETURN
```

我们发现多了三条规则：
```
*nat
# 对源地址为172.17.0.2/32，目的地址为172.17.0.2/32，目的端口为8080的TCP包做动态IP SNAT
-A POSTROUTING -s 172.17.0.2/32 -d 172.17.0.2/32 -p tcp -m tcp --dport 8080 -j MASQUERADE
# 对入口网桥不是docker0，目的端口为8080的TCP包做DNAT，目的地址为172.17.0.2:8080
-A DOCKER ! -i docker0 -p tcp -m tcp --dport 8080 -j DNAT --to-destination 172.17.0.2:8080
*filter
# 对目的地址为172.17.0.2/32，入口网桥不是docker0，出口网桥是docker0，目的端口是8080的TCP包做ACCEPT
-A DOCKER -d 172.17.0.2/32 ! -i docker0 -o docker0 -p tcp -m tcp --dport 8080 -j ACCEPT
```
下面我们依次手动添加Iptables规则，命令如下：
```
iptables -t nat -A POSTROUTING -s 172.17.0.2/32 -d 172.17.0.2/32 -p tcp -m tcp --dport 8080 -j MASQUERADE
iptables -t nat -A DOCKER ! -i docker0 -p tcp -m tcp --dport 8080 -j DNAT --to-destination 172.17.0.2:8080
iptables -t filter -A DOCKER -d 172.17.0.2/32 ! -i docker0 -o docker0 -p tcp -m tcp --dport 8080 -j ACCEPT
```