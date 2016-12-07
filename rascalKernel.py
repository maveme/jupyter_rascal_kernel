from ipykernel.kernelbase import Kernel
import os
from pexpect import replwrap, EOF
import signal


class RascalKernel(Kernel):
    _JAVA_COMMAND = '{}/bin/java'.format(os.environ['JAVA_HOME'])
    _RASCAL_LOCATION = os.environ['RASCAL_LOCATION']

    implementation = ''
    implementation_version = ''
    language = 'Rascal'
    language_version = ''
    banner = language + language_version + '\n'
    language_info = {
        'name': 'rascal',
        'codemirror_mode': 'java',
        'mimetype': 'text/x-java',
        'file_extension': '.rsc'
    }

    def __init__(self, **kwargs):
        Kernel.__init__(self, **kwargs)
        self._start_rascal()

    def _start_rascal(self):
        sig = signal.signal(signal.SIGINT, signal.SIG_DFL)
        try:
            self.rascal_wrapper = replwrap.REPLWrapper("{} -jar {}".format(self._JAVA_COMMAND,
                                                                           self._RASCAL_LOCATION
                                                                           ), "rascal>", None)
        finally:
            signal.signal(signal.SIGINT, sig)

    def do_execute(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=False):
        if not code.strip():
            return {
                'status': 'OK',
                'execution_count': self.execution_count,
                'payload': [],
                'user_expressions': {}
            }
        interrupted = False
        try:
            output = self.rascal_wrapper.run_command(code.rstrip(), timeout=None)
        except KeyboardInterrupt:
            self.rascal_wrapper.child.sendintr()
            interrupted = True
            self.rascal_wrapper._expect_prompt()
            output = self.rascal_wrapper.child.before
        except EOF:
            output = self.rascal_wrapper.child.before + 'Restarting Rascal'
            self._start_rascal()
        if not silent:
            stream_content = {'name': 'stdout', 'text': output}
            self.send_response(self.iopub_socket, 'stream', stream_content)
        if interrupted:
            return 'Abort'
        try:
            exitcode = int(self.rascal_wrapper.run_command('1').rstrip())
        except Exception:
            exitcode = 1

        if exitcode:
            error_content = {'execution_count': self.execution_count,
                             'ename': '', 'evalue': str(exitcode),
                             'traceback': []}

            self.send_response(self.iopub_socket, 'error', error_content)
            error_content['status'] = 'Exception'
            return error_content
        else:
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payload': [], 'user_expressions': {}}