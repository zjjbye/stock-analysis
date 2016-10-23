import atexit
import json
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify
from googlefinance import getQuotes
from kafka import KafkaProducer
from kafka.errors import KafkaError, KafkaTimeoutError


app = Flask(__name__)
app.config.from_envvar('ENV_CONFIG_FILE')
kafka_brokers = app.config['CONFIG_KAFKA_ENDPOINTS']
topic_name = app.config['CONFIG_KAFKA_TOPIC']

logger_format = '%(asctime)-15s %(message)s'
logging.basicConfig(format=logger_format)
logger = logging.getLogger('data-producer')
if app.config['DEBUG']:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

logger.debug('CONFIG_KAFKA_ENDPOINTS = %s', kafka_brokers)
logger.debug('CONFIG_KAFKA_TOPIC = %s', topic_name)

# - instantiate a simple kafka producer
producer = KafkaProducer(
    bootstrap_servers=kafka_brokers.split(',')
)

# - a set of symbols of stocks
symbols = set()

schedule = BackgroundScheduler()
schedule.add_executor('threadpool')
schedule.start()


def shutdown_hook():
    """
    a showdown hook to be called before the shutdown
    :return: None
    """
    try:
        logger.info('Flushing pending messages to kafka, timeout is set to 10s')
        producer.flush(10)
        logger.info('Finish flushing pending messages to kafka')
    except KafkaError as kafka_error:
        logger.warn('Failed to flush pending messages to kafka, caused by: %s', kafka_error.message)
    finally:
        try:
            logger.info('Closing kakfa connection')
            producer.close(10)
        except Exception as e:
            logger.warn('Fial to close kafka connection, caused by: %s', e.message)
    try:
        logger.info('shutdown scheduler')
        schedule.shutdown()
    except Exception as e:
        logger.warn('Failed to shutdown scheduler, caused by: %s', e.message)


def fetch_price(symbol):
    """
    helper function to retrieve stock data and send it to kafka
    :param symbol: symbol of the stock
    :return: None
    """
    logger.debug('Start to fetch stock price for %s', symbol)
    try:
        price = json.dumps(getQuotes(symbol))
        logger.debug('Retrieved stock info %s", price')
        producer.send(topic=topic_name, value=price, timestamp_ms=time.time())
        logger.info('Sent stock price for %s to kafka', symbol)
    except KafkaTimeoutError as timeout_error:
        logger.warn('Failed to send stock price for $s to kafka, caused by: %s', (symbol, timeout_error.message))
    except Exception:
        logger.warn('Failed to fetch stock price for %s', symbol)


@app.route('/<symbol>', methods=['POST'])
def add_stock(symbol):
    if not symbol:
        return jsonify({
            'error': 'Stock symbol cannot be empty'
        }), 400
    if symbol in symbols:
        pass
    else:
        symbols.add(symbol)
        schedule.add_job(fetch_price, 'interval', [symbol], seconds=1, id=symbol)
    return jsonify(list(symbols)), 200


@app.route('/<symbol>', methods=['DELETE'])
def del_stock(symbol):
    if not symbol:
        return jsonify({
            'error': 'Stock symbol cannot be empty'
        }), 400
    if symbol not in symbols:
        pass
    else:
        symbols.remove(symbol)
        schedule.remove_job(symbol)
    return jsonify(list(symbols)), 200


# @app.route('/')
# def hello_world():
#    return 'Hello World!'


if __name__ == '__main__':
    atexit.register(shutdown_hook)

    # - testing
    # symbols.add('AAPL')
    # schedule.add_job(fetch_price, 'interval', ['AAPL'], seconds=1, id='AAPL')

    app_port = app.config['CONFIG_APPLICATION_PORT']
    logger.debug('CONFIG_APPLICATION_PORT = %s', app_port)
    app.run(host='0.0.0.0', port=app_port)
