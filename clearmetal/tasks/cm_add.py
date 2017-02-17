# -*- coding: utf-8 -*-
"""Demo tasks to add numbers.

"""

import config
import clearmetal.utilities
import clearmetal.app


@clearmetal.utilities.logger(logger_spec=config.logging['app'])
def prep(input, segments=8, **kwargs):
    """Prepares the adding job by segmenting the input list into sub lists and sending each sub list to the 'do' task.

    Args:
        input (list): A list of numbers to add together. 
        segments (int): The number of segments to break the job into. Default: 8.
        **kwargs: Key word args.

    Returns:
        list: List of distributed tasks.

    """
    
    l = kwargs.get('logger')

    l.info(
        u'#{} Prep ADD. Total items: {}.'.format(u'-' * 8, len(input))
    )
    
    # Just to do a quick verification.
    l.info(
        u'#{} Actual result: {}.'.format(u'-' * 12, sum(input))
    )
    
    # Divide up the items to process them.
    if len(input) > 0:
        l.info(
            u'#{} Segmenting {:,} items into {} segments.'.format(u'-' * 12, len(input), segments)
        )
        distributed_tasks = []
        # Distribute the job
        sub_divided_data = clearmetal.utilities.subdivide_list(input, segments)
        for do_number, sub_data in enumerate(sub_divided_data):
            distributed_tasks.append(
                do.s(
                    sub_data,
                    do_number=do_number
                )
            )

        return distributed_tasks
    else:
        l.info(
            u'#{} No numbers to add.'.format(u'-' * 12)
        )

        return []


@clearmetal.app.app.task(queue='app', default_retry_delay=60, max_retries=10)
@clearmetal.utilities.logger(logger_spec=config.logging['app'])
def do(data, **kwargs):
    """Adds all the numbers in 'data' together and returns the results.

    Args: 
        data (list): A list of numbers to add together. 
        **kwargs: Key word args.

    Returns:
        dict: 'items_processed' (int): The number of numbers added together.
            'result' (int, float): The sum of the numbers.

    """
    l = kwargs.get('logger')
    do_number = kwargs.get(u'do_number')

    l.info(
        u'#{} Do ADD. Segment {}, {} items.'
        .format(
            u'-' * 8, do_number, len(data)
        )
    )
    
    # Processing logic here
    result = sum(data)

    return {'items_processed': len(data), 'result': result}


@clearmetal.app.app.task(queue='app')
@clearmetal.utilities.logger(logger_spec=config.logging['app'])
def collect(results, **kwargs):
    """Collects the results from the distributed tasks and adds them together for a final sum.

    Args:
        results (list): Results from the 'do' process.
        **kwargs: Key word args.

    Returns:
        int, float: The final sum. 

    """
    l = kwargs.get('logger')
    l.info(
        u'#{} Collect ADD.'.format(u'-' * 8)
    )

    l.info(
        u'#{} {} results from {} total items.'.format(
            u'-' * 12, len(results), sum([x['items_processed'] for x in results])
        )
    )
    
    final_result = sum([x['result'] for x in results])

    l.info(
        u'#{} Final result: {}.'.format(
            u'-' * 12, final_result
        )
    )

    return final_result
