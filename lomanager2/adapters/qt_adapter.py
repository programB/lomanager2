import sys

from PySide6.QtWidgets import (
    QApplication,
)
from PySide6.QtCore import (
    QObject,
    Signal,
)

from applogic.packagelogic import MainLogic
from applogic.subprocedures import install as install_subprocedure
from gui import AppMainWindow, ProgressDialog
from viewmodels import PackageMenuViewModel
from threads import InstallProcedureWorker


class Adapter(QObject):
    # register custom "refresh" signal (no data passed with it)
    # This is a class attribute (defined before outside __init__)
    refresh = Signal()

    def __init__(self, app_main_model, app_main_view) -> None:
        super().__init__()  # this is important when registering custom events

        # TODO:  Naming: too many different names for the same thing
        #        logic/model/package_menu etc

        self._main_model = app_main_model

        self._main_view = app_main_view
        self._package_menu_view = self._main_view.package_menu_view
        self._extra_langs_view = self._main_view.extra_langs_view.langs_view

        # TODO: adding this extra window just for test
        #       it should be rather defined directly in main_window
        #       like the lang modal
        self.progress_view = ProgressDialog(parent=self._main_view)

        # The viewmodel (PackageMenuViewModel) for the object responsible
        # for dealing with packages selection _main_view
        # is instantiated here.
        # In turn MainLogic object (_main_model) is passed to
        # PackageMenuViewModel constructor to link PackageMenuViewModel
        # to the underlying application logic.
        # This is done here explicitly although PackageMenuViewModel
        # has to now the details of methods exposed by MainLogic
        self._package_menu_viewmodel = PackageMenuViewModel(self._main_model)

        # TODO: Does not exist yet - Implement
        # extra_langs_menu_viewmodel = LangsMenuViewModel()

        # Prepare separate threads that run: apply_changes and
        # install_from_local_copy functions
        # from the MainLogic object (don't start them yet though)
        self.thread_apply_changes = InstallProcedureWorker(
            self._main_model.apply_changes
        )
        self.thread_local_copy_install = InstallProcedureWorker(
            self._main_model.install_from_local_copy
        )

        self._bind_views_to_viewmodels()
        # For the extra buttons outside table views I don't know how to
        # do automatic binding with viewmodel (the way Qt does it)
        # and I have to "manually" connect signals (defined in the view)
        # and slots (defined in the model)
        # TODO: I can potentially define a separate class that does this
        #       to pretend it is my "viewmodel" for this extra buttons
        self._connect_signals_and_slots()

    def _bind_views_to_viewmodels(self):
        self._package_menu_view.setModel(self._package_menu_viewmodel)
        # TODO: Implement - does not exist yet
        # self._extra_langs_view.setModel(self._langs_menu_viewmodel)

    def _connect_signals_and_slots(self):
        # TODO: Will clicking this button at wrong times result in unintended
        #       consequences? Should this be prevented by disabling this button?
        self._main_view.button_apply_changes.clicked.connect(self._apply_changes)
        self.thread_apply_changes.progress.connect(self._progress_was_made)
        self.thread_apply_changes.finished.connect(self._thread_stopped_or_terminated)
        # TODO: connecting to terminate just for tests
        # self.progress_view.button_terminate.clicked.connect(self.thread_apply_changes.stop)
        self.progress_view.button_terminate.clicked.connect(
            self.thread_apply_changes.terminate
        )

        # TODO: And there are buttons inside that modal window.
        #       Should they not be explicitly connected here?
        #       Should not the adapter be the only place that
        #       knows what can be done and how to do it?
        self._main_view.button_add_langs.clicked.connect(
            self._main_view.open_langs_selection_modal_window
        )

        # TODO: Some cleanup procedures should be called here first
        #       like eg. closing the log file.
        #       ...and these should not be called directly of course
        #       but _main_model should be providing that functions.
        self._main_view.button_quit.clicked.connect(self._main_view.close)

        # TODO: test connect "refresh" (custom signal)
        self.refresh.connect(self._do_something_on_refresh)
        # TODO: is the refresh button needed? Connecting it for now
        #       to the same slot as the "refresh" signal which is intended
        #       for automatic (not manual) emission.
        self._main_view.button_install_from_local_copy.clicked.connect(
            self._install_from_local_copy
        )
        self.thread_local_copy_install.finished.connect(self._thread_stopped_or_terminated)

    def _do_something_on_refresh(self):
        print("Refreshing!")

    def _apply_changes(self):
        self.progress_view.show()
        self.thread_apply_changes.start()  # starts the prepared thread

    def _install_from_local_copy(self):
        # self.progress_view.show()
        self.thread_local_copy_install.start()

    def _progress_was_made(self, progress):
        # TODO: print for test purposes, remove later
        print(f"Current progress (received in adapter's slot): {progress}")
        self.progress_view.progress_bar.setValue(progress)

    def _thread_stopped_or_terminated(self):
        # TODO: this methods is most likely not needed at all
        # TODO: print for test purposes, remove later
        print("Thread finished signal received.")
        print(
            f"thread: {self.thread_apply_changes}\n"
            f"is running?: {self.thread_apply_changes.isRunning()}\n"
            f"is finished?: {self.thread_apply_changes.isFinished()}"
            "---\n"
            f"thread: {self.thread_local_copy_install}\n"
            f"is running?: {self.thread_local_copy_install.isRunning()}\n"
            f"is finished?: {self.thread_local_copy_install.isFinished()}"
        )


def main():
    lomanager2App = QApplication([])

    # Model
    app_logic = MainLogic()

    # View
    main_window = AppMainWindow()

    # Adapter
    adapter = Adapter(app_main_model=app_logic, app_main_view=main_window)

    main_window.show()
    sys.exit(lomanager2App.exec())


if __name__ == "__main__":
    main()
