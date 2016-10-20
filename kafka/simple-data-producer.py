import argparse
import atexit
import datetime
import logging
import random
import time

from kafka import KafkaProducer

logger_format = '%(asctime)-15s %(message)s'
logging.basicConfig(format=logger_format)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def generate_and_write_data(p, topic):
    """
    generate data and write it to kafka
    :param p: produce
    :param topic:
    :return:
    """
    logger.info('Start to generate data and write to kafka')
    num_of_msg = 0
    start = time.time()
    while True:
        num_of_msg += 1
        price = random.randint(30, 120)
        current_time = time.time()
        timestamp = datetime.datetime.fromtimestamp(current_time).strftime('%Y-%m-%dT%H:%MZ')
        payload = ('[{"StockSymbol":"AAPL","LastTradePrice":%d,"LastTradeDateTime:"%s"}]' % (price, timestamp)).encode('utf-8')
        # p.produce(topic, value=payload)
        # p.poll(0)
        p.send(topic=topic, value=payload, timestamp_ms=current_time)
        # - generate one log for every 100000 records
        if num_of_msg == 100000:
            end = time.time()
            logger.info('Wrote 1000000 records to Kafka in %s' % (end - start))
            start = end
            num_of_msg = 0


def shutdown_hook(p):
    """
    a shutdown hook to be called before the shutdown
    :param p: produce
    :return:
    """
    try:
        logger.info('Flushing pending messages to kafka')
        p.flush()
        logger.info('Finish flushing pending messages to kafka')
    except Exception as kafka_error:
        logger.warn('Failed to flush pending messages to kafka, caused by: %s', kafka_error.message)


if __name__ == '__main__':
    # - setup command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('topic_name', help='the kafka topic push to')
    parser.add_argument('kafka_broker', help='the location of the kafka broker')

    # - parse arguments
    args = parser.parse_args()
    topic_name = args.topic_name
    kafka_broker = args.kafka_broker

    # - instantiate a simple kafka producer
    producer = KafkaProducer(bootstrap_servers=kafka_broker)

    # - setup proper shutdown hook
    atexit.register(shutdown_hook, producer)

    # - start to write kafka
    generate_and_write_data(producer, topic_name)
