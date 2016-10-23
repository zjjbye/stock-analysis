# Cassandra相关的代码

## 安装依赖
```sh
pip install -r requirements.txt
```

## 依赖的API说明
cassandra-driver https://github.com/datastax/python-driver

## stock-data-storage.py
### 说明
实现了一个Cassandra数据存储过程

### 运行代码
假如你的Cassandra运行在一个叫做bigdata的docker-machine里面, 然后虚拟机的ip是192.168.99.100 <br/>
下面的名命令将会创建名为stock的KEYSPACE和名为stock的TABLE，请确保其它程序不使用“stock”来命名它们，（以免造成您的其他程序存储的数据丢失）<br/>
可以通过``python data-storage.py -h``查看参数说明
```sh
python data-storage.py stock-analyzer 192.168.99.100:9092 stock stock 192.168.99.100
```