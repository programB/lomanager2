import logging

log = logging.getLogger("lomanager2_logger")


class OverallProgressReporter:
    def __init__(self, total_steps: int, callbacks={}):
        self.callbacks = callbacks
        self.counter = 0
        self.n_steps = total_steps

    def _overall_progress_description(self, txt: str):
        log.info(txt)
        if "overall_progress_description" in self.callbacks.keys():
            self.callbacks["overall_progress_description"](txt)

    def _overall_progress_percentage(self, percentage: int):
        # TODO: Should progress % be logged ?
        if "overall_progress_percentage" in self.callbacks.keys():
            self.callbacks["overall_progress_percentage"](percentage)

    def start(self, txt: str = ""):
        if txt:
            self._overall_progress_description(txt)

    def skip(self, txt: str = ""):
        if txt:
            self._overall_progress_description(txt)
        self.end()

    def end(self, txt: str = ""):
        if txt:
            self._overall_progress_description(txt)
        self.counter += 1
        self._overall_progress_percentage(int(100 * (self.counter / self.n_steps)))


def progress_closure(callbacks: dict):
    if "progress_percentage" in callbacks.keys():
        progressfunc = callbacks["progress_percentage"]

        def progress(percentage: int):
            progressfunc(percentage)

    else:

        def progress(percentage: int):
            pass

    return progress


def progress_description_closure(callbacks: dict):
    if "progress_description" in callbacks.keys():
        progressdescfunc = callbacks["progress_description"]

        def progress_description(txt: str):
            log.info(txt)
            progressdescfunc(txt)

    else:

        def progress_description(txt: str):
            log.info(txt)

    return progress_description
