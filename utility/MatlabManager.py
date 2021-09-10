# from matlab.engine import
import os
import subprocess
from random import randint

import matlab.engine
import matlab.engine.engineerror


class MatlabManager:
    SESSION_NEW_PERSISTENT = 1
    SESSION_NEW_NOTSHARED = 2
    SESSION_REUSE_FIRST = 3
    SESSION_REUSE_NAME = 4

    # start a new matlab session or connect to an existing one:
    #   persistent=False : start a new NOT-SHARED one if not existing or connect to an existing SHARED (given by conn2existing) or the first available
    #   persistent=True  :
    #
    # (if no session are active) or connect to the first one available or return None.

    @staticmethod
    def start_matlab(paths2add=[], sess_type=SESSION_REUSE_FIRST, conn2existing=""):

        if sess_type == MatlabManager.SESSION_NEW_PERSISTENT:
            if len(conn2existing) == 0:
                conn2existing = "persistentSession" + str(randint(1, 10000))

            # os.system('matlab -r \"matlab.engine.shareEngine(''' + conn2existing + ')\"')
            # os.system('matlab -r \"matlab.engine.shareEngine\"')
            # process = subprocess.run(['matlab', '-r', 'matlab.engine.shareEngine(\"' + conn2existing + '\")'])
            process = subprocess.run(['matlab', '-r \"matlab.engine.shareEngine\"'])

            # rrun("matlab -r \"matlab.engine.shareEngine(\'" + conn2existing + "\')\"")
            while True:
                existing_sessions = matlab.engine.find_matlab()
                if conn2existing in existing_sessions:
                    eng = matlab.engine.connect_matlab(conn2existing)
                    break

        elif sess_type == MatlabManager.SESSION_NEW_NOTSHARED:
            eng = matlab.engine.start_matlab()
            print("new NOT-SHARED matlab session opened")

        elif sess_type == MatlabManager.SESSION_REUSE_FIRST:
            # try to reuse existing engine
            existing_sessions = matlab.engine.find_matlab()
            if len(existing_sessions) > 0:
                eng = matlab.engine.connect_matlab(existing_sessions[0])  # reuse first
                print("reusing SHARED matlab session " + existing_sessions[0])
            else:
                eng = matlab.engine.connect_matlab()  # create new shared
                print("new SHARED matlab session opened")

        elif sess_type == MatlabManager.SESSION_REUSE_NAME:

            if conn2existing is "":
                print("WARNING in start_matlab: given session does not exist, using the first available")
                return MatlabManager.start_matlab(paths2add, MatlabManager.SESSION_REUSE_FIRST)
            else:
                existing_sessions = matlab.engine.find_matlab()
                if conn2existing in existing_sessions:
                    eng = matlab.engine.connect_matlab(conn2existing)
                    print("reusing SHARED matlab session " + conn2existing)
                else:
                    print("WARNING in start_matlab: given session does not exist, using the first available")
                    return MatlabManager.start_matlab(paths2add, MatlabManager.SESSION_REUSE_FIRST)

        for path in paths2add:
            eng.addpath(path)
        return eng

    @staticmethod
    def call_matlab_function(func, standard_paths=[], params="", logfile=None, endengine=True, eng=None):

        if eng is None:
            engine = MatlabManager.start_matlab(standard_paths)
            if engine is None:
                return
        else:
            engine = eng

        # add file path to matlab
        engine.addpath(os.path.dirname(func))
        batch_file = os.path.basename(os.path.splitext(func)[0])

        print("running matlab function: " + batch_file, file=logfile)
        res = eval("engine." + batch_file + "(" + params + ")")

        if endengine is True:
            engine.quit()
            print("quitting matlab session of " + batch_file)

        return [engine, res]

    @staticmethod
    def call_matlab_function_noret(func, standard_paths=[], params="", logfile=None, endengine=True, eng=None):

        if eng is None:
            engine = MatlabManager.start_matlab(standard_paths, MatlabManager.SESSION_REUSE_FIRST)
            if engine is None:
                return
        else:
            engine = eng

        if params == "":
            str_params = "(nargout=0)"
        else:
            str_params = "(" + params + ",nargout=0)"

        batch_file = os.path.basename(os.path.splitext(func)[0])
        # add file path to matlab
        engine.addpath(os.path.dirname(batch_file))

        print("running matlab function: " + batch_file, file=logfile)
        eval("engine." + batch_file + str_params)

        if endengine is True:
            engine.quit()
            print("quitting matlab session of " + batch_file)

        return engine

    # subcase of call_matlab_function_noret: call a SPM batch file that does not return anything
    @staticmethod
    def call_matlab_spmbatch(func, standard_paths=[], logfile=None, endengine=True, eng=None):

        batch_file = os.path.basename(os.path.splitext(func)[0])
        # err = io.StringIO

        try:
            if eng is None:
                engine = MatlabManager.start_matlab(standard_paths)
                if engine is None:
                    return
            else:
                engine = eng

            # add file path to matlab
            engine.addpath(os.path.dirname(func))

            print("running SPM batch template: " + func, file=logfile)
            eval("engine." + batch_file + "(nargout=0)")
            # eval("engine." + batch_file + "(nargout=0, stderr=err)")

            if endengine is True:
                engine.quit()
                print("quitting matlab session of " + batch_file)

            return engine

        except Exception as e:
            print("error in " + batch_file)
            # print(err.getvalue())
            print(e)
            exit()

        #
        # def _execute_sync(self, code):
        #     out = io.StringIO()
        #     err = io.StringIO()
        #     if not isinstance(code, str):
        #         code = code.encode('utf8')
        #     try:
        #         self._matlab.eval(code, nargout=0, stdout=out, stderr=err)
        #     except (SyntaxError, MatlabExecutionError) as exc:
        #         stdout = exc.args[0]
        #         self.Error(stdout)
        #         raise exc
        #     stdout = out.getvalue()
        #     self.Print(stdout)
        #
        #

    # attempt to create a multipurpose method that receive a list of functions/params/return types
    # def call_matlab_function(functions, params, standard_paths, logfile=None, endengine=True):
    #
    #     nfunc   = len(functions)
    #     nparams = len(params)
    #
    #     if nparams == 1:
    #         params = [params[0]] * nfunc
    #     else:
    #         if nfunc != nparams:
    #             print("Error in call_matlab_function")
    #
    #
    #     engine = start_matlab(standard_paths)
    #     if engine is None:
    #         return
    #
    #     for f in range(nfunc):
    #
    #         # add file path to matlab
    #         engine.addpath(os.path.dirname(functions[f]))
    #
    #         if params[f] is None:
    #             params_str = "(nargout=0)"
    #         else:
    #             params_str = "(" + params[f] + ")"
    #         eval("engine." + os.path.basename(os.path.splitext(functions[f])[0]) + "(nargout=0)")
    #
    #     if endengine is True:
    #         engine.quit()
    #         print("quitting matlab session")
    #
