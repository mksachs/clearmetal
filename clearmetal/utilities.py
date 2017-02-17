# -*- coding: utf-8 -*-
"""Utilities for the ClearMetal code challenge.

"""

import subprocess
import argparse
import sys
import functools
import logging
import logging.handlers
import os
import time
import math
import importlib
import json

default_logger_spec = {
    'datefmt': '%Y-%m-%d %H:%M:%S %z',
    'file': 'logs/log.log',
    'format': '[%(asctime)s +0000: %(levelname)s/%(name)s] %(message)s',
    'level': 20,
    'handler_type': 'file'
}


def set_up_logger(in_logger, **logger_spec):
    """Sets up a logging instance.

    Args:
        in_logger (logging.Logger): The logging instance to set up. 
        **logger_spec: Keyword arguments specifying the logger config. 

    Returns:
        logging.Logger: Configured logging.Logger instance

    """
    assert isinstance(in_logger, logging.Logger)

    for key in default_logger_spec:
        if key not in logger_spec:
            logger_spec[key] = default_logger_spec[key]

    handler_type = logger_spec.get('handler_type')
    format = logger_spec.get('format')
    date_format = logger_spec.get('date_format')
    level = logger_spec.get('level')
    file = logger_spec.get('file')

    if len(in_logger.handlers) > 0:
        in_logger.handlers = []

    if handler_type in ['auto_rotate', 'file']:
        if file is None:
            file = 'log.log'
        else:
            if file.startswith('/'):
                curr_path = '/'
            else:
                curr_path = ''

            for dir in file.split('/')[0:-1]:
                curr_path += '{}/'.format(dir)
                # print(curr_path)
                if not os.path.isdir(curr_path):
                    os.mkdir(curr_path)

    if handler_type == 'auto_rotate':
        handler = logging.handlers.RotatingFileHandler(
            file, backupCount=100, maxBytes=2000000
        )
    elif handler_type == 'file':
        handler = logging.handlers.RotatingFileHandler(file, backupCount=100)
    else:
        handler = logging.StreamHandler()

    formatter = logging.Formatter(format, datefmt=date_format)
    formatter.converter = time.gmtime
    handler.setFormatter(formatter)
    in_logger.addHandler(handler)
    in_logger.setLevel(level)

    return in_logger


