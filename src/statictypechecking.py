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
# import string
# import sys
# import textwrap
import time
# import types

if isPython3:
    import io
    StringIO = io.StringIO
else:
    import cStringIO
    StringIO = cStringIO.StringIO

def join_list (aList,indent='',leading='',sep='',trailing=''):
    
    if not aList:
        # g.trace('None: indent:%s' % repr(indent))
        return None
        
    if 1: # These asserts are reasonable.
        assert g.isString(indent),indent
        assert g.isString(leading),leading
        assert g.isString(sep),sep
        assert g.isString(trailing),trailing
    else: # This generality is not likely to be useful.
        if leading and not g.isString(leading):
            leading = list_to_string(leading)
        if sep and not g.isString(sep):
            sep = list_to_string(sep)
        if trailing and not g.isString(trailing):
            trailing = list_to_string(trailing)
        
    if indent or leading or sep or trailing:
        return {
            '_join_list':True, # Indicate that join_list created this dict.
            'aList':aList,
            'indent':indent,'leading':leading,'sep':sep,'trailing':trailing,
        }
    else:
        return aList
#@+node:ekr.20130102151010.5727: *3* stc.flatten_list
def flatten_list (obj):
    
    '''A generator yielding a flattened version of obj.'''

    if isinstance(obj,{}.__class__) and obj.get('_join_list'):
        # join_list created obj, and ensured that all args are strings.
        indent   = obj.get('indent') or ''
        leading  = obj.get('leading') or ''
        sep      = obj.get('sep') or ''
        trailing = obj.get('trailing') or ''
        aList = obj.get('aList')
        for i,item in enumerate(aList):
            if leading: yield leading
            for s in flatten_list(item):
                if indent and s.startswith('\n'):
                    yield '\n'+indent+s[1:]
                else:
                    yield s
            if sep and i < len(aList)-1: yield sep
            if trailing: yield trailing
    elif isinstance(obj,(list,tuple)):
        for obj2 in obj:
            for s in flatten_list(obj2):
                yield s
    elif obj:
        # assert g.isString(obj),obj.__class__.__name__
        if g.isString(obj):
            yield obj
        else:
            yield repr(obj) # Not likely to be useful.
    else:
        pass # Allow None and empty containers.

def list_to_string(obj):
    
    '''Convert obj (a list of lists) to a single string.
    
    This function stresses the gc; it will usually be better to
    work with the much smaller strings generated by flatten_list.

    Use this function only in special circumstances, for example,
    when it is known that the resulting string will be small.
    '''
    return ''.join([z for z in flatten_list(obj)])

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



