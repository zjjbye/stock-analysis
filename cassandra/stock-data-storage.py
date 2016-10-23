import argparse
import atexit
import json
import logging

from cassandra.cluster import Cluster
from kafka import KafkaConsumer
from kafka.errors import KafkaError


logger_format = '%(asctime)-15s %(messages)s'
logging.basicConfig()
logger = logging.getLogger('data-storage')
logger.setLevel(logging.DEBUG)


def persist_data(stock_data, cassandra_session, table):
    """
    persist stock data into cassandra
    :param stock_data:
         the stock data looks like this:
        [{
            "Index": "NASDAQ",
            "LastTradeWithCurrency": "109.36",
            "LastTradeDateTime": "2016-08-19T16:00:02Z",
            "LastTradePrice": "109.36",
            "LastTradeTime": "4:00PM EDT",
            "LastTradeDateTimeLong": "Aug 19, 4:00PM EDT",
            "StockSymbol": "AAPL",
            "ID": "22144"
        }]
    :param cassandra_session: instance of cassandra session
    :param table: the table to insert stock data into
    :return:None
    """
    # noinspection PyBroadException
    try:
        logger.debug('Start to persist data to cassandra %s' % stock_data)
        parsed = json.loads(stock_data)[0]
        symbol = parsed.get('StockSymbol')
        trade_price = float(parsed.get('LastTradePrice'))
        trade_time = parsed.get('LastTradeDateTime')

        # - prepare to insert to cassandra
        statement = "INSERT INTO %s (stock_symbol, trade_time, trade_price) VALUES ('%s', '%s', %f)" \
                    % (table, symbol, trade_time, trade_price)
        cassandra_session.execute(statement)
        logger.info('Persisted data to cassandra for symbol %s, trade-price %f, trade-time %s'
                    % (symbol, trade_price, trade_time))
    except Exception:
        logger.error('Faild to persist data to cassandra %s', stock_data)


# noinspection PyShadowingNames
def shutdown_hook(consumer, session):
    """
    a shutdown hook to be called before the shutdown
    :param consumer: instance of a kafka consumer
    :param session: instance of cassandra session
    :return: None
    """
    try:
        logger.info('Closing Kafka Consumer')
        consumer.close()
        logger.info('Dafka Consumer closed')
        logger.info('Closing Cassandra Session')
        session.shutdown()
        logger.info('Cassandra Session closed')
    except KafkaError as kafka_error:
        logger.warn('Failed to close Kafka Consumer, caused by: %s', kafka_error.message)
    finally:
        logger.info('Exiting program')


if __name__ == '__main__':
    # - setup commandline arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('topic_name', help='the Kafka topic to subscribe from')
    parser.add_argument('kafka_brokers', help='the locations of kafka brokers')
    parser.add_argument('key_space', help='the keyspace to write data for')
    parser.add_argument('data_table', help='the data table to use')
    parser.add_argument('cassandra_brokers', help='the cassandra_brokers location')

    # - parse arguments
    args = parser.parse_args()
    topic_name = args.topic_name
    kafka_brokers = args.kafka_brokers
    key_space = args.key_space
    data_table = args.data_table
    # - IPs delimited by ","
    cassandra_brokers = args.cassandra_brokers

    # - cassandra session creation
    cassandra_cluster = Cluster(
        contact_points=cassandra_brokers.split(',')
    )
    session = cassandra_cluster.connect()

    session.execute(
        "CREATE KEYSPACE IF NOT EXISTS %s WITH replication = {'class':'SimpleStrategy', 'replication_factor':3} \
        AND durable_writes = 'true'" % key_space
    )
    session.set_keyspace(key_space)
    session.execute(
        "CREATE TABLE IF NOT EXISTS %s (stock_symbol text, trade_time timestamp, trade_price float, \
        PRIMARY KEY (stock_symbol,trade_time))" % data_table
    )

    # - create kafka consumer
    consumer = KafkaConsumer(
        topic_name,
        bootstrap_servers=kafka_brokers.split(',')
    )
    # for msg in consumer:
    #    print(msg)

    # - setup proper shutdown hook
    atexit.register(shutdown_hook, consumer, session)

    for msg in consumer:
        print(msg)
        persist_data(msg.value, session, data_table)
