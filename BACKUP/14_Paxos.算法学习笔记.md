# [Paxos 算法学习笔记](https://github.com/zzy131250/gitblog/issues/14)

> 搬运自老博客，发表时间：2017-04-30

# 前言
前段时间实习，是做一个分布式的数据库系统，当然只是拿开源的分布式系统来使用一下。那时候，简单看了下分布式的基础算法——Paxos算法。最近看书又遇到了，打算好好学习一下，但是发现书上讲的好难懂，于是上网找，发现了土豆（更新：土豆上该视频已下架，链接改为b站的视频）上李海磊老师讲解Paxos的视频，讲得很到位，这里记录一下主要内容。

# Paxos 算法
## 简介
Paxos算法由Lamport于1990年提出，它是一种基于消息传递且具有高度容错特性的一致性算法。Paxos算法用来确定一个不可变变量的取值，它可以是任意取值，且一旦取值确定，就不再更改，且可被获取。在分布式系统中，可以把它理解为协商一个一致的数据操作序列。这在分布式系统中很重要，因为分布式系统的数据通常有多个副本。如何通过协调，让多个副本执行相同的操作序列，进而保证数据一致性，是分布式系统要解决的基本问题。

## 问题定义
可以把Paxos算法要解决的问题定义为：设计一个系统来存储名为var的取值，这个系统由acceptor来接收var值，由proposer发出var值。系统需要保证var的取值具有一致性，并需要保证具有容错性。这里不考虑acceptor故障丢失var信息问题和拜占庭将军问题。
解决这个问题，关键在以下四个方面：
1. 管理多个proposer的并发执行
2. 保证var取值的不可变性
3. 容忍proposer机器故障
4. 容忍半数以下acceptor机器故障

# 方案一
方案一先从简单的情况着手，我们先考虑系统由单个acceptor组成。这种情况下，可以通过类似互斥锁的机制来**管理proposer的并发执行**。proposer须先申请到acceptor的互斥访问权，然后再请求acceptor接受自己的值。acceptor负责发放互斥访问权，并接受得到互斥访问权的proposer发出的值。一旦acceptor接受了某个proposer的取值，就认为var值被确定，其他proposer**不再更改var值**。

## 具体实现
Acceptor：
1. 保存一个变量var和一个互斥锁lock
2. prepare()方法加锁，并返回当前var值
3. release()方法解锁，回收互斥访问权
4. accept(var, V)，如果已经加锁，且var值为空，则设置var为V并释放锁

Proposer（两阶段）：
- 第一阶段：通过Acceptor::prepare()尝试获取互斥访问权和var值，如果无法获取，则结束
- 第二阶段：根据var值选择执行方案。如果var值为空，则通过Acceptor::accept(var, V)提交V值；如果var值不为空，则释放锁，获得var值

## 问题
如果proposer在获得锁之后，释放锁之前发生故障，则系统将进入死锁。该方案不能容忍proposer机器故障。

# 方案二
为了解决方案一中的死锁问题，**容忍proposer机器故障**，我们引入抢占式访问权。acceptor可以让某个proposer的访问权失效，不再允许其访问，并将访问权重新发放给其他proposer。
为了实现这个目标，我们要求proposer在申请访问权的时候指定编号epoch，越大的epoch越新。acceptor采用“喜新厌旧”的原则，一旦收到更大的epoch，则令旧的访问权失效，然后给最新的epoch发放访问权，并只接受它提交的值。这样会导致拥有旧epoch的proposer无法运行，拥有新epoch的proposer将开始运行。为了保持一致性，不同epoch的proposer之间采用“后者认同前者”的原则，即如果acceptor上已设置了var值，则新的proposer不再更改，并且认同这个取值；如果acceptor上var值为空，proposer才提交自己的值。

## 具体实现
Acceptor：
1. 保存var的取值与var对应的accepted_epoch值，并保存最新发放访问权的lastest_epoch值
2. prepare(epoch)方法先判断参数epoch是否大于自己保存的lastest_epoch，如果大于则更新lastest_epoch为参数epoch值，并返回var的取值；否则返回错误
3. accept(var, epoch, V)方法先判断参数epoch是否为记录的lastest_epoch值，若相等则更新acceptor的var值与accepted_epoch值；否则返回错误

Proposer（两阶段）：
- 第一阶段：申请epoch值和获取var值。可选取当前时间戳作为epoch，调用Acceptor::prepare(epoch)尝试获取epoch轮次的访问权和var的取值，如果不能获取，则结束
- 第二阶段：根据var值选择执行方案。如果var值为空，则通过Acceptor::accept(var, epoch, V)提交V值，这里提交var值不一定成功，因为有可能在提交时其他proposer已经提交了更大的epoch值，导致当前proposer的访问权失效，此时会返回错误；如果var值不为空，获得并认同var值，不再更改

## 问题
由于系统仅有单个acceptor，如果acceptor发生故障，将导致整个系统无法运行。该方案不能容忍acceptor机器故障。

#方案三——Paxos
在前两种方案中，我们已经解决了部分问题，接下来，我们正式引入Paxos。Paxos在方案二的基础上，引入多个acceptor，并采用少数acceptor服从多数acceptor的思路，可以**容忍半数以下acceptor机器故障**。在Paxos中acceptor的实现与方案二一致，这里我们仅介绍proposer的实现。

## 具体实现
Proposer（两阶段）：
- 第一阶段：申请epoch值和获取var值。由于有多个acceptor，所以规定必须获取半数以上acceptor的访问权，才能进入第二阶段。当然，由于会有抢占epoch的情况，所以可能会有两个proposer分别获取半数以上访问权。但是请注意，这时实际上还是只有一个majority，因为必定有acceptor同时接受了两者，但是该acceptor只记录较大的epoch，所以对于该acceptor来说，只有较大epoch的proposer的访问权有效，结果只有一个proposer提交的值可以在acceptor中形成majority，从而达成一致。（如果有偶数个acceptor，这里可能会产生两个proposer各占一半的情况，在这种情况下，两个proposer都不能进入第二阶段。）
- 第二阶段：根据var值选择执行方案。如果var值都为空，则通过Acceptor::accept(var, epoch, V)提交V值，如果半数以上acceptor返回成功，则认为提交成功，否则返回错误；如果var值不都为空，则认同最大accepted_epoch对应的var值，并尝试向其他acceptor提交该var值

## 如何维持一致
这里我们假设，已经有一个epoch_1形成了一致的var值var_1，即已经有半数以上acceptor的var值确定为epoch_1对应的proposer提交的值var_1。那么，在epoch_1后一次的运行epoch_1+1轮次中，epoch_1+1对应的proposer需要获取半数以上acceptor访问权，所以它必定可以得到上一轮达成一致的var值var_1，并且var_1对应的epoch值epoch_1是已提交的epoch中最大的，那么，它就会认同var值，并继续传播var值，直到全部acceptor达成一致。

## 活锁
这里可能会出现一个活锁问题。我们知道，在proposer第一阶段获取半数以上acceptor访问权之后，可能会有新的proposer抢占它，导致原来的proposer无法继续运行。如果每次都有新的proposer抢占原来的proposer，那么将永远无法形成一致，这就是活锁。Lamport给出的解决方案是在proposer中选举一个leader，只允许leader提交取值，当leader故障时马上选举其他的leader。
