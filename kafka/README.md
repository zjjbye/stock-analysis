# Kafka相关的代码

## 安装依赖
```sh
pip install -r requirements.txt
```

## 配置参数
根据实根环境配置config中的文件

## 依赖的API说明
googlefinance   https://pypi.python.org/pypi/googlefinance<br/>
confluent-kafka https://github.com/confluentinc/confluent-kafka-python<br/>
schedule        https://pypi.python.org/pypi/schedule<br/>
APScheduler     https://pypi.python.org/pypi/APScheduler/3.2.0

## test-data-producer.py
### 说明
实现了一个kafka producer, 每秒钟产生随机的股票价格, 发送给Kafka

### 运行代码
假如你的Kafka运行在一个叫做bigdata的docker-machine里面, 然后虚拟机的ip是192.168.99.100
```sh
python test-data-producer.py stock-analyzer 192.168.99.100:9092
```

## stock-data-producer.py
### 说明
实现了一个kafka producer, 每秒钟从Yahoo Finance抓取某只股票的信息, 发送给Kafka
抓取的股票信息可以通过HTTP请求动态（指定股票代码，如AAPL、ADSK）添加（POST）或删除（DELETE）

### 运行代码
加入你的Kafka运行在一个叫做bigdata的docker-machine里面, 然后虚拟机的ip是192.168.99.100
```sh
export ENV_CONFIG_FILE=`pwd`/config/dev.cfg
python stock-data-producer.py
```