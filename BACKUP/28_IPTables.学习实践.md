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