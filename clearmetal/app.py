# -*- coding: utf-8 -*-
"""The main ClearMetal code challenge Celery app. 

Run with this signature
    celery -A clearmetal.app.app worker --pidfile=app.pid -n app -Q app,canvas

or for a scheduled run
    celery -A clearmetal.app.app worker --pidfile=app.pid -B -n app -Q app,canvas

"""

import celery.signals

import config
import clearmetal.utilities

# instantiate Celery object
app = celery.Celery(include=[
    'clearmetal.tasks.main'
])

app.conf.update(**config.celery)
app.log.setup()

logger = clearmetal.utilities.set_up_logger(
    app.log.get_default_logger(),
    **config.logging['base']
)


@celery.signals.import_modules.connect
@clearmetal.utilities.logger(logger_spec=config.logging['app'])
def app_started_signal(sender=None, body=None, **kwargs):
    l = kwargs.get('logger')
    l.info('The ClearMetal scheduling app is starting...')


@celery.signals.beat_init.connect
@clearmetal.utilities.logger(logger_spec=config.logging['app'])
def beat_init_signal(sender=None, body=None, **kwargs):
    l = kwargs.get('logger')
    l.info('The ClearMetal scheduling app {} with beat schedule is starting.'.format(sender))


@celery.signals.celeryd_init.connect
@clearmetal.utilities.logger(logger_spec=config.logging['app'])
def celeryd_init_signal(sender=None, conf=None, **kwargs):
    l = kwargs.get('logger')
    l.info('The ClearMetal scheduling app {} has started.'.format(sender))
    l.info(conf.CELERYBEAT_SCHEDULE)


@celery.signals.worker_shutdown.connect
@clearmetal.utilities.logger(logger_spec=config.logging['app'])
def worker_shutdown_signal(sender=None, body=None, **kwargs):
    l = kwargs.get('logger')
    l.info('The ClearMetal scheduling app {} is shutting down.'.format(sender))


if __name__ == '__main__':
    app.start()
