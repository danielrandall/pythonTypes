import os
import ast

import src.stcglobals as stcglobals
from src.pyfile import PyFile

def get_pys(top_level):
    ''' Returns a dict which has a directories as keys and maps to a list of
        dicts with file names as keys and maps to the corresponding PyFiles. '''
    py_files = {}
    os.chdir(top_level)
    for root, dirs, files in os.walk(top_level):
        # Remove those beginning with an underscore
        files_no_underscore = [x for x in files if x[0] != "_"]
        # Separate name and extension
        files_extensions = [os.path.splitext(x) for x in files_no_underscore]
        py_names = [x[0] for x in files_extensions if x[1] == ".py"]
        relative_root = os.path.relpath(root, top_level)
        py_files[relative_root] = {}
        for py_name in py_names:
            py_file = PyFile(py_name, relative_root, root + "/" + py_name + ".py")
            py_files[relative_root][py_name] = py_file
    return py_files