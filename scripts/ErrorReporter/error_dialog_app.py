import sys
import argparse

parser = argparse.ArgumentParser(description='Pass in exit_code')
parser.add_argument('--exitcode', dest='exit_code')
parser.add_argument('--directory', dest='directory')
command_line_args = parser.parse_args()

sys.path.insert(0, command_line_args.directory)

from PyQt4 import QtGui # noqa

import mantid # noqa
from ErrorReporter import resources # noqa
from mantid.kernel import UsageService # noqa
from ErrorReporter.error_report_presenter import ErrorReporterPresenter # noqa
from ErrorReporter.errorreport import CrashReportPage # noqa


def main():
    if not UsageService.isEnabled():
        return int(command_line_args.exit_code)
    app = QtGui.QApplication(sys.argv)
    form = CrashReportPage(show_continue_terminate=False)
    ErrorReporterPresenter(form, command_line_args.exit_code)
    app.exec_()
    return int(command_line_args.exit_code)

if __name__ == '__main__':              # if we're running file directly and not importing it
    sys.exit(main())                              # run the main function
