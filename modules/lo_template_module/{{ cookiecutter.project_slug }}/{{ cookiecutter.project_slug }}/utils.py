'''
This file contains functions that are common across your package.
'''

def increment(i):
    '''
    Increment passed in variable `i`. Raise an exception if it fails.

    Simple use case
    >>> increment(1)
    2

    Raise an exception on increment error.
    >>> increment('abc')
    Traceback (most recent call last):
        ...
    Exception: Unable to increment: invalid literal for int() with base 10: 'abc'
    '''
    try:
        return int(i) + 1
    except Exception as e:
        raise Exception(f'Unable to increment: {e}')


if __name__ == "__main__":
    # Run doctests
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
