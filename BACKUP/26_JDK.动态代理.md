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

这里有两个注意点：
1. 在 invoke 方法中，不能使用参数中的 proxy 来调用方法，这样会导致循环调用，最终导致栈溢出。
2. 在 main 方法中， subject 的对象声明可以是 Subject、Subject2、SubjectImpl中的任意一个，因为这里不是根据对象的声明来调用方法。

附上类图供参考。
![371ac0890df7772b.png](https://github.com/zzy131250/gitblog/assets/7437470/b83e2f46-8926-42a8-ad25-336fc64d4c2f)

# 原理分析
下面，我们来分析一下动态代理的源码实现，这里我们使用的是 JDK 1.8.0_144 版本。我们先来看下 Proxy.newProxyInstance() 这个方法，这个方法接收一个 ClassLoader，一组接口和一个 InvocationHandler。

```Java
public static Object newProxyInstance(ClassLoader loader, Class<?>[] interfaces, InvocationHandler h) throws IllegalArgumentException {
	...
	// 根据类加载器和接口获取代理类
	Class<?> cl = getProxyClass0(loader, intfs);
	...
	// 获取代理类的构造方法
	final Constructor<?> cons = cl.getConstructor(constructorParams);
	...
	// 使用构造方法新建一个实例，并将 InvocationHandler 参数传入
	return cons.newInstance(new Object[]{h});
	...
}
```

这里的关键是 getProxyClass0() 这个方法，我们看到方法里面是从一个 cache 中获取代理类。这个 cache 的作用是缓存已经生成的代理类以便后续使用，如果没有符合要求的代理类，则会根据该 cache 构造方法传入的 ProxyClassFactory 生成一个我们需要的代理类。下面我们看下 ProxyClassFactory 的实现，它主要实现了一个 apply() 方法，来生成代理类。

```Java
public Class<?> apply(ClassLoader loader, Class<?>[] interfaces) {
	...
	// 为代理类命名
	long num = nextUniqueNumber.getAndIncrement();
	String proxyName = proxyPkg + proxyClassNamePrefix + num;
	// 动态生成代理类的字节码数组
	byte[] proxyClassFile = ProxyGenerator.generateProxyClass(proxyName, interfaces, accessFlags);
	...
}
```

继续看 ProxyGenerator.generateProxyClass() 方法的实现。里面主要调用了 ProxyGenerator 的 generateClassFile() 方法，而该方法主要的作用是为代理类添加代理方法，将他设置为 Proxy 类的子类，然后转成字节码数组并返回。
在获取代理类之后，我们调用构造方法，生成了代理类实例对象。想看下我们生成的代理类长什么样吗？我们可以使用 IntelliJ IDEA 并在 main 方法第一行加一句：

```Java
System.getProperties().put("sun.misc.ProxyGenerator.saveGeneratedFiles", "true");
```

这样，我们就可以在项目目录下的 com.sun.proxy 包中看到动态生成的代理类了。

```Java
public final class $Proxy0 extends Proxy implements Subject, Subject2 {
    
    public final void hello2() throws  {
        try {
            super.h.invoke(this, m4, (Object[])null);
        } catch (RuntimeException | Error var2) {
            throw var2;
        } catch (Throwable var3) {
            throw new UndeclaredThrowableException(var3);
        }
    }
    public final void hello() throws  {
        try {
            super.h.invoke(this, m3, (Object[])null);
        } catch (RuntimeException | Error var2) {
            throw var2;
        } catch (Throwable var3) {
            throw new UndeclaredThrowableException(var3);
        }
    }
}
```

如我们所料，生成的 $Proxy0 类继承了 Proxy 类，并且实现了 Subject、Subject2 接口。而方法则通过调用父类 Proxy 的 InvocationHandler 的 invoke() 方法来实现。

# 参考资料
[Java 动态代理机制分析及扩展，第 1 部分](https://developer.ibm.com/languages/java/)