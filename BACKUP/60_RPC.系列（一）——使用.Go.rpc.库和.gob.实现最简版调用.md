# [RPC 系列（一）——使用 Go rpc 库和 gob 实现最简版调用](https://github.com/zzy131250/gitblog/issues/60)

# 前言
net/rpc 库是 Go 语言自带的 RPC 库，可以作为 RPC 学习的首选。
gob 库是 net/rpc 库的编解码库，可以实现对 TPC 包的编解码。

# 实现一个Service
使用 net/rpc 库实现 RPC 服务，其注册的 Service 方法需要符合以下要求：
1. 导出类型的导出方法（首字母大写表示导出）
2. 方法有两个导出类型的入参（请求和响应）
3. 第二个入参是指针类型
4. 一个 error 类型返回值

我们根据要求实现一个 HelloService：
```Go
import "fmt"

type HelloService struct{}

type HelloReq struct{
	Name string
}

type HelloResp struct{
	Resp string
}

func (*HelloService) Hello(req HelloReq, resp *HelloResp) error {
	resp.Resp = fmt.Sprintf("Hello, %v", req.Name)
	return nil
}
```

# Server 端
Server 端的主要作用是实现一个 Service 并提供服务。提供服务的方式是接收 TCP 请求，处理并返回 TCP 响应，代码如下：
```Go
import (
	"log"
	"net"
	"net/rpc"
)

func main() {
	// 注册RPC服务
	rpc.Register(&HelloService{})
	// 监听TCP端口
	listener, err := net.Listen("tcp", ":1234")
	if err != nil {
		log.Fatalf("ListenTCP err: %v", err)
	}
	log.Println("Server start")

	for {
		// 接收TCP连接
		conn, err := listener.Accept()
		if err != nil {
			log.Fatalf("Accept err: %v", err)
			continue
		}
		log.Println("Handle req")
		// 处理TCP连接
		go rpc.ServeConn(conn)
	}
}
```

# Client 端
Client 端主要是发起 TCP 连接，并进行 RPC 调用。Client 端代码如下：
```Go
import (
	"fmt"
	"log"
	"net/rpc"
)

func main() {
	// 建立TCP连接
	conn, err := rpc.Dial("tcp", ":1234")
	if err != nil {
		log.Fatalf("Dial err: %v", err)
	}

	resp := &HelloResp{}
	// 进行RPC调用
	err = conn.Call("HelloService.Hello", HelloReq{Name: "Zia"}, &resp)
	if err != nil {
		log.Fatalf("Call err: %v", err)
	}
	fmt.Println(resp)
}
```
# 最终效果
```Shell
# Server 端
go run hello.go server.go 
2023/09/24 18:39:20 Server start
2023/09/24 18:39:28 Handle req
# Client 端
go run hello.go client.go 
&{Hello, Zia}
```