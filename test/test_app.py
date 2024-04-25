# app.py
from flask import Flask
from celery import Celery

# Initialize Flask app
app = Flask(__name__)

# Celery configuration
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# Celery task


@celery.task
def add(x, y):
    return x + y

# Flask route


@app.route('/')
def hello_world():
    # Call Celery task asynchronously
    result = add.delay(4, 4)
    return f"Result: {result.get()}"  # Get task result


if __name__ == '__main__':
    app.run(debug=True)