class P1(AstFullTraverser):
    '''
    Unified pre-pass does two things simultaneously:
    1. Injects ivars into nodes. Only this pass should do this!
       For all nodes::
            node.stc_context = self.context
            node.stc_parent = self.parent
       For all context nodes::
            node.stc_symbol_table = {} # Expensive!
       For all Name nodes.
            node.stc_scope = None.
    2. Calls define_name() for all defined names:
       - class and function names,
       - all names defined in import statements.
       - all paramater names (ctx is 'Param')
       - all assigned-to names (ctx is 'Store'):
       This has the effect of setting::
           node.stc_scope = self.context.
           
    **Important**: Injecting empty lists, dicts or sets causes gc problems.
    This code now injects empty dicts only in context nodes, which does
    not cause significant problems.
    '''
    def __init__(self):
        AstFullTraverser.__init__(self)
        self.in_aug_assign = False
            # A hack: True if visiting the target of an AugAssign node.
        self.u = Utils()
    def __call__(self,fn,node):
        self.run(fn,node)

    class Dummy_Node:
        
        def __init__(self):
            
            # Use stc_ prefix to ensure no conflicts with ast.AST node field names.
            self.stc_parent = None
            self.stc_context = None
            self.stc_child_nodes = [] # Testing only.

    def run (self,fn,root):
        '''Run the prepass: init, then visit the root.'''
        # Init all ivars.
        self.context = None
        self.fn = fn
        self.n_attributes = 0
        self.n_contexts = 0
        self.n_defined = 0
        self.n_nodes = 0
        self.parent = self.Dummy_Node()
        self.visit(root)
        # Undo references to Dummy_Node objects.
        root.stc_parent = None
        root.stc_context = None
        
    def visit(self,node):
        '''Inject node references in all nodes.'''
        assert isinstance(node,ast.AST),node.__class__.__name__
        self.n_nodes += 1
        if 0:
            # Injecting empty lists is expensive!
            #@+<< code that demonstrates the anomaly >>
            #@+node:ekr.20130321223545.9508: *4* << code that demonstrates the anomaly >>
            #@+at
            # Injecting list ivars into nodes is very expensive!
            # But only for a collection of large files...
            # As of rev 403: Leo: 37 files.
            # Python 2, Windows 7, range(200)
            #     p1: 3.38 sec. nodes: 289950 kind: 1
            #     p1: 3.38 sec. nodes: 289950 kind: 2
            #     p1: 0.73 sec. nodes: 289950 kind: 3
            # Python 3, Windows 7, range(200)
            #     p1: 1.83 sec. nodes: 290772 kind: 1
            #     p1: 2.96 sec. nodes: 290772 kind: 2
            #     p1: 0.73 sec. nodes: 290772 kind: 3
            # Python 3, Windows 7, range(100)
            #     p1: 2.14 sec. nodes: 290772 kind: 1
            #     p1: 1.92 sec. nodes: 290772 kind: 2
            #     p1: 0.75 sec. nodes: 290772 kind: 3
            # Mystery solved: kind1 == kind3 if gc is disabled in the unit test.
            #@@c
            kind = 1
            if kind == 1:
                # if 0:
                    # node.stc_test_dict = {}
                # elif 0: # Bad.
                    # if hasattr(self.parent,'stc_child_nodes'):
                        # self.parent.stc_child_nodes.append(node)
                    # else:
                        # self.parent.stc_child_nodes = [node]
                # elif 0: # no problem.
                    # node.stc_child_nodes = None
                    # node.stc_child_statements = None
                # elif 0: # worst.
                    # node.stc_child_nodes = {}
                    # node.stc_child_statements = {} 
                # else: # worst.
                # self.parent.stc_child_nodes.append(node)
                node.stc_child_nodes = [] # 0.58 -> 1.70.
                    # node.stc_child_statements = [] # 1.70 -> 2.81.
                # for z in node._fields: assert not z.startswith('stc_')
            elif kind == 2:
                for i in range(100):
                    x = []
            #@-<< code that demonstrates the anomaly >>
        # Save the previous context & parent & inject references.
        # Injecting these two references is cheap.
        node.stc_context = self.context
        node.stc_parent = self.parent
        # Visit the children with the new parent.
        self.parent = node
        method = getattr(self,'do_' + node.__class__.__name__)
        method(node)
        # Restore the context & parent.
        self.context = node.stc_context
        self.parent = node.stc_parent
        
    def define_name(self,cx,name,defined=True):
        '''
        Fix the scope of the given name to cx.
        Set the bit in stc_defined_table if defined is True.
        '''
        st = cx.stc_symbol_table
        d = st.d
        if name not in d.keys():
            self.n_defined += 1
            d[name] = [] # The type list.
        if defined:
            st.defined.add(name)

    def do_Attribute(self,node):
        
        self.n_attributes += 1
        self.visit(node.value)
        cx = node.stc_context
        st = cx.stc_symbol_table
        d = st.attrs_d
        key = node.attr
        val = node.value
        # The following lines are expensive!
        # For Leo P1: 2.0 sec -> 2.5 sec.
    #    if d.has_key(key):
    #        d.get(key).add(val)
    #    else:
    #        aSet = set()
    #        aSet.add(val)
    #        d[key] = aSet
        # self.visit(node.ctx)
        if isinstance(node.ctx,(ast.Param,ast.Store)):
            st.defined_attrs.add(key)

    def do_AugAssign(self,node):
        # g.trace('FT',self.u.format(node),g.callers())
        assert not self.in_aug_assign
        try:
            self.in_aug_assign = True
            self.visit(node.target)
        finally:
            self.in_aug_assign = False
        self.visit(node.value)

    def do_ClassDef (self,node):
        self.n_contexts += 1
        parent_cx = self.context
        assert parent_cx == node.stc_context
        # Inject the symbol table for this node.
        node.stc_symbol_table = SymbolTable(parent_cx)
        # Define the function name itself in the enclosing context.
        self.define_name(parent_cx,node.name)
        # Visit the children in a new context.
        self.context = node
        for z in node.bases:
            self.visit(z)
        for z in node.body:
            self.visit(z)
        for z in node.decorator_list:
            self.visit(z)
        self.context = parent_cx

    def do_FunctionDef (self,node):
        self.n_contexts += 1
        parent_cx = self.context
        assert parent_cx == node.stc_context
        # Inject the symbol table for this node.
        node.stc_symbol_table = SymbolTable(parent_cx)
        # Add a list of all returns
        
        node.stc_symbol_table.returns = []
        
        # Define the function name itself in the enclosing context.
        self.define_name(parent_cx,node.name)
        # Visit the children in a new context.
        self.context = node
        pprint(self.context.stc_symbol_table.returns)
        self.visit(node.args)
        for z in node.body:
            self.visit(z)
        for z in node.decorator_list:
            self.visit(z)
        self.context = parent_cx
        
    def do_Return(self,node):
        assert hasattr(self.context.stc_symbol_table, 'returns'), "Return outside of function"
        self.context.stc_symbol_table.returns.append(node)
        if node.value:
            self.visit(node.value)

    def do_Global(self,node):
        cx = self.u.compute_module_cx(node)
        assert hasattr(cx,'stc_symbol_table'),cx
        node.stc_scope = cx
        for name in node.names:
            self.define_name(cx,name)
            
    def do_Import(self,node):
        self.alias_helper(node)
                
    def do_ImportFrom(self,node):
        self.alias_helper(node)

    def alias_helper(self,node):
        cx = node.stc_context
        assert cx
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name.split('.')[0]
            # if alias.asname: g.trace('%s as %s' % (alias.name,alias.asname))
            self.define_name(cx,name)

    def do_Lambda(self,node):
        self.n_contexts += 1
        parent_cx = self.context
        assert parent_cx == node.stc_context
        # Inject the symbol table for this node.
        node.stc_symbol_table = SymbolTable(parent_cx)
        # There is no lambda name.
        # Handle the lambda args.
        for arg in node.args.args:
            if isinstance(arg,ast.Name):
                # Python 2.x.
                assert isinstance(arg.ctx,ast.Param),arg.ctx
                # Define the arg in the lambda context.
                self.define_name(node,arg.id)
            else:
                # Python 3.x.
                assert isinstance(arg,ast.arg),arg
                assert isinstance(arg,ast.arg),arg
                self.define_name(node,arg.arg)
            arg.stc_scope = node
        # Visit the children in the new context.
        self.context = node
        # self.visit(node.args)
        self.visit(node.body)
        self.context = parent_cx

    def do_Module (self,node):
        self.n_contexts += 1
        assert self.context is None
        assert node.stc_context is None
        # Inject the symbol table for this node.
        node.stc_symbol_table = SymbolTable(node)
        # Visit the children in the new context.
        self.context = node
        for z in node.body:
            self.visit(z)
        self.context = None
       # print(node.stc_symbol_table)

    def do_Name(self,node):
        # g.trace('P1',node.id)
        
        # self.visit(node.ctx)
        cx = node.stc_context
        if isinstance(node.ctx,(ast.Param,ast.Store)):
            # The scope is unambigously cx, **even for AugAssign**.
            # If there is no binding, we will get an UnboundLocalError at run time.
            # However, AugAssigns do not actually assign to the var.
            assert hasattr(cx,'stc_symbol_table'),cx
            self.define_name(cx,node.id,defined = not self.in_aug_assign)
            node.stc_scope = cx
        else:
            # ast.Store does *not* necessarily define the scope.
            # For example, a += 1 generates a Store, but does not defined the symbol.
            # Instead, only ast.Assign nodes really define a symbol.
            node.stc_scope = None

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
    '''A class to infer the types of objects.'''
    
   # def __init__ (self):
    #    AstFullTraverser.__init__(self)

    def __call__(self,node):
        self.init()
        return self.run(node)
    
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
        self.functions = {}
        self.fun_params = []

        self.stats = Stats()
        self.u = Utils()
        
        # Local stats
        self.n_nodes = 0
        
        # Detecting circular inferences
        self.call_stack = [] # Detects recursive calls
        self.assign_stack = [] # Detects circular assignments.

        # Create the builtin type dict.
        ''' TODO: Differing number of parameters. '''
        self.builtin_type_dict = {
            'eval': {'parameter_types': [set([string_type])],
                     'return_types': [set([any_type])]},
            'id':   {'parameter_types': [set([any_type])],
                     'return_types': [set([int_type])]},
            'str':  {'parameter_types': [set([any_type])],
                     'return_types': [set([string_type])]},
            'len':  {'parameter_types': [set([any_type])],
                     'return_types': [set([int_type])]},
            'range':  {'parameter_types': [set([int_type])],   # Needs one than one parameter
                     'return_types': [set([ List_Type(None, [], set([int_type]) ) ])] },
            'ord':  {'parameter_types': [set([string_type])],
                     'return_types': [set([int_type])]},
            'chr':  {'parameter_types': [set([int_type])],
                     'return_types': [set([string_type])]},
            # list,tuple...
            # close,open,sort,sorted,super...
        }
        
        self.bin_op_constraints = {
            'Add' : { float_type.kind : [float_type, int_type],
                       int_type.kind  : [float_type, int_type],
                    #   List_Type().kind : [List_Type()],
                       string_type : [string_type] }, 
            'Mult' : { float_type : [float_type, int_type],
                       int_type : [float_type, int_type, List_Type, string_type],
                       List_Type: [List_Type, int_type],
                       string_type.kind: [string_type, int_type] },
            'Sub' : { float_type : [float_type, int_type],
                       int_type : [float_type, int_type],
                       List_Type: [List_Type] }                                
        }
        
       
    def run (self,root):        
        self.visit(root)

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

    def do_Attribute (self,node):
        ti = self
        trace = False and not g.app.runningAllUnitTests
        
        # g.trace(ti.format(node),node.value,node.attr)
        t = ti.visit(node.value) or [] ###
        t = ti.clean(t)
        t = ti.merge_failures(t)
        tag = '%s.%s' % (t,node.attr) # node.attr is always a string.
        if t:
            if len(t) == 1:
                ti.stats.n_not_fuzzy += 1
                t1 = t[0]
                if ti.kind(t1) == 'Class_Type':
                    aList = t1.cx.ivars_dict.get(node.attr)
                    aList = ti.clean(aList) if aList else []
                    if aList:
                        t = []
                        for node2 in aList:
                            t.extend(ti.visit(node2))
                        t = ti.clean(t)
                        ti.set_cache(node,t,tag='ti.Attribute')
                        ti.stats.n_attr_success += 1
                    elif t1.cx.bases:
                        pass ### Must check super classes.
                        t = set([Unknown_Type(node)])
                    else:
                        t = set([Unknown_Type(node)])
                else:
                    ti.stats.n_attr_fail += 1
                    t = set([Unknown_Type(node)])
            else:
                ti.stats.n_fuzzy += 1
        else:
            t = set([Unknown_Type(node)])
        # ti.check_attr(node) # Does nothing
        return [t]

    def do_Name(self,node):
        # Check whether the name is a function argument
        if node.id in self.fun_params:
            return [node.id]
        if self.currently_assigning:
            return [node.id]
        # Stupidly True and False are Names. Return bool type
        if (node.id == "True" or node.id == "False"):
            return [set([bool_type])]
        if node.id in self.variableTypes:
            return [self.variableTypes[node.id]]
        else:
            return [set([none_type])]
    
    def do_Assign(self,node):
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
                assert isinstance(value, Container_Type), "Error: Assigning non container type to a container"
                # Unpack the lists
                self.container_assignment(targets[i], value, node)
                continue
            
            if isinstance(value_types[i], Container_Type):
                value_types[i].infer_types()
                value_types[i] = set([value_types[i]])
                
            self.variableTypes[targets[i]] = value_types[i]
            # For each new assign, check whether any are waiting on it.
            self.check_waiting(targets[i])
        
    def container_assignment(self, target_container, value_container, node):
        assert isinstance(target_container, Container_Type)
        assert isinstance(value_container, Container_Type)
        
        targets = target_container.contents
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
            result_types = self.constraint_gen.do_BinOp(left_types, right_types, op_kind)
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
        for t in left_types:
                print(type(t))
                if isinstance(type(t), String_Type):
                    print("t is string")
        
        for left in left_types:
            for right in right_types:
                # Any_Type checkes
                ''' TODO: do this better | check the type is acceptable'''
                if isinstance(left, Any_Type) and isinstance(right, Any_Type):
                    return [set([any_type])]
                if isinstance(left, Any_Type):
                    result_types |= set(self.bin_op_constraints[op_kind][right.kind])
                    continue
                if isinstance(right, Any_Type):
                    result_types |= set(self.bin_op_constraints[op_kind][left])

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
                if op_kind == 'Mult' and (
                        (left <= string_type and right <= int_type) or
                        (left <= int_type and right <= string_type)):
                    result_types.add(string_type)
                    continue
            self.stats.n_binop_fail += 1
        assert result_types, "No acceptable BinOp operation. "
        return [result_types]
    
    def do_UnaryOp(self,node):
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
        all_types = []
        for z in node.values:
            all_types.extend(self.visit(z))
        return [set(all_types)]

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
        return [Dict_Type(node)]
    
    def do_If(self,node):
        self.visit(node.test)
        for z in node.body:
            self.visit(z)
        for z in node.orelse:
            self.visit(z)
        phis = node.afterPhis
        for phi in phis:
            self.visit(phi)
            
        pprint(self.variableTypes)
        
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
        pprint(self.variableTypes)
                
    def do_For(self, node):
        ''' TODO: Allow for any Iterable object in node.iter instead of just List_Type. '''
        # This is a glorified assignment so set to true
        self.currently_assigning = True
        targets = self.visit(node.target)
        self.currently_assigning = False
        print("targets")
      #  pprint(targets)
        print("types")
        value_types = self.visit(node.iter)
        pprint(value_types)
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
        return [extracted_types]
        
    def do_Import(self, node):
        for z in node.names:
            self.visit(z)
            
    def do_ImportFrom(self, node):
        ''' TODO: Give the names the type module. '''
        for z in node.names:
            self.visit(z)
            
    def do_alias (self,node):
        ''' Add the name as a Module type.
            TODO: Link the module to the name.
            TODO: Sort out cx '''
        self.variableTypes[node.id] = set({Module_Type(node.module_name, node)})        

    def do_Call (self,node):
        ''' Infer the value of a function called with a particular set of 
            arguments.
            TODO: Change so builtins can have more than 1 set of parameters. '''
        # Special case builtins.
        return_types = []
        given_arg_types = []
        for z in node.args:
            given_arg_types.extend(self.visit(z))
        func_name = self.find_function_call(node)
        print(func_name)
        func = self.builtin_type_dict.get(func_name,[])
        if func:
            return_types = func['return_types']
            accepted_types = func['parameter_types']
            # At least for now, assume the parameters are the same length
            assert(len(given_arg_types) == len(accepted_types))
            for i in range(len(given_arg_types)):
                pprint(given_arg_types[i])
                pprint(accepted_types[i])
                # If the arg is a function parameter then we can not type check
                # generate a constraint and then move on.
                if given_arg_types[i] in self.fun_params:
                    self.constraint_gen.do_Call(accepted_types[i], given_arg_types[i])
                    continue
                # ... otherwise type check. At least one type must match up.
                for t1 in given_arg_types[i]:
                    type_allowed = False
                    for t2 in accepted_types[i]:
                        print("t1")
                        pprint(t1)
                        print("t2")
                        pprint(t2)
                        if (t1 <= t2):
                            type_allowed = True
                    assert type_allowed, "Incorrect type given to function"
            return return_types
        # Cannot find the function. Return any
        return [set([any_type])]
            
    def do_ListComp(self,node):
        ''' A list comp can edit values inside of comp. Therefore must reset the
            variable types.
            TODO: Tuple in node.elt should result in List(Tuple(type)). '''
        old_type_list = self.variableTypes.copy()
        
        for node2 in node.generators:
            self.visit(node2)
        t = self.visit(node.elt)
        print("t")
        pprint(t)
        # Reset types
        self.variableTypes = old_type_list
        return [set([List_Type(node, list(t))])]

    def do_comprehension(self,node):
        ''' Assign types in the list to the variable name. '''
        self.currently_assigning = True
        targets = self.visit(node.target) # A name.
        self.currently_assigning = False
        value_types = self.visit(node.iter) # An attribute.
        value_types = self.extract_list_types(value_types)
        self.conduct_assignment(targets, value_types, node)
        #return [List_Type(node)]
        
    def do_FunctionDef (self,node):
        ''' Find all args and return values. '''
        pprint(node.stc_symbol_table.returns)
        # Create a constraint satisfaction problem for the arguments
        self.fun_params = self.visit(node.args)
        self.constraint_gen = ConstraintGenerator()
        self.constraint_gen(node, self.variableTypes, self.fun_params)
        
        for z in node.body:
            self.visit(z)
        for z in node.decorator_list:
            self.visit(z)
        
        self.constraint_gen.extract_results()
        self.constraint_gen.clear_list()
        # Constraint updates types for the params
        pprint(self.variableTypes)
            
    def extract_return_names(self, returns):
        ''' Returns can be '''
        for return_node in returns:
            pass
            
    def do_arguments(self,node):
        ''' We need to begin checking what types the args can take. Defaults
            already give us a nice possible value.
            The defaults list contains the value for the last len(defaults)
            arguments. '''
        args = []
        for z in node.args:
            args.extend(self.visit(z))
        defaults = []
        for z in node.defaults:
            defaults.extend(self.visit(z))
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

    def class_instance (self,e):      
        '''
        Return a type representing an instance of the class
        whose ctor is evaluated in the present context.
        '''
        
        ti = self
        trace = True and not g.app.runningAllUnitTests
        cx = e.self_context
        
        # Step 1: find the ctor if it exists.
        d = cx.st.d
        ctor = d.get('__init__')

            
        args = [] ### To do
        t = [Class_Type(cx)]
        # ti.set_cache(e,t,tag='class name')
        return args,t

    def find_call_e (self,node):
        '''Find the symbol table entry for node, an ast.Call node.'''
        ti = self
        trace = False and not g.app.runningAllUnitTests
        trace_errors = False; trace_fuzzy = True ; trace_return = False
        kind = ti.kind(node)
        e = None # Default.
        if kind == 'Name':
            # if trace: g.trace(kind,node.id)
            e = getattr(node,'e',None)
        else:
            t = ti.visit(node) or []
            if len(t) == 1:
                ti.stats.n_not_fuzzy += 1
                t = t[0]
                if ti.kind(t) == 'Class_Type':
                    d = t.cx.st.d
                    if ti.kind(node) == 'Attribute':
                        name = node.attr
                    elif ti.kind(node) == 'Call':
                        name = node.func
                    else:
                        name = None
                    if name:
                        e = d.get(name)
                    else:
                        e = None
                else:
                    if trace and trace_errors:
                        g.trace('not a class type: %s %s' % (ti.kind(t),ti.format(node)))
            elif len(t) > 1:
                if trace and trace_fuzzy: g.trace('fuzzy',t,ti.format(node))
                ti.stats.n_fuzzy += 1
                e = None

    def infer_actual_args (self,e,node):
        
        '''Return a list of types for all actual args, in the order defined in
        by the entire formal argument list.'''
        
        ti = self
        trace = False and not g.app.runningAllUnitTests
        trace_args = False
        assert ti.kind(node)=='Call'
        cx = e.self_context
        # Formals...
        formals  = cx.node.args or []
        defaults = cx.node.args.defaults or [] # A list of expressions
        vararg   = cx.node.args.vararg
        kwarg    = cx.node.args.kwarg
        # Actuals...
        actuals  = node.args or [] # A list of expressions.
        keywords = node.keywords or [] # A list of (identifier,expression) pairs.
        starargs = node.starargs
        kwargs   = node.kwargs
        assert ti.kind(formals)=='arguments'
        assert ti.kind(formals.args)=='list'
        
        formal_names = [z.id for z in formals.args]
            # The names of *all* the formal arguments, include those with defauls.
            # Doesw not include vararg and kwarg.
           
        # Append unnamed actual args.
        # These could be either non-keyword arguments or keyword arguments.
        args = [ti.visit(z) for z in actuals]
        bound_names = formal_names[:len(actuals)]
        
        if trace and trace_args:
            g.trace('formal names',formal_names)
            g.trace('   arg names',bound_names)
            g.trace('    starargs',starargs and ti.format(starargs))
            g.trace('    keywargs',kwargs   and ti.format(kwargs))
            # formal_defaults = [ti.visit(z) for z in defaults]
                # # The types of each default.
            # g.trace('formal default types',formal_defaults)
            # g.trace('unnamed actuals',ti.format(actuals))
        
        # Add keyword args in the call, in the order they appear in the formal list.
        # These could be either non-keyword arguments or keyword arguments.
        keywargs_d = {}
        keywords_d = {}
        for keyword in keywords:
            name = keyword.arg
            t = ti.visit(keyword.value)
            value = ti.format(keyword.value)
            keywords_d[name] = (value,t)

        for name in formal_names[len(actuals):]:
            data = keywords_d.get(name)
            if data:
                value,t = data
                if trace and trace_args: g.trace('set keyword',name,value,t)
                args.append(t)
                bound_names.append(name)
            # else: keywargs_d[name] = None ### ???

        # Finally, add any defaults from the formal args.
        n_plain = len(formal_names) - len(defaults)
        defaults_dict = {}
        for i,expr in enumerate(defaults):
            name = formal_names[n_plain+i]
            value = ti.format(expr)
            t = ti.visit(expr)
            defaults_dict[name] = (value,t)

        for name in formal_names:
            if name not in bound_names:
                data = defaults_dict.get(name)
                t = None # default
                if data:
                    value,t = data
                    if trace and trace_args: g.trace('set default',name,value,t)
                elif name == 'self':
                    def_cx = e.self_context
                    class_cx = def_cx and def_cx.class_context
                    if class_cx:
                        t = [Class_Type(class_cx)]
                if t is None:
                    t = [Unknown_Arg_Type(node)]
                    ti.error('Unbound actual argument: %s' % (name))
                args.append(t)
                bound_names.append(name)
                
        ### Why should this be true???
        # assert sorted(formal_names) == sorted(bound_names)

        if None in args:
            g.trace('***** opps node.args: %s, args: %s' % (node.args,args))
            args = [z for z in args if z is not None]
            
        if trace: g.trace('result',args)
        return args

    def infer_def(self,node,rescan_flag):
        
        '''Infer everything possible from a def D called with specific args:
        
        1. Bind the specific args to the formal parameters in D.
        2. Infer all assignments in D.
        3. Infer all outer expression in D.
        4. Infer all return statements in D.
        '''
        
        ti = self
        trace = False and not g.app.runningAllUnitTests
        return ###

        # t0 = ti.get_call_cache(e,hash_) or []
        # if hash_ in ti.call_stack and not rescan_flag:
            # # A recursive call: always add an Recursive_Instance marker.
            # if trace:g.trace('A recursive','rescan',rescan_flag,hash_,'->',t0)
            # ti.stats.n_recursive_calls += 1
            # t = [Recursive_Inference(node)]
        # else:
            # if trace: g.trace('A',hash_,'->',t0)
            # ti.call_stack.append(hash_)
            # try:
                # cx = e.self_context
                # # data = ti.switch_context(e,hash_,node)
                # ti.bind_args(specific_args,cx,e,node)
                # ti.infer_assignments(cx,e)
                # ti.infer_outer_expressions(cx,node)
                # t = ti.infer_return_statements(cx,e)
                # ti.restore_context(data)
            # finally:
                # hash2 = ti.call_stack.pop()
                # assert hash2 == hash_
        # # Merge the result and reset the cache.
        # t.extend(t0)
        # t = ti.clean(t)
        # if trace: g.trace('B',hash_,'->',t)
        # return t
    #@+node:ekr.20130315094857.9501: *7* ti.bind_args (ti.infer_def helper) (To do: handle self)
    # Call(expr func, expr* args, keyword* keywords, expr? starargs, expr? kwargs)
    #   keyword = (identifier arg, expr value) # keyword arguments supplied to call

    # FunctionDef(identifier name, arguments args, stmt* body, expr* decorator_list)
    #   arguments = (expr* args, identifier? vararg, identifier? kwarg, expr* defaults)

    def bind_args (self,types,cx,e,node):
        
        ti = self
        trace = False and not g.app.runningAllUnitTests
        assert ti.kind(node)=='Call'
        assert isinstance(node.args,list),node
        formals = cx.node.args or []
        assert ti.kind(formals)=='arguments'
        assert ti.kind(formals.args)=='list'
        formal_names = [z.id for z in formals.args]
            # The names of *all* the formal arguments, include those with defauls.
            
        if len(formal_names) != len(types):
            # g.trace('**** oops: formal_names: %s types: %s' % (formal_names,types))
            return

        def_cx = e.self_context
        d = def_cx.st.d
        for i,name in enumerate(formal_names):
            pass ### 
            ### Handle self here.
            # t = types[i]
            # e2 = d.get(name)
            # if e2:
                # if trace: g.trace(e2,t) # g.trace(e2.name,t)
                # ti.set_cache(e2,[t],tag='bindargs:%s'%(name))
            # else:
                # g.trace('**** oops: no e2',name,d)
    #@+node:ekr.20130315094857.9502: *7* ti.infer_assignments
    def infer_assignments(self,cx,e):       
        '''Infer all the assignments in the function context.'''
        ti = self
        trace = False and not g.app.runningAllUnitTests
        for a in cx.assignments_list:
            if ti.kind(a) == 'Assign': # ignore AugAssign.
                pass ####

                # t2 = ti.get_cache(a)
                # if t2:
                    # ti.stats.n_assign_hits += 1
                    # if trace: g.trace('hit!',t2)
                # else:
                    # t2 = ti.visit(a)
                    # t3 = ti.ignore_failures(t2)
                    # if t3:
                        # ti.stats.n_assign_misses += 1
                        # # g.trace('***** set cache',t2)
                        # ti.set_cache(a,t2,tag='infer_assns')
                        # if trace: g.trace('miss',t2)
                    # else:
                        # ti.stats.n_assign_fails += 1
                        # if trace: g.trace('      
        return None # This value is never used.
    
    def infer_outer_expressions(self,cx,node):
        '''Infer all outer expressions in the function context.'''
        ti = self
        trace = False and not g.app.runningAllUnitTests
        for exp in cx.expressions_list:
            if trace: g.trace(ti.format(exp))
            ti.stats.n_outer_expr_misses += 1
            t = ti.visit(exp)

        return None # This value is never used.

    def infer_return_statements(self,cx,e):
        '''Infer all return_statements in the function context.'''
        ti = self
        trace = False and not g.app.runningAllUnitTests
        t = []
        for r in cx.returns_list:
            t2 = ti.visit(r)
            if trace: g.trace('miss',t2)
            t.extend(t2)
        if ti.has_failed(t):
            t = ti.merge_failures(t)
        else:
            t = ti.clean(t)
        return t

    def do_Compare(self,node):
        ''' A comparison will always return a boolean type.
            TODO: Check if errors can occur as a result of a comparison. '''
        self.visit(node.left)
        for z in node.comparators:
            self.visit(z)
        return [set([bool_type])]

    def do_Expr(self,node):
        ti = self
        t = ti.visit(node.value)
        return t

    def do_GeneratorExp (self,node):
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

    def do_Index(self,node):    
        return self.visit(node.value)

    def do_Lambda (self,node):
        ti = self
        return ti.visit(node.body)

    def do_Slice(self,node):
        ti = self
        if node.upper: junk = ti.visit(node.upper)
        if node.lower: junk = ti.visit(node.lower)
        if node.step:  junk = ti.visit(node.step)
        return [ti.int_type] ### ???

    def do_Subscript(self,node):
        ti = self
        trace = False and not g.app.runningAllUnitTests
        t1 = ti.visit(node.value)
        t2 = ti.visit(node.slice)
        if t1 and trace: g.trace(t1,t2,ti.format(node))
        return t1 ### ?

    def do_Builtin(self,node):
        ti = self
        return [ti.builtin_type]

    def do_ClassDef(self,node):
        for z in node.body:
            self.visit(z)

    def count_full_args (self,node):
        '''Return the number of arguments in a call to the function/def defined
        by node, an ast.FunctionDef node.'''
        ti = self
        trace = False and not g.app.runningAllUnitTests
        assert ti.kind(node)=='FunctionDef'    
        args = node.args
        if trace: g.trace('args: %s vararg: %s kwarg: %s' % (
            [z.id for z in args.args],args.vararg,args.kwarg))
        n = len(args.args)
        if args.vararg: n += 1
        if args.kwarg:  n += 1
        return n
    
    def bind_outer_args (self,node):
        '''Bind all all actual arguments except 'self' to "Unknown_Arg_Type".'''
        ti = self
        trace = False and not g.app.runningAllUnitTests
        assert ti.kind(node)=='FunctionDef'
        e = node.e
        def_cx = e.self_context
        args = node.args or []
        assert ti.kind(args)=='arguments',args
        assert ti.kind(args.args)=='list',args.args
        formal_names = [z.id if hasattr(z,'id') else '<tuple arg>' for z in args.args]
        if args.vararg: formal_names.append(args.vararg)
        if args.kwarg:  formal_names.append(args.kwarg)
        # if trace: g.trace(formal_names)
        d = def_cx.st.d
        for name in formal_names:
            if name == 'self':
                if def_cx:
                    t = [Class_Type(def_cx)]
                else:
                    t = [Unknown_Arg_Type(node)]
                e2 = e
            else:
                t = [Unknown_Arg_Type(node)]
                e2 = d.get(name)

    def do_Return(self,node):
        self.visit(node.value)
        return
        return self.return_helper(node)
        
    def do_Yield(self,node):
        return self.return_helper(node)

    def return_helper(self,node):
        ti = self
        trace = False and not g.app.runningAllUnitTests
        e = ti.call_e
        assert e
        if node.value:
            t = ti.visit(node.value)
            if ti.has_failed(t):
                ti.stats.n_return_fail += 1
                t = ti.ignore_unknowns(t)
            if t:
                ti.stats.n_return_success += 1
            else:
                ti.stats.n_return_fail += 1
                t = [] # Do **not** propagate a failure here!
        else:
            t = [ti.none_type]
        if trace: g.trace(t,ti.format(node))
        return t

    def do_With (self,node):
        ti = self
        t = []
        for z in node.body:
            t.append(ti.visit(z))
        t = ti.clean(t)
        return t
