import datetime
import traceback


class DAGExecutionException(Exception):
    '''
    Exception for errors raised during the execution of the dag

    Generating the tracebacks may cause a decrease in performance.
    TODO profile this code and determine how we should handle tracebacks.
    Possibilities:
    - hide traceback behind a feature flag (possibly the same
      flag that determines if we show the error json on each of
      the dashboards)
    - create an exponential backoff strategy that only records the
      traceback every so many times that a specific error occurs
    - do nothing if there is not a performance decrease

    Attributes:
        function -- the function causing the error
        error_provenance -- any items that may be useful for debugging the error
        timestamp -- when the error occured
        traceback -- traceback object for error
    '''

    def __init__(self, error, function, provenance, traceback=None):
        self.error = error
        self.function = function
        self.provenance = provenance
        self.traceback = traceback

    def to_dict(self):
        # TODO create serialize/deserialize methods for traceback
        tb = self.traceback
        if hasattr(self, '__traceback__'):
            tb = self.__traceback__ if tb is None else tb
        return {
            'error': self.error,
            'function': self.function,
            'error_provenance': self.provenance,
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'traceback': ''.join(traceback.format_tb(tb))
        }
