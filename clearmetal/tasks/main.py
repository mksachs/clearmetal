# -*- coding: utf-8 -*-
"""Main task control. Runs sub-tasks and collects their results.

"""

import datetime

import celery

import config
import clearmetal.app
import clearmetal.utilities

# Need to explicitly import all of the phase tasks
import clearmetal.tasks.cm_add
import clearmetal.tasks.cm_word_count


def title_string(base_string):
    """Adds formating characters to the provided string. 

    Resulting string will be 186 characters long, padded on the right with '-' and ending with '#'. For example, the 
    string:

    'test me!'

    becomes

    'test me!---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#'


    Args:
        base_string (str): A string which will have trailing characters added.

    Returns:
        title_string (str): The base string plus trailing characters. 

    """
    return base_string + (u'-' * (185 - len(base_string))) + u'#'


@clearmetal.app.app.task(queue='app')
@clearmetal.utilities.logger(logger_spec=config.logging['app'])
def start_task(
        task_data, task_metadata, segments=8, **kwargs
):
    """Generic distributed task initiation.

    Args:
        task_data: The data to be processed by the task.
        task_metadata: Metadata to control task chaining.
        segments (int): The number of segments to break the job into. Default: 8. 
        **kwargs: Key word args.

    """
    l = kwargs.get('logger')
    
    l.info(title_string(
        u'# Begin {} '.format(task_metadata['current_task'])
    ))
    
    del kwargs['logger']

    phase_tasks = 'clearmetal.tasks.{}'.format(task_metadata['current_task'].lower())

    concurrent_tasks = eval(phase_tasks).prep(
        task_data,
        segments=segments, **kwargs
    )

    process = celery.chord(
        concurrent_tasks,
        eval(phase_tasks).collect.s()
    )
    celery.chain(
        [
            process,
            end_task.s(
                task_metadata,
                segments=segments,
                **kwargs
            )
        ]
    ).delay()


@clearmetal.app.app.task(queue='app')
@clearmetal.utilities.logger(logger_spec=config.logging['app'])
def end_task(task_results, task_metadata, segments=8, **kwargs):
    """Generic distributed task termination.

    Args:
        task_results: The results from the current task. Will be passed to any chained tasks.
        task_metadata: Metadata to control task chaining.
        segments (int): The number of segments to break the job into. Default: 8. 
        **kwargs: Key word args.

    """
    l = kwargs.get('logger')
    
    l.info(title_string(
        u'# End {}.'.format(task_metadata['current_task'])
    ))

    del kwargs['logger']
    
    all_tasks = task_metadata.get('all_tasks')
    if all_tasks is not None:
        current_task_id = all_tasks.index(task_metadata['current_task'])
        new_phase_id = current_task_id + 1
        if new_phase_id == len(task_metadata['all_tasks']):
            # We are done
            l.info(title_string(
                u'# End Job.'
            ))
        else:
            # Prep the new phase
            task_metadata['current_task'] = all_tasks[new_phase_id]
    
            start_task.delay(
                task_results, task_metadata, segments=segments, **kwargs
            )
