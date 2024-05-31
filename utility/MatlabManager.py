"""
This class provides a set of static methods to manage Matlab sessions and execute Matlab functions.

The class provides the following methods:

    start_matlab: Starts a new Matlab session or connects to an existing one.

    call_matlab_function: Calls a Matlab function and returns the result.

    call_matlab_function_noret: Calls a Matlab function that does not return a value.

    call_matlab_spmbatch: Calls a SPM batch file that does not return a value.

The class can be used as follows:

import matlab.engine
import os

# Start a new Matlab session
eng = MatlabManager.start_matlab()

# Add the current directory to the Matlab path
eng.addpath(os.path.dirname(__file__))

# Call a Matlab function and get the result
result = MatlabManager.call_matlab_function('myfunction', params='param1, param2')

# Disconnect from the Matlab session
eng.quit()

# Call a Matlab function that does not return a value
MatlabManager.call_matlab_function_noret('myfunction2')

# Call a SPM batch file
MatlabManager.call_matlab_spmbatch('myspmbatchfile')
"""
import os
import subprocess
from random import randint

import matlab.engine
import matlab.engine.engineerror


class MatlabManager:
    """
    A class for managing Matlab sessions and running Matlab functions.

    Attributes:
        None

    Methods:
        start_matlab: Starts a new Matlab session or connects to an existing one.
        call_matlab_function: Runs a Matlab function and returns the result.
        call_matlab_function_noret: Runs a Matlab function that does not return a result.
        call_matlab_spmbatch: Runs a SPM batch file that does not return a result.

    """

    SESSION_NEW_PERSISTENT = 1
    SESSION_NEW_NOTSHARED = 2
    SESSION_REUSE_FIRST = 3
    SESSION_REUSE_NAME = 4

    @staticmethod
    def start_matlab(paths2add=None, sess_type=SESSION_REUSE_FIRST, conn2existing:str=""):
        """
        Starts a new Matlab session or connects to an existing one.

        Args:
            paths2add (list): A list of paths to add to the Matlab search path.
            sess_type (int): The type of Matlab session to start.
                Possible values are:
                    SESSION_NEW_PERSISTENT: Starts a new NOT-SHARED Matlab session.
                    SESSION_NEW_NOTSHARED: Starts a new SHARED Matlab session.
                    SESSION_REUSE_FIRST: Tries to reuse the first available Matlab session.
                    SESSION_REUSE_NAME: Tries to reuse the Matlab session with the given name.
            conn2existing (str): The name of an existing shared Matlab session to connect to.

        Returns:
            The Matlab engine object, or None if the session could not be started.

        Raises:
            Exception: If the Matlab session could not be started.

        """
        if paths2add is None:
            paths2add = []

        if sess_type == MatlabManager.SESSION_NEW_PERSISTENT:
            if len(conn2existing) == 0:
                conn2existing = "persistentSession" + str(randint(1, 10000))

            # os.system('matlab -r \"matlab.engine.shareEngine(''' + conn2existing + ')\"')
            # os.system('matlab -r \"matlab.engine.shareEngine\"')
            # process = subprocess.run(['matlab', '-r', 'matlab.engine.shareEngine(\"' + conn2existing + '\")'])
            subprocess.run(['matlab', '-r \"matlab.engine.shareEngine\"'])

            # rrun("matlab -r \"matlab.engine.shareEngine(\'" + conn2existing + "\')\"")
            while True:
                existing_sessions = matlab.engine.find_matlab()
                if conn2existing in existing_sessions:
                    eng = matlab.engine.connect_matlab(conn2existing)
                    break
            raise Exception("matlab session not found")

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
    def call_matlab_function(func, standard_paths=None, params:str="", logfile=None, endengine:bool=True, eng=None):
        """
        Runs a Matlab function and returns the result.

        Args:
            func (str): The path to the Matlab function to run.
            standard_paths (list): A list of paths to add to the Matlab search path.
            params (str): The parameters to pass to the Matlab function.
            logfile (file): A file object to write log messages to.
            endengine (bool): Whether to end the Matlab engine after running the function.
            eng (object): An existing Matlab engine object to use for the function call.

        Returns:
            A list containing the Matlab engine object and the function result.

        Raises:
            Exception: If the Matlab function could not be run.

        """
        if standard_paths is None:
            standard_paths = []
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

        if endengine:
            engine.quit()
            print("quitting matlab session of " + batch_file)

        return [engine, res]

    @staticmethod
    def call_matlab_function_noret(func, standard_paths=None, params:str="", logfile=None, endengine:bool=True, eng=None):
        """
        Runs a Matlab function that does not return a result.

        Args:
            func (str): The path to the Matlab function to run.
            standard_paths (list): A list of paths to add to the Matlab search path.
            params (str): The parameters to pass to the Matlab function.
            logfile (file): A file object to write log messages to.
            endengine (bool): Whether to end the Matlab engine after running the function.
            eng (object): An existing Matlab engine object to use for the function call.

        Returns:
            The Matlab engine object.

        Raises:
            Exception: If the Matlab function could not be run.

        """
        if standard_paths is None:
            standard_paths = []
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

        if endengine:
            engine.quit()
            print("quitting matlab session of " + batch_file)

        return engine

    @staticmethod
    def call_matlab_spmbatch(func, standard_paths=None, logfile=None, endengine:bool=True, eng=None):
        """
        Runs a SPM batch file that does not return a result.

        Args:
            func (str): The path to the SPM batch file to run.
            standard_paths (list): A list of paths to add to the Matlab search path.
            logfile (file): A file object to write log messages to.
            endengine (bool): Whether to end the Matlab engine after running the function.
            eng (object): An existing Matlab engine object to use for the function call.

        Returns:
            The Matlab engine object.

        Raises:
            Exception: If the SPM batch file could not be run.

        """
        if standard_paths is None:
            standard_paths = []
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

            if endengine:
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
    # def call_matlab_function(functions, params, standard_paths, logfile=None, endengine:bool=True):
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
    #     if endengine:
    #         engine.quit()
    #         print("quitting matlab session")
    #
