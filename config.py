# -*- coding: utf-8 -*-
"""Configuration for the ClearMetal coding challenge.

"""

import celery.schedules

secrets = {
    'rabbitmq': {'user': 'clearmetal_app','password': 'set_me'}
}

logging = {
    'base': {
        'file': 'logs/celery.log',
        'handler_type': 'auto_rotate'
    },
    'app': {
        'file': 'logs/app.log',
        'handler_type': 'auto_rotate'
    }
}

celery = {
    'broker_url': 'pyamqp://{}:{}@localhost:5672'.format(
        secrets['rabbitmq']['user'], secrets['rabbitmq']['password']
    ),
    'task_annotations': {'celery.chord_unlock': {'queue': 'canvas'}},
    'result_backend': 'cache+memcached://127.0.0.1:11211/',
    'task_serializer': 'json',
    'beat_schedule': {
        'word_count-pipeline': {
            'args': [
                'moby_dick.txt', 
                {'current_task': 'cm_word_count', 'all_tasks': ['cm_word_count', 'cm_add']}
            ],
            # 'schedule': celery.schedules.crontab(minute=51, hour=8),
            'schedule': celery.schedules.crontab(minute='*/5'),
            'task': 'clearmetal.tasks.main.start_task'
        }
    }
}