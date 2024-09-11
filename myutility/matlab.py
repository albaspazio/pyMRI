"""
This module provides functions for interacting with MATLAB from Python.
The functions in this module can be divided into two categories:
those that start a MATLAB session
    - start_matlab: Starts a new MATLAB session or connects to an existing one.
and those that do not.
    - call_matlab_function: Calls a MATLAB function that returns a value.
    - call_matlab_function_noret: Calls a MATLAB function that does not return a value.
    - call_matlab_spmbatch: Calls a SPM batch file that does not return a value.

Example usage:

import matlab_interface

# Start a new MATLAB session
eng = matlab_interface.start_matlab()

# Call a MATLAB function that returns a value
res = matlab_interface.call_matlab_function('my_matlab_function', eng=eng, params='param1, param2')

# Call a MATLAB function that does not return a value
matlab_interface.call_matlab_function_noret('my_matlab_function', eng=eng, params='param1, param2')

# Call a SPM batch file that does not return a value
matlab_interface.call_matlab_spmbatch('my_spm_batch.m', eng=eng)

# End the MATLAB session
eng.quit()

Note that the actual function names and arguments may vary slightly depending on the specific MATLAB version and environment.
"""

# from matlab.engine import
import os

import matlab.engine
import matlab.engine.engineerror


# start a new matlab session (if no session are active) or connect to the first one available or return None.
def start_matlab(paths2add=None, conn2first:bool=True):
    """
    Starts a new MATLAB session or connects to an existing one.

    Args:
        paths2add (list, optional): A list of paths to add to the MATLAB path.
        conn2first (bool, optional): If True, connects to the first MATLAB session found, otherwise starts a new session.

    Returns:
        The MATLAB engine object, or None if no session could be started.
    """
    if paths2add is None:
        paths2add = []
    existing_sessions = matlab.engine.find_matlab()

    if len(existing_sessions) > 0:
        if conn2first:
            eng = matlab.engine.connect_matlab(existing_sessions[0])
        else:
            print("More than one matlab sessions are presently open...returning")
            return None

    else:
        print("opening matlab session")
        eng = matlab.engine.start_matlab()
        print("matlab session opened")

    for path in paths2add:
        eng.addpath(path)
    return eng


def call_matlab_function(func, standard_paths=None, params:str="", logfile=None, endengine:bool=True, eng=None):
    """
    Calls a MATLAB function that returns a value.

    Args:
        func (str): The name of the MATLAB function to call.
        standard_paths (list, optional): A list of paths to add to the MATLAB path.
        params (str, optional): The parameters to pass to the MATLAB function.
        logfile (file, optional): A file object for logging output.
        endengine (bool, optional): If True, ends the MATLAB session after the function call.
        eng (matlab.engine.base.Engine, optional): The MATLAB engine object to use for the function call.

    Returns:
        A list containing two elements: the first element is the MATLAB engine object (if the function ended the session), and the second element is the return value of the MATLAB function.

    Raises:
        MatlabExecutionError: If the function call fails.
    """
    if standard_paths is None:
        standard_paths = []
    if eng is None:
        engine = start_matlab(standard_paths)
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
        engine = None
        print("quitting matlab session of " + batch_file)

    return [engine, res]


def call_matlab_function_noret(func, standard_paths=None, params:str="", logfile=None, endengine:bool=True, eng=None):
    """
    Calls a MATLAB function that does not return a value.

    Args:
        func (str): The name of the MATLAB function to call.
        standard_paths (list, optional): A list of paths to add to the MATLAB path.
        params (str, optional): The parameters to pass to the MATLAB function.
        logfile (file, optional): A file object for logging output.
        endengine (bool, optional): If True, ends the MATLAB session after the function call.
        eng (matlab.engine.base.Engine, optional): The MATLAB engine object to use for the function call.

    Returns:
        The MATLAB engine object (if the function ended the session).

    Raises:
        MatlabExecutionError: If the function call fails.
    """
    if standard_paths is None:
        standard_paths = []
    if eng is None:
        engine = start_matlab(standard_paths)
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
        engine = None
        print("quitting matlab session of " + batch_file)

    return engine


# subcase of call_matlab_function_noret: call a SPM batch file that does not return anything
def call_matlab_spmbatch(func, standard_paths=None, logfile=None, endengine:bool=True, eng=None):
    """
    Calls a SPM batch file that does not return a value.

    Args:
        func (str): The name of the SPM batch file to call.
        standard_paths (list, optional): A list of paths to add to the MATLAB path.
        logfile (file, optional): A file object for logging output.
        endengine (bool, optional): If True, ends the MATLAB session after the function call.
        eng (matlab.engine.base.Engine, optional): The MATLAB engine object to use for the function call.

    Returns:
        The MATLAB engine object (if the function ended the session).

    Raises:
        MatlabExecutionError: If the function call fails.
    """
    if standard_paths is None:
        standard_paths = []
    batch_file = os.path.basename(os.path.splitext(func)[0])
    # err = io.StringIO

    try:
        if eng is None:
            engine = start_matlab(standard_paths)
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
            engine = None
            print("quitting matlab session of " + batch_file)

        os.remove(func)
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
