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

import sys
import imp
import queue
import ast
import gc
import glob
import io
import os
import time
from pprint import pprint

from src.constraintgenerator import ConstraintGenerator
import src.binopconstraints as binopcons
from src.utils import Utils
from src.traversers.astfulltraverser import AstFullTraverser
from src.traversers.astformatter import AstFormatter
from src.typeclasses import *
from src.pyfile import *
from src.traversers.ssatraverser import Phi_Node
from src.importdependent import ImportDependent



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
        self.currently_assigning = False
        self.awaiting_Typing = []  # Elements : (node, name)
        self.fun_params = []
        # The class definition we are currently under
        self.current_class = None

        self.u = Utils()
        
        # Local stats
        self.n_nodes = 0
        
        # Detecting circular inferences
        self.call_stack = [] # Detects recursive calls
        self.assign_stack = [] # Detects circular assignments.

        # Add the builtin_types to the variable dict
        self.variableTypes.update(BUILTIN_TYPE_DICT)
        
       
    def run(self, file_tree):
        ''' file_tree is a list of pyfiles.
            TODO: Do this file find outside of this module... '''
        # Keys are module name, values their typed dicts
        file_list = self.file_tree_to_list(file_tree)
        for file in file_list:
            assert isinstance(file, PyFile), "Error: Not a Python file"
            if file.has_been_typed():
                continue
            dependents = self.check_dependents(file, file_tree)
            self.type_file(file, dependents) 
            
    def check_dependents(self, file, file_tree):
        ''' TODO: Detect circular references.
            TODO: Wildcard imports '''
        dependent_vars = {}
        if file.has_been_typed():
            #dependent_vars[file.get_name()] = set([Module_Type(file.get_name(), file.get_global_vars())])
            return dependent_vars
        root = file.get_source()
        for dependent in root.import_dependents:
                assert isinstance(dependent, ImportDependent)
                name = dependent.get_module_name()
                as_name = dependent.get_as_name()
                directory = dependent.get_directory_no_name()
               # assert(directory in file_tree), "File not found"
               
                # If can't find it then just set it to any   
                if not directory in file_tree or name not in file_tree[directory]:
                    dependent_vars[as_name] = set([any_type])
                    continue
                
                dependent_file = file_tree[directory][name]
                dependent_dependents = self.check_dependents(dependent_file, file_tree)
                self.type_file(dependent_file, dependent_dependents)
                # Check if a specific class is imported from the module
                pprint(dependent_file.get_global_vars())
                if dependent.is_import_from():
                    value = dependent_file.get_global_vars()[dependent.get_class_name()]
                else:
                    value = set([Module_Type(name, dependent_file.get_global_vars())])
                dependent_vars[as_name] = value
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
        print("Printing module: ----------------------------- " + file.get_name() + " ------------------------------")   
        self.variableTypes = root.variableTypes
        self.init()
     #   print("-DEPENDENTS-")
     #   pprint(dependents)
        self.variableTypes.update(dependents)
        self.visit(root)
        pprint(self.variableTypes)
        file.set_global_vars(self.variableTypes)
        file.typed = True
    
    def visit(self, node):
        '''Visit a single node.  Callers are responsible for visiting children.'''
        if hasattr(node, "phi_nodes"):
            phis = node.phi_nodes
            for phi in phis:
                self.visit(phi)
        method = getattr(self,'do_' + node.__class__.__name__)
        self.n_nodes += 1
        return method(node)

    def do_Attribute (self, node):
        ''' Always a variable of the form x.y .
            TODO: For assignments x.y = ? and x can be a number of different classes - do something clever. '''
        print(node.lineno)
        print(node.value)
        print(node.attr)
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
                    if node.attr in n.global_vars:
                        result_types |= n.global_vars[node.attr]
                        # Add the context - change this to work with others
                        if isinstance(n, Class_Base):
                            n.update_dependents(node.attr, node.stc_context)
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
        if node.id == "self" or (self.current_class and node.id == self.current_class.get_name()):
            assert self.current_class, "self used outside of class definition. "
            return [set([self.current_class])]
        if node.id in self.variableTypes:
            return [self.variableTypes[node.id]]
        # Check if name has already been analysed (i.e. has an SSA)
        pass
        # Check if name is defined somewhere in the future
        found = self.find_in_parent_contexts(node.id, node.stc_context)
        if found:
            found_node, found_context = found
            self.visit(found_node)
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
        ''' TODO: Stop comparisons with instantiation of Container_Type.
            TODO: Deal with fun params better '''
        assert(len(value_types) == len(targets)), "Line " + str(node.lineno)
        for i in range(len(targets)):
            # Switch fun param to types
            if value_types[i] in self.fun_params:
                value_types[i] = self.variableTypes[value_types[i]]
            for e in value_types[i]:
                print(e)
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
                    self.variableTypes[targets[i]] = set([Awaiting_Type(targets[i], result.waitee)])
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
                assert value <= Container_Type(None, None, None, None), "Line " + str(node.lineno) + ": Assigning non-container type to a container"
                # Unpack the lists
                self.container_assignment(targets[i], value, node)
                continue
            
            if isinstance(value_types[i], Container_Type):
                value_types[i].infer_types()
                value_types[i] = set([value_types[i]])
                
            # This is updating types in a container. e.g. x[i] = 5
            # We need to return here as it is not a traditional assignment
            if isinstance(targets[i], ContainerUpdate):
                if targets[i].is_slice():
                    pprint(value_types[i])
                    extracted_types = self.extract_container_types([value_types[i]])[0]
                    assert extracted_types, "Line " + str(node.lineno) + ": Assigning non-container type to a slice"
                    # Replace value_types (a container) with the types it contains
                    value_types[i] = extracted_types
                for container in targets[i].get_container_list():
                    container.update_content_types(value_types[i])
                return   
            
            if isinstance(targets[i], Awaiting_Type):
                pass  
                
            # Class globals has a special assignment
            if isinstance(targets[i], Attribute_Type):
                self.attribute_assignment(targets[i], value_types[i])
            else:
                print(node.lineno)
                print(targets[i])
                print(value_types[i])
                self.variableTypes[targets[i]] = value_types[i]
            # For each new assign, check whether any are waiting on it.
            self.check_waiting(targets[i])
            
    def attribute_assignment(self, target, value):
        ''' Update the types of the variable and then update those that
            reference it. '''
        class_instance = target.class_type
        attr = target.variable_type
        # Update the types in the var
        type_changed = class_instance.update_vars_types(attr, value)
        if type_changed:
            # Update all others
            update_list = class_instance.get_var_depedent_list(attr)
            old_vars = self.variableTypes
            for to_update in update_list:
                self.visit(to_update)
            self.variableTypes = old_vars
        
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
        print(node.left)
        print(node.right)
        
        op_kind = self.kind(node.op)
        
        # Check if this operation depends on variable awaiting the type of
        # another
        for a_type in left_types:
            if (isinstance(a_type, Awaiting_Type)):
                return [set([a_type])]
        for a_type in right_types:
            if (isinstance(a_type, Awaiting_Type)):
                return [set([a_type])]
        
        
        if left_types in self.fun_params or right_types in self.fun_params:
            result_types = self.constraint_gen.do_BinOp(left_types, right_types, op_kind, node.lineno)
            if left_types in self.fun_params:
                left_types = result_types[0] # Will return a list of 1 element
            if right_types in self.fun_params:
                right_types = result_types[0] # ''
        
        result_types = set()
        
        for left in left_types:
            for right in right_types:
                # Any_Type checks
                ''' TODO: do this better | check the type is acceptable
                    TODO: List types less explicitly'''
                if isinstance(left, Any_Type) and isinstance(right, Any_Type):
                    return [set([any_type])]
                if isinstance(left, Any_Type):
                    result_types |= set(binopcons.BIN_OP_CONSTRAINTS[op_kind][List_Type if isinstance(right, List_Type) else right])
                    continue
                if isinstance(right, Any_Type):
                    print(op_kind)
                    print(left)
                    print(node.lineno)
                    result_types |= set(binopcons.BIN_OP_CONSTRAINTS[op_kind][List_Type if isinstance(left, List_Type) else left])
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
                
                if op_kind == 'Mult' and isinstance(left, List_Type) and right <= int_type:
                    result_types.add(left)
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
        pprint(left_types)
        print(node.op)
        pprint(right_types)
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
                assert(False)
        a_type = [set([Unknown_Type(node)])]
        return a_type
    
    def do_BoolOp(self, node):
        ''' For and/or
            Never fails.
            Boolean operators can return any types used in its values.
            ie. len(x) or [] can return Int or List.
            TODO: Deal with fun param better '''
        all_types = set()
        for z in node.values:
            types = self.visit(z)[0]
            # Get the types if it's a fun param
            if types in self.fun_params:
                types = self.variableTypes[types]
            all_types |= types
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
        return [set([Dict_Type()])]
    
    def do_If(self,node):
        self.visit(node.test)
        for z in node.body:
            self.visit(z)
        for z in node.orelse:
            self.visit(z)
      #  phis = node.afterPhis
      #  for phi in phis:
      #      self.visit(phi)
        
    def do_Phi_Node(self, node):
        if not node.get_targets():
            return
        var = node.get_var()
        self.variableTypes[var] = set()
        for target in node.get_targets():
            if (target == Phi_Node.TARGET_NOT_DECLARED):
                possibleTypes = set([none_type])
            # Target can't be awaiting_type
            
            elif target in self.variableTypes and not any([isinstance(x, Awaiting_Type) for x in self.variableTypes[target]]):
                possibleTypes = self.variableTypes[target]
            else:
                # Variable is used in the future
                self.awaiting_Typing.append((node, target))
                self.variableTypes[var] = set([Awaiting_Type(var, target)])
                return
            self.variableTypes[var] |= possibleTypes
            self.check_waiting(var)
        
    def do_While (self, node):
        self.visit(node.test) 
        self.loop_helper(node)
    
    def loop_helper(self, node):
        # Type the phis before the loop
    #    phis = node.beforePhis
    #    for phi in phis:
    #        self.visit(phi)
                
        for z in node.body:
            self.visit(z)
        for z in node.orelse:
            self.visit(z)
        # Type the phis after the loop
    #    phis = node.afterPhis
    #    for phi in phis:
    #        self.visit(phi)
                
    def do_For(self, node):
        ''' TODO: Allow for any Iterable object in node.iter instead of just List_Type. '''
        # This is a glorified assignment so set to true
        self.currently_assigning = True
        targets = self.visit(node.target)
        self.currently_assigning = False
        value_types = self.visit(node.iter)
        # value_types should be a list.
      #  assert isinstance(value_types, List_Type)
        self.conduct_assignment(targets, self.extract_container_types(value_types), node)
        self.loop_helper(node)
        
    def extract_container_types(self, list_of_containers):
        ''' Should be given a list of sets which contains only List_Type.
            This function returns a list containing a single set which contains
            all types find in each list. '''
        extracted_types = set()
        assert isinstance(list_of_containers, list)
        for possible_types in list_of_containers:
            for container_type in possible_types:
                if container_type == any_type:
                    return [set([any_type])]
                if container_type <= Container_Type(None, None, None, None):
                    container_type.infer_types()     # Just to make sure
                    extracted_types |= container_type.content_types
        # If nothing is found then return any_type
        if extracted_types:
            return [extracted_types]
        else:
            return [set([any_type])]  

    def do_Call (self, node):
        ''' Infer the value of a function called with a particular set of 
            arguments. '''
        given_arg_types = []
        result_types = set()
        if node.lineno == 157:
            pass
        for z in node.args:
            given_arg_types.extend(self.visit(z))
        print("Given arg types")
        pprint(given_arg_types)
        pprint(self.variableTypes)
        possible_funcs = self.visit(node.func)[0]
        print("node.func")
        if isinstance(node.func, ast.Name):
            print(node.func.id)
        print("Function possible types")
        pprint(possible_funcs)
        # Check Awaiting_Type
        for a_type in possible_funcs:
            if isinstance(a_type, Awaiting_Type):
                return [set([a_type])]
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
            assert len(given_arg_types) <= len(accepted_types), "Line: " + str(node.lineno) + " Given: " + str(given_arg_types) + " Accepted: " + str(accepted_types)
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
                    if isinstance(t1, Awaiting_Type):
                        return [set([t1])]
                    type_allowed = False
                    for t2 in accepted_types[i]:
                        if (t1 <= t2):
                            type_allowed = True
                    print(i)
                    assert type_allowed, "Line " + str(node.lineno) + ": Incorrect type given to function. Got: " + str(given_arg_types[i]) + ". Expected: " + str(accepted_types[i])
            result_types |= func_return_types
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
        value_types = self.extract_container_types(value_types)
        self.conduct_assignment(targets, value_types, node)
        #return [List_Type(node)]
        
    def do_FunctionDef(self, node):
        ''' Find all args and return values.
        
            TODO: Find out possible types in *karg dict. '''
  #      print(node.lineno)
        self.variableTypes = node.variableTypes
        self.variableTypes.update(node.stc_context.variableTypes)

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
        
        print("Final types")
        pprint(self.variableTypes)
        
        if node.name == "__init__" and self.current_class:
            self.current_class.set_init_params(parameter_types)
        
        # Restore variables
        self.variableTypes = node.stc_context.variableTypes
        
        fun_type = Def_Type(parameter_types, self.fun_return_types, node.args.default_length)
        self.variableTypes[node.name] = set([fun_type])
        # Add to the currently class vars if there is one
        if self.current_class:
            self.current_class.update_vars_types(node.name, self.variableTypes[node.name])
        # Clear awaiting_typings - not needed outside of this scope
        self.awaiting_Typing.clear()
            
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
            assert(args[0] == "self"), "Line " + str(node.lineno) + ": First argument of function " + node.stc_parent.name + " should be self."
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
        return args
            
    def do_arg(self, node):
        return [node.arg]
    
    def do_ClassDef(self, node):
        ''' The __init__ will provide us with the majority of the self. vars
            so we want to analyse that first.
            TODO: Reverse base class list and update that way to avoid list comp. '''
        self.variableTypes = node.variableTypes
        self.variableTypes.update(node.stc_context.variableTypes)
        
        if node.name == "RGB":
            pass
        
        parent_class = self.current_class
        # Deal with inheritence.
        inherited_vars = {}
        for base in node.bases:
            base_class = self.visit(base)[0]
            acceptable_type = False
            for possible_type in base_class:
                if possible_type == any_type:
                    # What the hell do I do here?
                    acceptable_type = True
                if isinstance(possible_type, Class_Type):
                    # If there is a clash, the first instance will be used
                    inherited_vars.update({k:v for k,v in possible_type.get_vars().items() if k not in inherited_vars})
                    acceptable_type = True
            assert acceptable_type, "Line " + str(node.lineno) + ": " + base.id + " is not a class. "
        # Add the self variables found
   #     for self_var in node.self_variables:
   #         if self_var not in inherited_vars:
   #             inherited_vars[self_var] = set()
        self.current_class = Class_Type(node.name, inherited_vars, node.callable)
        self.move_init_to_top(node.body, node)
        
        for z in node.body:
            self.visit(z)
        # We need to set the parameters for init
     #   init_def = list(self.variableTypes["__init__"])[0]
        
        # Set the call if possible
        is_callable, call_node = node.callable
        if is_callable:
            fun = list(self.variableTypes[call_node.name])
            # Should be a list of size 1
            assert len(fun) == 1, "__call__ multiply defined. "
            self.current_class.set_callable_params(fun[0].get_parameter_types(), fun[0].get_return_types())
        
        pprint("class globals")
        pprint(node.self_variables)
        
        # Restore parents variables
        self.variableTypes = node.stc_context.variableTypes
        self.variableTypes[node.name] = set([self.current_class])
        self.current_class = parent_class
        
    def move_init_to_top(self, body, node):
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
            arg.arg = "self"
            init_def.args.args = [arg]
            init_def.args.defaults = []
            init_def.name = "__init__"
            init_def.variableTypes = {}
            init_def.lineno = 0
            init_def.stc_context = node
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
        print("value")
        print(node.value)
        print(node.lineno)
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
        junk = ti.visit(node.elt)
        t = []
        for node2 in node.generators:
            t2 = ti.visit(node2)
            t.extend(t2)
        if ti.has_failed(t):
            t = ti.merge_failures(t)
        else:
            t = ti.clean(t)
        return t
    
    def do_Lambda (self, node):
        return self.visit(node.body)

    def do_Index(self, node):    
        ''' TODO: Adjust this so it checks the type.
            Lists have to be int
            Dicts can have any type for a key. '''
        value_types = self.visit(node.value)[0]
        if value_types in self.fun_params:
            self.constraint_gen.do_Slice(value_types)
            return
        int_like_types = [x for x in value_types if x <= any_type]
        assert int_like_types, "Line " + str(node.lineno) + ": index value must be an integer"
        return

    def do_Slice(self, node):
        ''' No need to return anything here.
            TODO: Do better with awaiting_type '''
        if node.upper:
            upper_types = self.visit(node.upper)[0]
            if upper_types in self.fun_params:
                self.constraint_gen.do_Slice(upper_types)
                return
            int_like_types = [x for x in upper_types if x <= int_type or isinstance(x, Awaiting_Type)]
            assert int_like_types, "Line " + str(node.lineno) + ": upper in slice must be an integer"
        if node.lower:
            lower_types = self.visit(node.lower)[0]
            if lower_types in self.fun_params:
                self.constraint_gen.do_Slice(lower_types)
                return
            int_like_types = [x for x in lower_types if x <= int_type or isinstance(x, Awaiting_Type)]
            assert int_like_types, "Line " + str(node.lineno) + ": lower in slice must be an integer"
        if node.step:
            step_types = self.visit(node.step)[0]
            if step_types in self.fun_params:
                self.constraint_gen.do_Slice(step_types)
                return
            int_like_types = [x for x in step_types if x <= int_type or isinstance(x, Awaiting_Type)]
            assert int_like_types, "Line " + str(node.lineno) + ": step in slice must be an integer"
        return

    def do_Subscript(self, node):
        ''' You can have slice assignment. e.g. x[0:2] = [1, 2]
            TODO: Allow user-defined types to index/slice.
            TODO: Stop comparing with an instantiation of Container_Type - will probably be solved with the above. '''
        value_types = self.visit(node.value)[0]
        print(node.lineno)
        if self.currently_assigning:
            if isinstance(value_types, Attribute_Type):
                ct = value_types.class_type
                vt = value_types.variable_type
                value_types = ct.get_global_var(vt)
            elif isinstance(value_types, ContainerUpdate):
                value_types = value_types.get_container_list()
            else:    
                # Check whether variable can be a container
                value_types = self.variableTypes[value_types]
        if value_types in self.fun_params:
            value_types = self.constraint_gen.do_Subscript(node.slice, value_types)
        # Check awaiting_type
        for a_type in value_types:
            if isinstance(a_type, Awaiting_Type):
                return [set([a_type])]
        # Check container type
        container_like_types = [x for x in value_types if x <= Container_Type(None, None, None, None)]
        pprint(self.variableTypes)
        pprint(value_types)
        pprint(container_like_types)
        assert container_like_types, "Line " + str(node.lineno) + ": cannot index/slice in non-container types. "
        
        # When checking the type of slice we can't have currently_assigning being true
        old_ca = self.currently_assigning
        self.currently_assigning = False
        self.visit(node.slice)
        self.currently_assigning = old_ca
        
        if self.currently_assigning:
            return [ContainerUpdate(container_like_types, isinstance(node.slice, ast.Slice))]
        
        if isinstance(node.slice, ast.Slice):
            # Should return list
            return [value_types]
        if isinstance(node.slice, ast.Index):
            # Should return something in the list
            return_types = set()
            for possible_container in container_like_types:
                pprint(container_like_types)
                if isinstance(possible_container, Any_Type):
                    return [set([any_type])]
                return_types |= possible_container.content_types
            return [return_types]
        assert False, "How did I get here?"

    def do_Builtin(self, node):
        ti = self
        return [ti.builtin_type]
        
    def do_Yield(self, node):
        return

    def do_With (self, node):
        ''' Uses __enter__ and __exit__ methods to ensure initialisation and cleaning of the variable.
            TODO: Add new variable temporarily. '''
        for z in node.items:
            self.visit(z)
        for z in node.body:
            self.visit(z)
    
    def do_withitem(self, node):
        ''' Equivalent to an assignment.
            TODO: Make it call __enter__ method here. '''
        self.variableTypes[node.optional_vars] = set([any_type])
        return
        assignment = ast.Assign()
        assignment.targets = [node.optional_vars]
        assignment.value = node.context_expr
        self.visit(assignment)
