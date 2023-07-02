import sys

from PySide6.QtWidgets import (
    QApplication,
)
from PySide6.QtCore import (
    QObject,
    QThreadPool,
    Slot,
    Signal,
)

from applogic.packagelogic import MainLogic
from gui import AppMainWindow
from viewmodels import PackageMenuViewModel
from threads import InstallProcedureWorker

class Adapter(QObject):
    # register custom "refresh" signal (no data passed with it)
    # This is a class attribute (defined before outside __init__)
    refresh = Signal()

    def __init__(self, app_main_model, app_main_view) -> None:
        super().__init__()  # this is important when registering custom events

        # Prepare capacity for running some code in separate thread
        self.threadpool = QThreadPool()

        # TODO:  Naming: too many different names for the same thing
        #        logic/model/package_menu etc

        self._main_model = app_main_model

        self._main_view = app_main_view
        self._package_menu_view = self._main_view.package_menu_view
        self._extra_langs_view = self._main_view.extra_langs_view.langs_view

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
        # TODO: 1) the model should Implement the gather_system_info
        #       2) clicking this button at wrong times may have unintended
        #          consequences. It is model's responsibility to decide whether
        #          handling this signal makes sense (it can be directly in the
        #          gather_system_info procedure perhaps.)
        #       3) Is Qt queueing signals? Will this result in
        #          many events triggered if the signal gets ignored?
        # self._main_view.button_refresh.clicked.connect(
        #     self._main_model.gather_system_info
        # )

        # TODO: 1) Implement
        self._main_view.button_apply_changes.clicked.connect(self._apply_changes)

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

    def _do_something_on_refresh(self):
        print("Refreshing!")

    def _apply_changes(self):
        # TODO: This is not the way to do it. Implement
        self.threadpool.start(self.apply_in_external_thread)
        # Simulate thread finishing here
        # (I know this should be emitted from within the thread
        # not here - test only)
        self.refresh.emit()

    # The reason why connect does not call this method directly
    # but instead calls a an intermediate self._apply_changes first
    # is the have the @Slot() decorator kept in this file and not
    # import it in the MainLogic module
    # This way MainLogic is independent from any Qt realated stuff.
    @Slot()
    def apply_in_external_thread(self):
        self._main_model.apply_changes()


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
