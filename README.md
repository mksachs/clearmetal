# ClearMetal Code Challange

My solution to the ClearMetal coding challenge. This is a general task manager that uses [RabbitMQ](http://www.rabbitmq.com)
and [Celery](https://celery.readthedocs.io/en/latest/). One cool thing about this paticular solution is that the 
processing step of each task is designed to be distributed. In principal this would allow the tasks to be broken up into
as many segments as your hardware permits. The example tasks here are trivial, but will hopefully be enough to 
illustrate the technique.

## Installation

I use [homebrew](https://brew.sh) on osx for my package manager so all of the instructions will assume that. Also, all
of the code is written using python 3.6.

First install RabbitMQ and Memcached (which is used to store task results):

```bash
brew install rabbitmq memcached libmemcached
```

Next install the python requirements:

```bash
pip install -r requirements.txt
```

That *should* be it! I did not test this on a clean machine so there may be some dependencies I missed.

## Setup and running

To setup RabbitMQ and Memcached simply run:

```bash
python clearmetal/utilities.py set_foundation clearmetal_app -p set_me
```

`clearmetal_app` is the RabbitMQ user name and `set_me` is the password. These are defined in the `config.py` file and
you can set them to be anything you want. If you do change them just make sure you re-run `clearmetal/utilities.py` with
the new values.

Next start Celery with the following command:

```bash
celery -A clearmetal.app.app worker --pidfile=app.pid -n app -Q app,canvas
```

If all went well you should see something like this:

```bash
[2017-02-17 10:18:46,327: INFO/MainProcess] The ClearMetal scheduling app is starting...
[2017-02-17 10:18:46,333: INFO/MainProcess] The ClearMetal scheduling app celery@app has started.
[2017-02-17 10:18:46,333: INFO/MainProcess] {'word_count-pipeline': {'args': ['moby_dick.txt', {'current_task': 'cm_word_count', 'all_tasks': ['cm_word_count', 'cm_add']}], 'schedule': <crontab: */5 * * * * (m/h/d/dM/MY)>, 'task': 'clearmetal.tasks.main.start_task'}}
 
 -------------- celery@app v4.0.2 (latentcall)
---- **** ----- 
--- * ***  * -- Darwin-16.4.0-x86_64-i386-64bit 2017-02-17 10:18:46
-- * - **** --- 
- ** ---------- [config]
- ** ---------- .> app:         __main__:0x10cf18668
- ** ---------- .> transport:   amqp://clearmetal_app:**@localhost:5672//
- ** ---------- .> results:     memcached://127.0.0.1:11211/
- *** --- * --- .> concurrency: 8 (prefork)
-- ******* ---- .> task events: OFF (enable -E to monitor tasks in this worker)
--- ***** ----- 
 -------------- [queues]
                .> app              exchange=app(direct) key=app
                .> canvas           exchange=canvas(direct) key=canvas

[2017-02-17 10:18:46,502: INFO/Beat] beat: Starting...
[2017-02-17 10:18:46,512: INFO/Beat] The ClearMetal scheduling app <celery.beat.Service object at 0x10d113cf8> with beat schedule is starting.
[2017-02-17 10:18:46,519: INFO/MainProcess] Connected to amqp://clearmetal_app:**@127.0.0.1:5672//
[2017-02-17 10:18:46,532: INFO/MainProcess] mingle: searching for neighbors
[2017-02-17 10:18:47,557: INFO/MainProcess] mingle: all alone
[2017-02-17 10:18:47,619: INFO/MainProcess] celery@app ready.
```

To run tasks, open a new terminal window. There are two demo tasks included `cm_add` and `cm_word_count`. As their names
suggest, `cm_add` will add together a list of numbers, and `cm_word_count` will count all the significant words 
(ignores 'and', 'but', etc.) in a text file.

To add together the list `[1,2,3,4,5,6,7,8,9,10]` run:

```bash
python clearmetal/utilities.py run_task clearmetal.tasks.main.start_task --args='[[1,2,3,4,5,6,7,8,9,10], {"current_task": "cm_add"}]'
```

To count the words in the provided `moby_dick.txt` run: 

```bash
python clearmetal/utilities.py run_task clearmetal.tasks.main.start_task --args='["moby_dick.txt", {"current_task": "cm_word_count"}]'
```

Also, these tasks are designed to be chained together. You can count the words in `moby_dick.txt` and then take the
resulting list of counts and add them together. To do this run:

```bash
python clearmetal/utilities.py run_task clearmetal.tasks.main.start_task --args='["moby_dick.txt", {"current_task": "cm_word_count", "all_tasks": ["cm_word_count", "cm_add"]}]'
```

You will see all the output from these tasks in the terminal window running Celery. Also, the application will output
all of the log data to two files `logs/celery.log` for system messages, and `logs/app.log` for application messages. 
Lastly, there is a schedule defined in the `config.py` file to run the chained job every five minutes. To run this
schedule, first kill Celery by typing 'control-c' in the terminal window where Celery is running (not the window where
the commands are being issued from). Then restart Celery with this command:

```bash
celery -A clearmetal.app.app worker --pidfile=app.pid -B -n app -Q app,canvas
```

You should see a line like this:

```bash
[2017-02-17 10:34:51,151: INFO/Beat] The ClearMetal scheduling app <celery.beat.Service object at 0x101583c18> with beat schedule is starting.
```

which indicates that the scheduler is running.

## Troubleshooting

Celery stores the schedule information in a file called `celerybeat-schedule`. If you kill Celery and then re-start it
sometimes strange things can happen if this file is still there. To prevent this either delete the file before starting
Celery, or re-run:

```bash
python clearmetal/utilities.py set_foundation clearmetal_app -p set_me
```