def logger(**logger_kwargs):
    """Decorator to enable logging in any decorated function. 

    Args:
        **logger_kwargs: Keyword arguments specifying the logger config. 

    Returns:
        function: Decorator function.

    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Make sure we have a complete logger spec
            logger_spec = logger_kwargs.get('logger_spec')
            if logger_spec is None:
                logger_spec = default_logger_spec
            else:
                logger_spec = logger_spec
                for key in default_logger_spec:
                    if key not in logger_spec:
                        logger_spec[key] = default_logger_spec[key]

            # Set up the logger
            l = set_up_logger(
                logging.getLogger('{}.{}'.format(func.__module__, func.__name__)),
                **logger_spec
            )

            kwargs['logger'] = l

            return func(*args, **kwargs)
        return wrapper
    return decorator


def set_foundation(username, password):
    """Sets up the foundational processes to run the ClearMetal code challenge.

    Args:
        username (str): Username for the RabbitMQ instance. 
        password (str): Password for the RabbitMQ instance. 
    """
    calls =[
        [
            'rm',
            'celerybeat-schedule'
        ],
        [
            'memcached',
            '-d'
        ],
        [
            'sudo',
            'rabbitmq-server',
            '-detached'
        ],
        [
            'sudo',
            'rabbitmqctl',
            'stop_app'
        ],
        [
            'sudo',
            'rabbitmqctl',
            'force_reset'
        ],
        [
            'sudo',
            'rabbitmqctl',
            'start_app'
        ],
        [
            'sudo',
            'rabbitmqctl',
            'add_user',
            '{}'.format(username),
            '{}'.format(password)
        ],
        [
            'sudo',
            'rabbitmqctl',
            'set_user_tags',
            '{}'.format(username),
            'administrator'
        ],
        [
            'sudo',
            'rabbitmqctl',
            'set_permissions',
            '-p',
            '/',
            '{}'.format(username),
            '.*',
            '.*',
            '.*'
        ],
        [
            'sudo',
            'rabbitmqctl',
            'delete_user',
            'guest'
        ],

    ]

    for call in calls:
        proc = subprocess.Popen(call, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        proc_result = proc.communicate()
        for res in proc_result:
            for line in str(res, 'utf-8').split('\n'):
                print(line)


def subdivide_list(full_list, subdivisions):
    """Segments a list into sub-lists.

    Args:
        full_list (list): The list to subdivide. 
        subdivisions (int): The number of sublists to return. 

    Returns:
        list: A list of lists.

    """
    list_size = len(full_list)

    if list_size > 0:
        # Figure out how many segments we will break the task up into
        seg = int(math.floor(float(list_size)/float(subdivisions)))
        if seg < 1:
            seg = 1

        # Break up the tasks.
        subdivided_list = []
        if list_size < subdivisions:
            subdivisions = list_size

        for i in range(subdivisions):
            # if i == subdivisions - 1:
            #     end_index = list_size
            # else:
            end_index = seg*int(i + 1)
            start_index = int(i) * seg
            if start_index != end_index:
                subdivided_list.append(full_list[start_index:end_index])

        remainder = full_list[end_index:int(end_index + float(list_size) % float(subdivisions))]

        index = 0
        while len(remainder) > 0:
            if index % len(subdivided_list) == 0:
                index = 0
            subdivided_list[index].append(remainder.pop(0))
            index += 1

        return subdivided_list
    else:
        return []
    

def main():
    
    sys.path.insert(1, './')

    parser = argparse.ArgumentParser(prog='PROG')
    subparsers = parser.add_subparsers(help='Command list', dest='subparser_name')

    set_foundation_parser = subparsers.add_parser('set_foundation', help='Sets up all the foundational processes.')
    set_foundation_parser.add_argument('user', help='The name of the rabbitmq user.')
    set_foundation_parser.add_argument('-p', help='Password.', dest='password')

    run_task_parser = subparsers.add_parser('run_task', help='Run tasks.')
    run_task_parser.add_argument(
        dest='task',
        help='The full path to the task to run. Eg. clearmetal.tasks.main.start_task'
    )
    run_task_parser.add_argument(
        '--args',
        help='A string representation of a python list of positional arguments. Eg. "[arg1, arg2]"',
        dest='args'
    )
    run_task_parser.add_argument(
        '--kwargs',
        help='A string representation of a python dict of keyword arguments. Eg. "{kw1: value1, kw1: value2}"',
        dest='kwargs'
    )

    cl_args = parser.parse_args()

    if cl_args.subparser_name == 'set_foundation':
        if cl_args.password is not None:
            need_selection = False
            password = cl_args.password
        else:
            need_selection = True
            password = None
    
        while need_selection:
            user_input = input(
                u'Password: '
            )
            if user_input != '':
                password = user_input
                need_selection = False
            else:
                print('Please enter a password.')
    
        set_foundation(cl_args.user, password)
    elif cl_args.subparser_name == 'run_task':
        task_module_str = '.'.join(cl_args.task.split('.')[0:-1])
        task_str = cl_args.task.split('.')[-1]
        i = importlib.import_module(task_module_str)
        task = getattr(i, task_str)

        if cl_args.args is not None:
            args = json.loads(cl_args.args)
        else:
            args = []

        if cl_args.kwargs is not None:
            kwargs = json.loads(cl_args.kwargs)
        else:
            kwargs = {}

        task.delay(*args, **kwargs)
    

if __name__ == "__main__":
    sys.exit(main())

