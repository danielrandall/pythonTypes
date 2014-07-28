# -*- coding: utf-8 -*-
#@+leo-ver=5-thin
#@+node:ekr.20120626085227.11392: * @file statictypechecking.py
#@@first

'''
A static type checker for Python. See:
https://groups.google.com/forum/?fromgroups#!forum/python-static-type-checking
'''
#@+<< copyright notices >>
#@+node:ekr.20121230060528.5221: ** .<< copyright notices >>
#@@nocolor-node
#@+at
# The MIT License:
# 
# Copyright (c) 2012-2013 by Edward K. Ream
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 
# The License for the HTMLReportTraverser:
#     
# Copyright (C) 2005-2012 Paul Boddie <paul@boddie.org.uk>
# 
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
# 
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
# 
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.
#@-<< copyright notices >>
use_leo_globals = True # Better for debugging.
#@+<< imports >>
#@+node:ekr.20120626085227.11393: ** .<< imports >>
import sys
isPython3 = sys.version_info >= (3,0,0)
import imp
from pprint import pprint
import queue
# Used for constraint solving

from src.constraintgenerator import ConstraintGenerator
import src.binopconstraints as binopcons
from src.utils import Utils
from src.traversers.astfulltraverser import AstFullTraverser
from src.traversers.astformatter import AstFormatter
from src.typeclasses import *
from src.traversers.ssatraverser import Phi_Node

try:
    if use_leo_globals: # This is better for EKR's debugging.
        import leo.core.leoGlobals as g
        # print('*** using leo.core.leoGlobals')
    else:
        raise ImportError
except ImportError:
    try:
        import stcglobals as g
        imp.reload(g)
        print('*** using stcglobals')
    except ImportError:
        g = None # Will fail later.

# Used by ast-oriented code.
# if not isPython3:
    # import __builtin__
    
import ast
import gc
import glob

import os

import time

if isPython3:
    import io
    StringIO = io.StringIO
else:
    import cStringIO
    StringIO = cStringIO.StringIO

class BaseStats: 
    '''The base class for all statistics classes.'''

    def __init__ (self):
        # May be overriden in subclases.
        self.always_report = []
        self.distribution_table = []
        self.table = []
        self.init_ivars()
        self.init_tables()

    def print_distribution(self,d,name):
        print('Distribution for %s...' % name)
        
        for n in sorted(d.keys()):
            print('%2s %s' % (n,d.get(n)))
        print('')

    def print_stats (self):
        max_n = 5
        for s in self.table:
            max_n = max(max_n,len(s))
            
        print('\nStatistics...\n')
        for s in self.table:
            var = 'n_%s' % s
            pad = ' ' * (max_n - len(s))
            if s.startswith('*'):
                if s[1:].strip():
                    print('\n%s:\n' % s[1:])
            else:
                pad = ' ' * (max_n-len(s))
                val = getattr(self,var)
                if val or var in self.always_report:
                    print('%s%s: %s' % (pad,s,val))
        print('')
        for d,name in self.distribution_table:
            self.print_distribution(d,name)
        print('')


class PatternFormatter (AstFormatter):
    # def __init__ (self):
        # AstFormatter.__init__ (self)

    def do_BoolOp(self,node): # Python 2.x only.
        return 'Bool' 

    def do_Bytes(self,node): # Python 3.x only.
        return 'Bytes' # return str(node.s)

    def do_Name(self,node):
        return 'Bool' if node.id in ('True','False') else node.id

    def do_Num(self,node):
        return 'Num' # return repr(node.n)

    def do_Str (self,node):
        '''This represents a string constant.'''
        return 'Str' # return repr(node.s)


