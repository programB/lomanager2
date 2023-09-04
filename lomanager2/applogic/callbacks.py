import logging

log = logging.getLogger("lomanager2_logger")


class UnifiedProgressReporter:
    def __init__(self, total_steps: int, callbacks={}):
        self._callbacks = callbacks
        self._counter = 0
        self._n_steps = total_steps

        self._overall_progress_dsc_callback = self._callbacks.get(
            "overall_progress_description"
        )
        self._overall_progress_prc_callback = self._callbacks.get(
            "overall_progress_percentage"
        )

        self.step_start = self._step_start_closure()
        self.step_skip = self._step_skip_closure()
        self.step_end = self._step_end_closure()
        self.progress = self._progress_closure()
        self.progress_msg = self._progress_msg_closure()

    def _step_start_closure(self):
        if (self._overall_progress_dsc_callback is not None) and (
            self._overall_progress_prc_callback is not None
        ):

            def step_start(txt: str = ""):
                if txt:
                    log.info(txt)
                    self._overall_progress_dsc_callback(txt)

        else:

            def step_start(txt: str = ""):
                if txt:
                    log.info(txt)

        return step_start

    def _step_skip_closure(self):
        if (self._overall_progress_dsc_callback is not None) and (
            self._overall_progress_prc_callback is not None
        ):

            def step_skip(txt: str = ""):
                if txt:
                    log.info(txt)
                    self._overall_progress_dsc_callback(txt)
                self.step_end()

        else:

            def step_skip(txt: str = ""):
                if txt:
                    log.info(txt)
                self.step_end()

        return step_skip

    def _step_end_closure(self):
        if (self._overall_progress_dsc_callback is not None) and (
            self._overall_progress_prc_callback is not None
        ):

            def step_end(txt: str = ""):
                if txt:
                    log.info(txt)
                    self._overall_progress_dsc_callback(txt)
                self._counter += 1
                self._overall_progress_prc_callback(
                    int(100 * (self._counter / self._n_steps))
                )

        else:

            def step_end(txt: str = ""):
                if txt:
                    log.info(txt)
                self._counter += 1

        return step_end

    def _progress_closure(self):
        if "progress_percentage" in self._callbacks.keys():

            def progress(percentage: int):
                self._callbacks["progress_percentage"](percentage)

        else:

            def progress(percentage: int):
                pass

        return progress

    def _progress_msg_closure(self):
        if "progress_description" in self._callbacks.keys():

            def progress_description(txt: str):
                log.info(txt)
                self._callbacks["progress_description"](txt)

        else:

            def progress_description(txt: str):
                log.info(txt)

        return progress_description
