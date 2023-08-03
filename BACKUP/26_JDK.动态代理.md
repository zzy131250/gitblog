# [JDK 动态代理](https://github.com/zzy131250/gitblog/issues/26)

> 搬运自老博客，发表时间：2018-09-02

# 前言
JDK 动态代理可以让我们很容易地实现代理模式。通过解析动态代理的实现机制，我们可以更好地使用它。

# 一个例子
我们先来写个简单的例子，先定义两个接口 Subject 和 Subject2。

```Java
public interface Subject {
    void hello();
}
public interface Subject2 {
    void hello2();
}
```

再定义一个实现类来实现上面的两个接口。

```Java
public class SubjectImpl implements Subject, Subject2 {
    @Override
    public void hello() {
        System.out.println("hello world");
    }
    @Override
    public void hello2() {
        System.out.println("hello world, two");
    }
}
```

下面，我们还得实现 InvocationHandler 接口，这个接口有一个 invoke 方法，用于集中处理在动态代理类对象上的方法调用，通常在该方法中实现对委托类的代理访问。我们在其中加入了处理逻辑，用于在实际调用方法之前打印一句 log，这也是动态代理常用的一个场景。

```Java
public class IHandler implements InvocationHandler {
    private Object object;
    IHandler(Object object) {
        this.object = object;
    }
    @Override
    public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
        System.out.println("log: before hello");
        method.invoke(object, args);
        return null;
    }
}
```

最后，我们写一个 main 方法，来测试动态代理。

```Java
public static void main(String[] args) {
    Subject subject = new SubjectImpl();
    InvocationHandler handler = new IHandler(subject);
    Subject s = (Subject) Proxy.newProxyInstance(IHandler.class.getClassLoader(),
            new Class<?>[]{Subject.class, Subject2.class}, handler);
    Subject2 s2 = (Subject2) Proxy.newProxyInstance(IHandler.class.getClassLoader(),
            new Class<?>[]{Subject.class, Subject2.class}, handler);
    s.hello();
    s2.hello2();
}
```

运行之后，可以看到控制台的输出如下：

```Java
log: before hello
hello world
log: before hello
hello world, two
```