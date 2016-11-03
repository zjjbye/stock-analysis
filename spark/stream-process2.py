import argparse
import atexit
import json
import logging
import time

from kafka import KafkaProducer
from kafka.errors import KafkaError
from pyspark import SparkConf
from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils

logging.basicConfig()
logger = logging.getLogger('stream-processing')
logger.setLevel(logging.DEBUG)


def shutdown_hook(producer):
    try:
        logger.info('Flushing pending message to kafka, timeout is set to 10s')
        producer.flush(10)
        logger.info('Finish flushing pending message to kafka')
    except KafkaError as error:
        logger.warn('Failed to flush pending messages to kafka, caused by: %s', error.message)
    finally:
        try:
            logger.info('Closing kafka connection')
            producer.close(10)
        except Exception as e:
            logger.warn('Failed to close kafka connection, caused by: %s', e.message)


def streaming_process(dstream):

    def record2pair(raw_record):
        record = json.loads(raw_record[1].decode('utf-8'))[0]
        return record.get('StockSymbol'), (float(record.get('LastTradePrice')), 1)

    def send2kafka(rdd):
        # - collect records to DRIVER
        records = rdd.collect()

        for record in records:
            data = json.dumps({
                'symbol': record[0],
                'timestamp': time.time(),
                'average': record[1]
            })
            try:
                kafka_producer.send(new_topic, value=data)
            except KafkaError as error:
                logger.warn('Failed to send average stock price to kafka, caused by: %s', error.message)
            logger.info('Send %s to kafka' % json.loads(data))

    dstream \
        .map(record2pair) \
        .reduceByKey(lambda a, b: (a[0] + b[0], a[1] + b[1])) \
        .map(lambda (k, v): (k, v[0] / v[1])) \
        .foreachRDD(send2kafka)


if __name__ == '__main__':
    # - setup command line argument
    parser = argparse.ArgumentParser()
    parser.add_argument('kafka_brokers', help='location of kafka')
    parser.add_argument('topic', help='original topic name')
    parser.add_argument('new_topic', help='new topic to send data to')

    # - get arguments
    args = parser.parse_args()
    kafka_brokers = args.kafka_brokers
    topic = args.topic
    new_topic = args.new_topic

    # - setup spark streaming utility

    conf = SparkConf() \
        .setMaster("local[2]") \
        .setAppName("StockAveragePrice")

    sc = SparkContext(conf=conf)
    sc.addFile('spark/stream-process.py')
    sc.setLogLevel('ERROR')
    ssc = StreamingContext(sc, 5)

    # - instantiate a kafka stream for processing
    kafka_stream = KafkaUtils.createDirectStream(ssc, [topic], {'metadata.broker.list': kafka_brokers})
    streaming_process(kafka_stream)

    # - instantiate a simple kafka producer
    kafka_producer = KafkaProducer(bootstrap_servers=kafka_brokers.split(','))

    # - setup proper shutdown hook
    atexit.register(shutdown_hook, kafka_producer)

    # - start streaming processing
    ssc.start()
    ssc.awaitTermination()
