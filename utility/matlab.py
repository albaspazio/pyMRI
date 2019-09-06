import matlab.engine
import os


# start a new matlab session (if no session are active) or connect to the first one available or return None.
def start_matlab(paths2add, conn2first=True):

    existing_sessions = matlab.engine.find_matlab()

    if len(existing_sessions) > 0:
        if conn2first is True:
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


def call_matlab_function(func, standard_paths, params="", logfile=None, endengine=True):

    engine = start_matlab(standard_paths)
    if engine is None:
        return

    # add file path to matlab
    engine.addpath(os.path.dirname(func))
    print("running matlab function: " + func, file=logfile)
    res = eval("engine." + os.path.basename(os.path.splitext(func)[0]) + "(" + params + ")")

    if endengine is True:
        engine.quit()
        print("quitting matlab session")

    return [engine, res]


def call_matlab_function_noret(func, standard_paths, params="", logfile=None, endengine=True):

    engine = start_matlab(standard_paths)
    if engine is None:
        return

    if params == "":
        str_params = "(nargout=0)"
    else:
        str_params = "(" + params + ",nargout=0)"

    # add file path to matlab
    engine.addpath(os.path.dirname(func))
    print("running matlab function: " + func, file=logfile)
    eval("engine." + os.path.basename(os.path.splitext(func)[0]) + str_params)

    if endengine is True:
        engine.quit()
        print("quitting matlab session")

    return engine


# subcase of call_matlab_function_noret: call a SPM batch file that does not return anything
def call_matlab_spmbatch(func, standard_paths, logfile=None, endengine=True):

    engine = start_matlab(standard_paths)
    if engine is None:
        return

    # add file path to matlab
    engine.addpath(os.path.dirname(func))
    print("running SPM batch template: " + func, file=logfile)
    eval("engine." + os.path.basename(os.path.splitext(func)[0]) + "(nargout=0)")

    if endengine is True:
        engine.quit()
        print("quitting matlab session")

    return engine














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