class Stats(BaseStats):
    # def __init__(self):
        # BaseStats.__init__(self):
            
    def init_ivars (self,n_files=0):
        
        self.n_files = n_files
        
        # Dictionaries for computing distributions.
        # Keys are lengths (ints); values are counts for each lenght (ints).
        self.actual_args_dict = {}
        self.formal_args_dict = {}
        
        # Errors & warnings.
        self.n_errors = 0
        self.n_warnings = 0

        # Pre-passes...
        self.n_chains = 0
        self.n_contexts = 0
        self.n_files = 0 # set only in print_stats.
        self.n_library_modules = 0
        self.n_modules = 0
        self.n_relinked_pointers = 0
        # self.n_resolvable_names = 0
        self.n_resolved_contexts = 0
        self.n_relinked_names = 0
        
        # Cache & circular inferences
        self.n_assign_hits = 0
        self.n_assign_fails = 0
        self.n_assign_misses = 0
        self.n_call_hits = 0
        self.n_call_misses = 0
        self.n_circular_assignments = 0
        self.n_outer_expr_hits = 0
        self.n_outer_expr_misses = 0
        self.n_recursive_calls = 0
        
        # Inference...
        self.n_attr_fail = 0
        self.n_attr_success = 0
        self.n_binop_fail = 0
        self.n_caches = 0
        self.n_clean_fail = 0
        self.n_clean_success = 0
        self.n_find_call_e_fail = 0
        self.n_find_call_e_success = 0
        self.n_fuzzy = 0
        self.n_not_fuzzy = 0
        self.n_return_fail = 0
        self.n_return_success = 0
        self.n_ti_calls = 0
        self.n_unop_fail = 0
        
        # Names...
        self.n_attributes = 0
        self.n_ivars = 0
        self.n_names = 0        # Number of symbol table entries.
        self.n_del_names = 0
        self.n_load_names = 0
        self.n_param_names = 0
        self.n_param_refs = 0
        self.n_store_names = 0
        
        # Statements...
        self.n_assignments = 0
        self.n_calls = 0
        self.n_classes = 0
        self.n_defs = 0
        self.n_expressions = 0 # Outer expressions, ast.Expr nodes.
        self.n_fors = 0
        self.n_globals = 0
        self.n_imports = 0
        self.n_lambdas = 0
        self.n_list_comps = 0
        self.n_returns = 0
        self.n_withs = 0
        
        # Times...
        self.parse_time = 0.0
        self.pass1_time = 0.0
        self.pass2_time = 0.0
        self.total_time = 0.0

    def init_tables(self):

        self.table = (
            # '*', 'errors',

            '*Pass1',
            'files','classes','contexts','defs','library_modules','modules',
            
            '*Statements',
            'assignments','calls','expressions','fors','globals','imports',
            'lambdas','list_comps','returns','withs',
            
            '*Names',
            'attributes','del_names','load_names','names',
            'param_names','param_refs','store_names',
            # 'resolvable_names',
            'relinked_names','relinked_pointers',
            
            '*Inference',
            'assign_hits','assign_fails','assign_misses',
            'attr_fail','attr_success',
            'call_hits','call_misses','recursive_calls',
            'circular_assignments',
            'clean_fail','clean_success',
            'find_call_e_fail','find_call_e_success',
            'fuzzy','not_fuzzy',
            'outer_expr_hits','outer_expr_misses',
            'return_fail','return_success',
            'ti_calls',
            'unop_fail',

            '*Errors & Warnings',
            'errors',
            'warnings',
        )
        
        self.always_report = (
            'n_assign_hits',
            'n_call_hits',
            'n_outer_expr_hits',
            'n_recursive_calls',
            'n_fuzzy',
        )
        
        self.distribution_table = (
            (self.actual_args_dict,'actual args'),
            (self.formal_args_dict,'formal args'),
        )
        
class SymbolTable:
    
    def __init__ (self,cx):
        self.cx = cx
        self.attrs_d = {}
            # Keys are attribute names.
            # Values are sets of contexts having that name.
        self.d = {} # Keys are names, values are type lists.
        self.defined = set() # Set of defined names.
        self.defined_attrs = set() # Set of defined attributes.
        self.ssa_d = {} # Keys are names, values are reaching lists.
    
    def __repr__ (self):
        return 'Symbol Table for %s\n' % self.cx
    
    __str__ = __repr__
    

