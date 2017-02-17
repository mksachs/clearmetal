# -*- coding: utf-8 -*-
"""Demo tasks to count words in a text file.

"""
import string

import stop_words

import config
import clearmetal.utilities
import clearmetal.app


@clearmetal.utilities.logger(logger_spec=config.logging['app'])
def prep(input, segments=8, **kwargs):
    """

    Args:
        input (str): The path to the file to count words from. 
        segments (int): The number of segments to break the job into. Default: 8.
        **kwargs: Key word args.

    Returns:
        list: List of distributed tasks.

    """

    l = kwargs.get('logger')

    l.info(
        u'#{} Prep word count. Target file: {}.'.format(u'-' * 8, input)
    )
    
    # Read the file in and strip punctuation and newlines. Also remove stop words (if and but etc).
    with open(input, 'r') as myfile:
        text = myfile.read()
    punctuation_table = str.maketrans({key: None for key in string.punctuation})
    whitespace_table = str.maketrans({key: ' ' for key in string.whitespace if key != ' '})
    strip_table = {**punctuation_table, **whitespace_table}
    mod_text = text.lower().translate(strip_table)
    sw = set(stop_words.get_stop_words('en'))
    all_words = [x for x in mod_text.split(' ') if x != '' and x not in sw]
    
    # Just to do a quick verification.
    l.info(
        u'#{} Total words: {}.'.format(u'-' * 12, len(all_words))
    )

    # Divide up the items to process them.
    if len(all_words) > 0:
        l.info(
            u'#{} Segmenting {:,} items into {} segments.'.format(u'-' * 12, len(all_words), segments)
        )
        distributed_tasks = []
        # Distribute the job
        sub_divided_data = clearmetal.utilities.subdivide_list(all_words, segments)
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
    """Counts the words in the input data.

    Args: 
        data (list): A list of words to count. 
        **kwargs: Key word args.

    Returns:
        dict: 'items_processed' (int): The number of words counted.
            'result' (dict): Words and their counts.

    """
    l = kwargs.get('logger')
    do_number = kwargs.get(u'do_number')

    l.info(
        u'#{} Do count words. Segment {}, {} items.'
            .format(
            u'-' * 8, do_number, len(data)
        )
    )

    result = {}
    # Processing logic here
    for word in data:
        if word not in result:
            result[word] = 0
        result[word] += 1

    return {'items_processed': len(data), 'result': result}


@clearmetal.app.app.task(queue='app')
@clearmetal.utilities.logger(logger_spec=config.logging['app'])
def collect(results, **kwargs):
    """Provides a final count of the words from each 'do' sub task and outputs the top 100.

    Args:
        results (list): List of results from the 'do' tasks.
        **kwargs: Key word args.

    Returns:
        list: A list containing the word counts. 

    """
    l = kwargs.get('logger')
    l.info(
        u'#{} Collect word count.'.format(u'-' * 8)
    )

    l.info(
        u'#{} {} results from {} total items.'.format(
            u'-' * 12, len(results), sum([x['items_processed'] for x in results])
        )
    )
    
    final_result = {}
    for result in results:
        for word in result['result']:
            if word not in final_result:
                final_result[word] = result['result'][word]
            else:
                final_result[word] += result['result'][word]

    l.info(
        u'#{} Top 100.'.format(u'-' * 12)
    )
    for word in sorted(final_result, key=lambda x: final_result[x], reverse=True)[0:100]:
        l.info(
            u'#{} {}: {}.'.format(
                u'-' * 16, word, final_result[word]
            )
        )

    return [final_result[key] for key in final_result]
