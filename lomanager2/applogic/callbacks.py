import gettext
import logging

t = gettext.translation("lomanager2", localedir="./locales", fallback=True)
_ = t.gettext
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
        self._last_seen_progress_dsc = ""

        self.step_start = self._step_start_closure()
        self.step_skip = self._step_skip_closure()
        self.step_end = self._step_end_closure()
        self.progress = self._progress_closure()
        self.progress_msg = self._progress_msg_closure()

    def _step_start_closure(self):
        if (self._overall_progress_dsc_callback is not None) and (
            self._overall_progress_prc_callback is not None
        ):

            def step_start(txt: str):
                # When starting a new step clear/reset the
                # fine grained progress indicator first
                self.progress(0)
                self.progress_msg("", show_msg=False)
                # Save description to reuse it in step_end
                if txt:
                    txt = txt[0].upper() + txt[1:]
                self._current_step_description = txt
                # Set step name
                log.info(txt + " ...")
                self._overall_progress_dsc_callback(txt + " ...")

        else:

            def step_start(txt: str):
                self.progress(0)
                self.progress_msg("", show_msg=False)
                self._current_step_description = txt
                log.info(txt)

        return step_start

    def _step_skip_closure(self):
        if (self._overall_progress_dsc_callback is not None) and (
            self._overall_progress_prc_callback is not None
        ):

            def step_skip(txt: str):
                # Skipping a step is the same as
                # starting it and immediately ending
                # but without logging the step_end message
                self.step_start(txt)
                self.step_end(show_msg=False)

        else:

            def step_skip(txt: str):
                self.step_start(txt)
                self.step_end()

        return step_skip

    def _step_end_closure(self):
        if (self._overall_progress_dsc_callback is not None) and (
            self._overall_progress_prc_callback is not None
        ):

            def step_end(txt: str = "", show_msg=True):
                self._steps_counter += 1
                self._overall_progress_prc_callback(self._steps_counter)
                msg = (
                    txt
                    if txt
                    else _("... done ") + self._current_step_description.lower()
                )
                if show_msg:
                    log.info(msg)
                    self._overall_progress_dsc_callback(msg)

        else:

            def step_end(txt: str = "", show_msg=True):
                self._steps_counter += 1
                msg = (
                    txt if txt else "... done " + self._current_step_description.lower()
                )
                if show_msg:
                    log.info(msg)

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

            def progress_description(txt: str, prc: str = "", show_msg=True):
                if show_msg:
                    self._progress_dsc_callback(txt)
                    msg = rf"{txt} ({prc})%" if prc else txt
                    if txt == self._last_seen_progress_dsc:
                        log.debug(msg)
                    else:
                        self._last_seen_progress_dsc = txt
                        log.info(txt)

        else:

            def progress_description(txt: str, prc: str = "", show_msg=True):
                if show_msg:
                    msg = rf"{txt} ({prc})%" if prc else txt
                    if txt == self._last_seen_progress_dsc:
                        log.debug(msg)
                    else:
                        self._last_seen_progress_dsc = txt
                        log.info(txt)

        return progress_description