class TypeInferrer(AstFullTraverser):
    '''A class to infer the types of objects. 
    
       TODO: Analyse classes first. '''
    
    def clean (self,aList):    
        '''Return sorted(aList) with all duplicates removed.'''
        return aList or []
        
        ti = self
        if 1:
            # Good for debugging and traces.
            result = []
            for z in aList:
                if z not in result:
                    result.append(z)
            
            # An excellent check.
            assert len(result) == len(list(set(aList))),aList
        else:
            result = list(set(aList))
       
        # Strip out inference errors if there are real results.
        result2 = ti.ignore_failures(result)
        if result2:
            ti.stats.n_clean_success += 1
            return sorted(result2)
        else:
            ti.stats.n_clean_fail += 1
            return sorted(result)
    
    def format(self,node):
        u = self.u
        return '%s%s' % (
            ' '*u.compute_node_level(node),
            u.first_line(u.format(node)))
    
    def init(self):   
        self.variableTypes = {} # Used as string:name -> set():types
        self.currently_assigning = False
        self.awaiting_Typing = []  # Elements : (node, name)
        self.fun_params = []
        # The class definition we are currently under
        self.current_class = None

        self.stats = Stats()
        self.u = Utils()
        
        # Local stats
        self.n_nodes = 0
        
        # Detecting circular inferences
        self.call_stack = [] # Detects recursive calls
        self.assign_stack = [] # Detects circular assignments.

        # Create the builtin type dict.
        ''' TODO: Differing number of parameters. '''
        builtin_type_dict = {
            'eval': set([Def_Type([set([string_type])],
                                  set([any_type]),
                                  0)]),
            'id':   set([Def_Type([set([any_type])],
                                  set([int_type]),
                                  0)]),
            'str':  set([Def_Type([set([any_type])],
                                  set([string_type]),
                                  0)]),
            'len':  set([Def_Type([set([any_type])],
                                  set([int_type]),
                                  0)]),
            'range':  set([Def_Type([set([int_type]), set([int_type]), set([int_type])],
                                    set([ List_Type(None, [], set([int_type]) ) ]),
                                    2)]),
            'ord':  set([Def_Type([set([string_type])],
                                  set([int_type]),
                                  0)]),
            'chr':  set([Def_Type([set([int_type])],
                                  set([string_type]),
                                  0)]),
            'print': set([Def_Type([set([any_type])],
                                  set([none_type]),
                                  0)]),
            'sorted': set([Def_Type([set([List_Type(None, [], set())])],
                                  set([List_Type(None, [], set())]),
                                  0)]),
            # min and max work on any iterable and have varargs
            'min' : set([Def_Type([set([any_type]), set([any_type])],
                                  set([any_type]),
                                  0)]),
            'max' : set([Def_Type([set([any_type]), set([any_type])],
                                  set([any_type]),
                                  0)]),
            'getattr' : set([Def_Type([set([any_type]), set([string_type]), set([any_type])],
                                  set([any_type]),
                                  1)])
            # list,tuple...
            # close,open,sort,sorted,super...
        }
        # Add the builtin_types to the variable dict
        self.variableTypes.update(builtin_type_dict)
        
       
    def run(self, file_tree):
        ''' file_tree is a list of pyfiles.
            TODO: Do this file find outside of this module... '''
        # Keys are module name, values their typed dicts
        self.checked_list = {}
        file_list = self.file_tree_to_list(file_tree)
        for file in file_list:
            if file.has_been_typed():
                continue
            dependents = self.check_dependents(file, file_tree)
            self.type_file(file, dependents) 
            
    def check_dependents(self, file, file_tree):
        dependent_vars = {}
        if file.has_been_typed():
            dependent_vars[file.get_name()] = Module_Type(file.get_name(), file.get_global_vars())
            return dependent_vars
        root = file.get_source()
        for dependent in root.import_dependents:
                if dependent not in self.checked_list:
                    split_string = dependent.split('/')
                    name = split_string.pop()
                    # We want to remove the last '/' as well
                    directory = dependent[:dependent.rfind(name) - 1]
                    assert(directory in file_tree), "File not found"   
                    dependent_file = file_tree[directory][name]
                    dependent_dependents = self.check_dependents(dependent_file, file_tree)
                    self.type_file(dependent_file, dependent_dependents)
                    dependent_vars[name] = Module_Type(name, dependent_file.get_global_vars())
        return dependent_vars 
            
    def file_tree_to_list(self, file_tree):
        file_lists = []
        name_dicts = file_tree.values()
        for n_dict in name_dicts:
            file_lists.extend(n_dict.values())
        return file_lists
            
    def type_file(self, file, dependents):   
        ''' Runs the type_checking on an individual file. '''
        root = file.get_source()           
        self.init()
        self.variableTypes.update(dependents)
        self.visit(root)
        file.set_global_vars(self.variableTypes)
        file.typed = True

    def has_failed(self,t1,t2=[],t3=[]):
        return any([isinstance(z,Inference_Failure) for z in t1+t2+t3])
        
    def is_circular(self,t1,t2=[],t3=[]):
        return any([isinstance(z,Circular_Assignment) for z in t1+t2+t3])
        
    def is_recursive(self,t1,t2=[],t3=[]):
        return any([isinstance(z,Recursive_Inference) for z in t1+t2+t3])
        
    def ignore_failures(self,t1,t2=[],t3=[]):
        return [z for z in t1+t2+t3 if not isinstance(z,Inference_Failure)]
        
    def ignore_unknowns(self,t1,t2=[],t3=[]):
        return [z for z in t1+t2+t3 if not isinstance(z,(Unknown_Type,Unknown_Arg_Type))]
        
    def merge_failures(self,t1,t2=[],t3=[]):
        aList = [z for z in t1+t2+t3 if isinstance(z,Inference_Failure)]
        if len(aList) > 1:
            # Prefer the most specific reason for failure.
            aList = [z for z in aList if not isinstance(z,Unknown_Type)]
        return aList
    
    def visit(self,node):
        '''Visit a single node.  Callers are responsible for visiting children.'''
        method = getattr(self,'do_' + node.__class__.__name__)
        self.n_nodes += 1
        return method(node)

    def do_Attribute (self, node):
        ''' Always a variable of the form x.y .
            TODO: For assignments x.y = ? and x can be a number of different classes - do something clever. '''
        if node.variable:
            name = self.do_Name(node.value)[0]
            if self.currently_assigning:
                # Special case self
                if name == "self":
                    class_to_assign = self.current_class
                else:
                    n_type = self.variableTypes[name]
                    class_to_assign = None
                    for n in n_type:
                        if isinstance(n, Class_Base):
                            class_to_assign = n
                            break                 
                assert class_to_assign, "Error: Cannot assign to builtin class" + str(n_type)
                return [Attribute_Type(class_to_assign, node.attr)]
            else:
                # Generate a constraint if the value is a function parameter
                if name in self.fun_params:
                    name = self.constraint_gen.do_Attribute(name, node.attr, node.lineno)[0]
                result_types = set()
                for n in name:
                    if isinstance(n, Module_Type):
                        ''' TODO: Deal with modules. '''
                        return [set([any_type])]
                    if node.attr in n.global_vars:
                        result_types |= n.global_vars[node.attr]
                    else:
                        result_types.add(any_type)
                return [result_types]
        else:
            # Class here. Like {}.__class__
            ''' TODO: Find the types '''
            return [set([any_type])]

    def do_Name(self, node):
        # Check whether the name is a function argument
        if node.id in self.fun_params:
            return [node.id]
        if self.currently_assigning:
            return [node.id]
        # Stupidly True and False are Names. Return bool type
        if (node.id == "True" or node.id == "False"):
            return [set([bool_type])]
        if node.id == "self":
            assert self.current_class, "self used outside of class definition. "
            return [set([self.current_class])]
        if node.id in self.variableTypes:
            return [self.variableTypes[node.id]]
        # Check if name has already been analysed (i.e. has an SSA)
        pass
        # Check if name is defined somewhere in the future
        print(node.id)
        found = self.find_in_parent_contexts(node.id, node.stc_context)
        if found:
            found_node, found_context = found
            self.visit(found_node)
            self.give_ssa_reference(node)
            pprint(self.variableTypes)
            assert node.id in self.variableTypes, "node.id should really be in there now!"
            return [self.variableTypes[node.id]]
        return [set([none_type])]
    
    def find_in_parent_contexts(self, name_to_find, context):
        ''' Returns a tuple containing the found node and it's context. '''
        if name_to_find in context.contents_dict:
            return (context.contents_dict[name_to_find], context)
        # Keep going up the module hierarchy until a dead end is reached
        if context.stc_context:
            return self.find_in_parent_contexts(name_to_find, context.stc_context)
        return None
    
    def find_biggest_ssa_reference(self, id):
        ''' Finds the highest ssa reference, if one exists.
        
            This is useful when the SSA cannot not detect the reference as it is yet
            to be seen but it has been referenced more than once. We do not want to
            analyse it twice!
            TODO: Make this work. Doesn't work now as two different variables x and x1 will clash. '''
        current_check = 1
        if id + str(current_check) not in self.variableTypes:
            return False
        while True:
            if id + str(current_check + 1) in self.variableTypes:
                current_check += 1
            else:
                break
        return id + str(current_check)
    
    def give_ssa_reference(self, node):
        ''' Gives an un-SSA'd node an SSA'd id.
            Used if the id has not yet been accessed so the
            find_in_parents_contexts function has been used.
            This should just require adding 1. '''
        node.id += str(1)
    
    def do_Assign(self, node):
        ''' Set all target variables to have the type of the value of the
            assignment. '''
        value_types = self.visit(node.value)
        
        self.currently_assigning = True
        targets = []
        for z in node.targets:
            targets.extend(self.visit(z))
        self.currently_assigning = False
        
        self.conduct_assignment(targets, value_types, node)
        pprint(self.variableTypes)
        
    def conduct_assignment(self, targets, value_types, node):
        ''' TODO: Stop comparisons with instantiation of Container_Type. '''
        assert(len(value_types) == len(targets)) 
        for i in range(len(targets)):
            for e in value_types[i]:
                result = e.contains_waiting_type()
                if result:
                    if result.waiting_for == targets[i]:
                        # We have a circular assignment, ladies and gentlemen.
                        # Just give up and assign both Any.
                        # TODO: Improve this
                        self.variableTypes[targets[i]] = set([any_type])
                        self.variableTypes[result.waitee] = set([any_type])
                        del value_types[i]
                        del targets[i]
                        break
                    self.variableTypes[targets[i]] = [set([Awaiting_Type(targets[i], result.waitee)])]
                    self.awaiting_Typing.append((node, result.waitee))
                    # Remove the culprits from the list so we can continue processing
                    del value_types[i]
                    del targets[i]
                    break
        # Must start a new loop as we delete elements in the previous loop
        for i in range(len(targets)):
            if isinstance(targets[i], Container_Type):
                assert len(value_types[i]) == 1
                (value,) = value_types[i]
                assert value <= Container_Type(None, None, None, None), "Line " + str(node.lineno) + ": Assigning non container type to a container"
                # Unpack the lists
                self.container_assignment(targets[i], value, node)
                continue
            
            if isinstance(value_types[i], Container_Type):
                value_types[i].infer_types()
                value_types[i] = set([value_types[i]])

            if isinstance(targets[i], Attribute_Type):
                class_instance = targets[i].class_type
                attr = targets[i].variable_type
                class_instance.add_to_vars(attr, value_types[i])
            else:
                self.variableTypes[targets[i]] = value_types[i]
            # For each new assign, check whether any are waiting on it.
            self.check_waiting(targets[i])
        
    def container_assignment(self, target_container, value_container, node):
        ''' Check both are containers. But if the value is any_type construct
            an equivalently sized list with all any_types. '''
        assert target_container <= Container_Type(None, None, None, None)
        assert value_container <= Container_Type(None, None, None, None)
        targets = target_container.contents
        if value_container == any_type:
            values = [set([any_type])] * len(targets)
        else:
            values = value_container.contents
        self.conduct_assignment(targets, values, node)
        
    def do_AugAssign(self,node):
        ''' This covers things like x += ... x -=...
            This is pretty much just a BinOp so modify the node so node.value is a binop
            work out the type and then assign the result. '''
        binOp_node = ast.BinOp()
        binOp_node.left = node.prev_name
        binOp_node.right = node.value
        binOp_node.op = node.op
        # Assign expects targets
        node.targets = [node.target]
        
        node.value = binOp_node
        self.do_Assign(node)
        if "g1" in self.variableTypes:
            pprint(list(self.variableTypes["g1"])[0].get_vars()) 
        
    def check_waiting(self, new_var):
        waiting = [x[0] for x in self.awaiting_Typing if x[1] == new_var]
        for z in waiting:
            self.visit(z)
            
    def do_List(self,node):
        names = []
        for z in node.elts:
            names.extend(self.visit(z))
        new_list = List_Type(node, names, set())
        if self.currently_assigning:
            return [new_list]
        else:
            return [set([new_list])]
        
    def do_Tuple(self,node):
        ''' No need to worry about currently_assigning.
            Can return types or names. '''
        names = []
        for z in node.elts:
            names.extend(self.visit(z))
        new_tuple = Tuple_Type(node, names, set())
        if self.currently_assigning:
            return [new_tuple]
        else:
            return [set([new_tuple])]

    def do_BinOp (self,node):
        ''' Try all combinations of types
            TODO: Correct this to cover all possibilities.
            TODO: Classes/functions... etc
            TODO: Allow for Any_Type'''
        left_types = self.visit(node.left)[0] # Will return a list of 1 element
        right_types = self.visit(node.right)[0] # ''
        
        op_kind = self.kind(node.op)
        
        if left_types in self.fun_params or right_types in self.fun_params:
            result_types = self.constraint_gen.do_BinOp(left_types, right_types, op_kind, node.lineno)
            if left_types in self.fun_params:
                left_types = result_types[0] # Will return a list of 1 element
            if right_types in self.fun_params:
                right_types = result_types[0] # ''
        
        # Check if this operation depends on variable awaiting the type of
        # another
        for a_type in left_types:
            if (isinstance(a_type, Awaiting_Type)):
                return [set([a_type])]
        for a_type in right_types:
            if (isinstance(a_type, Awaiting_Type)):
                return [set([a_type])]
        
        result_types = set()
        
        for left in left_types:
            for right in right_types:
                # Any_Type checks
                ''' TODO: do this better | check the type is acceptable'''
                if isinstance(left, Any_Type) and isinstance(right, Any_Type):
                    return [set([any_type])]
                if isinstance(left, Any_Type):
                    pprint(right)
                    result_types |= set(binopcons.BIN_OP_CONSTRAINTS[op_kind][right])
                    continue
                if isinstance(right, Any_Type):
                    result_types |= set(binopcons.BIN_OP_CONSTRAINTS[op_kind][left])
                    continue

                if isinstance(left, Num_Type) and isinstance(right, Num_Type):
                    # Doesn't matter what the op is
                    if right <= float_type or left <= float_type:
                        result_types.add(float_type)
                        continue
                    else:
                        result_types.add(int_type)
                        continue
                    
                if isinstance(left, List_Type) and isinstance(right, List_Type) and op_kind == 'Add':
                    left.infer_types()
                    right.infer_types()
                    new_list = List_Type(node, [], left.content_types | right.content_types)
                    result_types.add(new_list)
                    continue
                
                if left <= string_type and right <= string_type and op_kind == 'Add':
                    result_types.add(string_type)
                    continue
                
                if left <= string_type and op_kind == 'Mod':
                    # String mod anything is a string, so long as there's stuff to format
                    result_types.add(string_type)
                    continue
                
                if op_kind == 'Mult' and (
                        (left <= string_type and right <= int_type) or
                        (left <= int_type and right <= string_type)):
                    result_types.add(string_type)
                    continue
            self.stats.n_binop_fail += 1
        assert result_types, "Line " + str(node.lineno) + ": " + "No acceptable BinOp operation. "
        return [result_types]
    
    def do_UnaryOp(self,node):
        ''' TODO: Check this. Should be able to return more than one type. '''
        op_types = self.visit(node.operand)[0] # Will only have 1 element
        op_kind = self.kind(node.op)
        if op_kind == 'Not':    # All types are valid
            return [set([bool_type])]
        for a_type in op_types:
            if a_type == int_type or a_type == float_type:
                return [set([a_type])]
            else:    # No other possibilities exist.
                self.stats.n_unop_fail += 1
                assert(False)
        a_type = [set([Unknown_Type(node)])]
        return a_type
    
    def do_BoolOp(self,node):
        ''' For and/or
            Never fails.
            Boolean operators can return any types used in its values.
            ie. len(x) or [] can return Int or List. '''
        all_types = set()
        for z in node.values:
            all_types |= self.visit(z)[0]
        return [all_types]

    def do_Num(self,node):
        ''' Returns int or float. '''
        t_num = Num_Type(node.n.__class__)
        return [set([t_num])]
    
    def do_Bytes(self,node):
        return [set([self.bytes_type])]

    def do_Str(self,node):
        '''This represents a string constant.'''
        return [set([string_type])]

    def do_Dict(self,node):   
        for z in node.keys:
            self.visit(z)
        for z in node.values:
            self.visit(z)
        return [set([Dict_Type(node)])]
    
    def do_If(self,node):
        self.visit(node.test)
        for z in node.body:
            self.visit(z)
        for z in node.orelse:
            self.visit(z)
        phis = node.afterPhis
        for phi in phis:
            self.visit(phi)
        
    def do_Phi_Node(self, node):
        self.variableTypes[node.var] = set()
        for target in node.targets:
            if (target == Phi_Node.TARGET_NOT_DECLARED):
                possibleTypes = set([none_type])
            elif target in self.variableTypes:
                possibleTypes = self.variableTypes[target]
            else:
                # Variable is used in the future
                self.awaiting_Typing.append((node, target))
                self.variableTypes[node.var] = set([Awaiting_Type(node.var, target)])
                return
            self.variableTypes[node.var] = (
                                 self.variableTypes[node.var] | possibleTypes)
            self.check_waiting(node.var)
        
    def do_While (self, node):
        self.visit(node.test) 
        self.loop_helper(node)
    
    def loop_helper(self, node):
        # Type the phis before the loop
        phis = node.beforePhis
        for phi in phis:
            self.visit(phi)
                
        for z in node.body:
            self.visit(z)
        for z in node.orelse:
            self.visit(z)
        # Type the phis after the loop
        phis = node.afterPhis
        for phi in phis:
            self.visit(phi)
                
    def do_For(self, node):
        ''' TODO: Allow for any Iterable object in node.iter instead of just List_Type. '''
        # This is a glorified assignment so set to true
        self.currently_assigning = True
        targets = self.visit(node.target)
        self.currently_assigning = False
        value_types = self.visit(node.iter)
        # value_types should be a list.
      #  assert isinstance(value_types, List_Type)
        self.conduct_assignment(targets, self.extract_list_types(value_types), node)
        self.loop_helper(node)
        
    def extract_list_types(self, list_of_lists):
        ''' Should be given a list of sets which contains only List_Type.
            This function returns a list containing a single set which contains
            all types find in each list. '''
        extracted_types = set()
        assert isinstance(list_of_lists, list)
        for possible_types in list_of_lists:
            for list_type in possible_types:
                assert isinstance(list_type, List_Type), "Should be a list but found a " + str(list_type)
                list_type.infer_types()     # Just to make sure
                extracted_types |= list_type.content_types
        # If nothing is found then return any_type
        if extracted_types:
            return [extracted_types]
        else:
            return [set([any_type])]
        
    def do_Import(self, node):
        for z in node.names:
            self.visit(z)
            
    def do_ImportFrom(self, node):
        ''' TODO: Give the names the type module. '''
        for z in node.names:
            self.visit(z)
            
    def do_alias (self, node):
        ''' Add the name as a Module type.
            TODO: Link the module to the name.
            TODO: Sort out cx '''
        self.variableTypes[node.id] = set({Module_Type(node.module_name, node)})        

    def do_Call (self, node):
        ''' Infer the value of a function called with a particular set of 
            arguments. '''
        given_arg_types = []
        result_types = set()
        for z in node.args:
            given_arg_types.extend(self.visit(z))
        possible_funcs = self.visit(node.func)[0]
        print("Function possible types")
        pprint(possible_funcs)
        # If the function could not be found then just return any_type
        if any_type in possible_funcs:
            return [set([any_type])]
        callable_funcs = [x for x in possible_funcs if x.is_callable()]
        # At least one possible type needs to be callable
        assert callable_funcs, "Line " + str(node.lineno) + ": not callable."
        for func in callable_funcs:
            func_return_types = func.get_return_types()
            accepted_types = func.get_parameter_types()

            # Check that the correct number of types has been given.
            # If the number is less than the maximum then ensure it falls
            # within the default range and adjust accordingly
            assert len(given_arg_types) <= len(accepted_types), "Line " + str(node.lineno)
            if len(given_arg_types) < len(accepted_types):
                missing_num = len(accepted_types) - len(given_arg_types)
                assert missing_num <= func.get_arg_default_length(), "Line " + str(node.lineno) + ": Too few args given"
                accepted_types = [accepted_types[x] for x in range(len(accepted_types) - missing_num)]
                
            for i in range(len(given_arg_types)):
                # If the arg is a function parameter then we can not type check
                # generate a constraint and then move on.
                if given_arg_types[i] in self.fun_params:
                    self.constraint_gen.do_Call(accepted_types[i], given_arg_types[i])
                    continue
                # ... otherwise type check. At least one type must match up.
                for t1 in given_arg_types[i]:
                    type_allowed = False
                    for t2 in accepted_types[i]:
                        if (t1 <= t2):
                            type_allowed = True
                    assert type_allowed, "Incorrect type given to function"
            result_types |= func_return_types
        pprint(result_types)
        return [result_types]
            
    def do_ListComp(self, node):
        ''' A list comp can edit values inside of comp. Therefore must reset the
            variable types.
            TODO: Tuple in node.elt should result in List(Tuple(type)). '''
        old_type_list = self.variableTypes.copy()
        
        for node2 in node.generators:
            self.visit(node2)
        t = self.visit(node.elt)
        # Reset types
        self.variableTypes = old_type_list
        return [set([List_Type(node, list(t), set())])]

    def do_comprehension(self, node):
        ''' Assign types in the list to the variable name. '''
        self.currently_assigning = True
        targets = self.visit(node.target) # A name.
        self.currently_assigning = False
        value_types = self.visit(node.iter) # An attribute.
        value_types = self.extract_list_types(value_types)
        self.conduct_assignment(targets, value_types, node)
        #return [List_Type(node)]
        
    def do_FunctionDef(self, node):
        ''' Find all args and return values.
        
            TODO: Find out possible types in *karg dict. '''
        old_types = self.variableTypes.copy()

        # Create a constraint satisfaction problem for the arguments
        self.fun_params = self.visit(node.args)
        self.constraint_gen = ConstraintGenerator()
        self.constraint_gen(node, self.variableTypes, self.fun_params)
        self.fun_return_types = set() 
        
      #  if node.kwarg:
      #      self.variableTypes[kwarg] = set(Dict_Type)
      #  vararg='vargs'
      #  kwonlyargs=[arg(arg='x')]
      #  kwarg='kargs'
      #  defaults=[Num(n=5)]
      #  kw_defaults=[Num(n=3)])
        
        for z in node.body:
            self.visit(z)
        for z in node.decorator_list:
            self.visit(z)
            
        # If nothing was added then this function does not return anything
        if self.fun_return_types == set():
            self.fun_return_types = set([none_type])
        
        self.constraint_gen.extract_results()
        self.constraint_gen.clear_list()
        
        parameter_types = []
        for arg in self.fun_params:
            parameter_types.append(self.variableTypes[arg])
            
        self.fun_params = []
        # Restore variables
        self.variableTypes = old_types
        
        fun_type = Def_Type(parameter_types, self.fun_return_types, node.args.default_length)
        self.variableTypes[node.id] = set([fun_type])
        #Add to the currently class vars if there is one
        if self.current_class:
            self.current_class.add_to_vars(node.id, self.variableTypes[node.id])
        pprint(parameter_types)
            
    def do_arguments(self, node):
        ''' We need to begin checking what types the args can take. Defaults
            already give us a nice possible value.
            The defaults list contains the value for the last len(defaults)
            arguments.
            TODO: Deal with list length when self is removed. '''
        args = []
        for z in node.args:
            args.extend(self.visit(z))
        # If this a function in a class then self should be the first arg
        if self.current_class:
            pprint(args[0])
            assert(args[0] == "self"), "First argument of function " + node.stc_parent.name + " should be self."
            del args[0]
        defaults = []
        for z in node.defaults:
            defaults.extend(self.visit(z))
        node.default_length = len(defaults)
        # Assign defaults in reverse order until there are none left then
        # assign Any_Type
        for i in range(len(args) - 1, -1, -1):
            if defaults:
     #           self.variableTypes[args[i]] = defaults.pop()
                self.variableTypes[args[i]] = set([any_type])
            else:
                self.variableTypes[args[i]] = set([any_type])
        pprint(self.variableTypes)
        return args
            
    def do_arg(self, node):
        return [node.id]
    
    def do_ClassDef(self, node):
        ''' The __init__ will provide us with the majority of the self. vars
            so we want to analyse that first.
            TODO: Reverse base class list and update that way to avoid list comp. '''
        old_types = self.variableTypes.copy()
        # Deal with inheritence.
        inherited_vars = {}
        for base in node.bases:
            base_class = self.visit(base)[0]
            acceptable_type = False
            pprint(base_class)
            for possible_type in base_class:
                if isinstance(possible_type, Class_Type):
                    # If there is a clash, the first instance will be used
                    inherited_vars.update({k:v for k,v in possible_type.get_vars().items() if k not in inherited_vars})
                    acceptable_type = True
            assert acceptable_type, "Line " + str(node.lineno) + ": " + base.id + " is not a class. "
        self.current_class = Class_Type(node.id, inherited_vars, node.callable)
        self.move_init_to_top(node.body)
        for z in node.body:
            self.visit(z)
        # We need to set the parameters for init
        pprint(self.variableTypes)
        init_ssa_reference = self.find_biggest_ssa_reference("__init__")
        init_def = list(self.variableTypes[init_ssa_reference])[0]
        self.current_class.set_init_params(init_def.parameter_types)
        pprint(self.variableTypes)
        # Set the call if possible
        is_callable, call_node = node.callable
        if is_callable:
            fun = list(self.variableTypes[call_node.id])
            # Should be a list of size 1
            assert len(fun) == 1, "__call__ multiply defined. "
            self.current_class.set_callable_params(fun[0].get_parameter_types(), fun[0].get_return_types())
        self.variableTypes = old_types
        self.variableTypes[node.id] = set([self.current_class])
        
    def move_init_to_top(self, body):
        assert isinstance(body, list), "Body needs to be a list."
        for i in range(len(body)):
            elem = body[i]
            if isinstance(elem, ast.FunctionDef):
                if elem.name == "__init__":
                    body.insert(0, body.pop(i))
                    return
        else:
            # Insert a blank one if none found
            init_def = ast.FunctionDef()
            init_def.body = [ast.Pass()]
            init_def.args = ast.arguments()
            arg = ast.arg()
            arg.id = "self"
            init_def.args.args = [arg]
            init_def.args.defaults = []
            init_def.name = "__init__"
            init_def.id = "__init__1"
            init_def.name = init_def.id
            init_def.decorator_list = []
            body.insert(0, init_def)

    def do_Compare(self, node):
        ''' A comparison will always return a boolean type.
            TODO: Check if errors can occur as a result of a comparison. '''
        self.visit(node.left)
        for z in node.comparators:
            self.visit(z)
        return [set([bool_type])]
    
    def do_Assert(self, node):
        ''' No real checking to here. Any expression can be compared with a
            boolean in Python. '''
        pass
    
    def do_Return(self, node):
        if not node.value:
            self.fun_return_types |= set([none_type])
            return            
        possible_return_type = self.visit(node.value)[0] # Can only be len 1
        # If the a parameter is being returned then use the default value set
        # Its probably any_type.
        if possible_return_type in self.fun_params:
            possible_return_type = self.variableTypes[possible_return_type]
        assert isinstance(possible_return_type, set), "Can be a set of types!"
        self.fun_return_types |= possible_return_type

    def do_Expr(self, node):
        ti = self
        t = ti.visit(node.value)
        return t

    def do_GeneratorExp (self, node):
        ti = self
        trace = False and not g.app.runningAllUnitTests
        junk = ti.visit(node.elt)
        t = []
        for node2 in node.generators:
            t2 = ti.visit(node2)
            t.extend(t2)
        if ti.has_failed(t):
            t = ti.merge_failures(t)
            if trace: g.trace('failed inference',ti.format(node),t)
        else:
            t = ti.clean(t)
        return t

    def do_Index(self, node):    
        value_types = self.visit(node.value)[0]
        int_like_types = [x for x in value_types if x <= int_type]
        assert int_like_types, "index value must be an integer"
        return

    def do_Lambda (self, node):
        return self.visit(node.body)

    def do_Slice(self, node):
        ''' No need to return anything here. '''
        if node.upper:
            upper_types = self.visit(node.upper)[0]
            int_like_types = [x for x in upper_types if x <= int_type]
            assert int_like_types, "upper in slice must be an integer"
        if node.lower:
            lower_types = self.visit(node.lower)[0]
            int_like_types = [x for x in lower_types if x <= int_type]
            assert int_like_types, "lower in slice must be an integer"
        if node.step:
            step_types = self.visit(node.step)[0]
            int_like_types = [x for x in step_types if x <= int_type]
            assert int_like_types, "step in slice must be an integer"
        return

    def do_Subscript(self, node):
        ''' TODO: Allow user-defined types to index/slice.
            TODO: Stop comparing with an instantiation of Container_Type - will probably be solved with the above'''
        value_types = self.visit(node.value)[0]
        container_like_types = [x for x in value_types if x <= Container_Type(None, None, None, None)]
        assert container_like_types, "Line " + str(node.lineno) + ": cannot index/slice in non-container types. "
        self.visit(node.slice)
        if isinstance(node.slice, ast.Slice):
            # Should return list
            return [value_types]
        if isinstance(node.slice, ast.Index):
            # Should return something in the list
            return_types = set()
            for possible_container in container_like_types:
                return_types |= possible_container.content_types
            return [return_types]
        assert False, "How did I get here?"

    def do_Builtin(self, node):
        ti = self
        return [ti.builtin_type]
        
    def do_Yield(self,node):
        return self.return_helper(node)

    def do_With (self, node):
        ''' TODO: Add new variable temporarily. '''
        ti = self
        t = []
        for z in node.body:
            t.append(ti.visit(z))
        t = ti.clean(t)
        return t
