import logging

log = logging.getLogger("lomanager2_logger")


class UnifiedProgressReporter:
    def __init__(self, total_steps: int, callbacks={}):
        self._steps_counter = 0
        self._current_step_description = ""
        self._total_steps = total_steps

        self._overall_progress_dsc_callback = callbacks.get(
            "overall_progress_description"
        )
        self._overall_progress_prc_callback = callbacks.get(
            "overall_progress_percentage"
        )
        self._progress_dsc_callback = callbacks.get("progress_description")
        self._progress_prc_callback = callbacks.get("progress_percentage")

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
                # When starting a new step clear/reset the
                # fine grained progress indicator first
                self.progress(0)
                self.progress_msg("")
                # Save description to reuse it in step_end
                self._current_step_description = txt
                # Set step name
                log.info(txt)
                self._overall_progress_dsc_callback(txt)

        else:

            def step_start(txt: str = ""):
                self.progress(0)
                self.progress_msg("")
                self._current_step_description = txt
                log.info(txt)

        return step_start

    def _step_skip_closure(self):
        if (self._overall_progress_dsc_callback is not None) and (
            self._overall_progress_prc_callback is not None
        ):

            def step_skip(txt: str = ""):
                # Skipping a step is the same as
                # starting it and immediately ending
                self.step_start(txt)
                self.step_end()

        else:

            def step_skip(txt: str = ""):
                self.step_start(txt)
                self.step_end()

        return step_skip

    def _step_end_closure(self):
        if (self._overall_progress_dsc_callback is not None) and (
            self._overall_progress_prc_callback is not None
        ):

            def step_end(txt: str = ""):
                msg = txt if txt else self._current_step_description + " ...done"
                log.info(msg)
                self._overall_progress_dsc_callback(msg)
                self._steps_counter += 1
                self._overall_progress_prc_callback(
                    int(100 * (self._steps_counter / self._total_steps))
                )

        else:

            def step_end(txt: str = ""):
                msg = txt if txt else self._current_step_description + " ...done"
                log.info(msg)
                self._steps_counter += 1

        return step_end

    def _progress_closure(self):
        if (
            self._progress_dsc_callback is not None
            and self._progress_prc_callback is not None
        ):

            def progress(percentage: int):
                self._progress_prc_callback(percentage)

        else:

            def progress(percentage: int):
                pass

        return progress

    def _progress_msg_closure(self):
        if (
            self._progress_dsc_callback is not None
            and self._progress_prc_callback is not None
        ):

            def progress_description(txt: str):
                log.info(txt)
                self._progress_dsc_callback(txt)

        else:

            def progress_description(txt: str):
                log.info(txt)

        return progress_description
