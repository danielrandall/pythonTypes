from pprint import pprint
import src.constraint as python_constraint
import src.binopconstraints as binopcons
from src.typeclasses import *

class ConstraintGenerator:
    ''' We're only interested in a parameter until it is assigned a value. '''
    
    def __call__(self, node, variable_types, parameters):
        self.variable_types = variable_types
        self.parameters = parameters
        self.init()
    
    def __init__(self):
        self.parameters = []
    
    def init(self):    
        temp = self.variable_types
        self.variableTypes = temp
        subsets_as_lists = list(self.powerset(binopcons.ALL_TYPES))
        subsets_as_sets = [set(x) for x in subsets_as_lists]
        self.csp_problem = python_constraint.Problem()
        self.csp_problem.addVariables(self.parameters, subsets_as_sets)
        
    def extract_results(self):
        # Extract results
        solutions = self.csp_problem.getSolutions()
        #pprint(solutions)
        biggest_sols = self.find_largest_set_in_list_of_dicts(solutions)
        self.update_types(biggest_sols)
        
    def update_types(self, param_types):
        ''' Set the type to any_type if it returns all types or the constraints
            solving failed (returned empty set). '''
        for var, types in param_types.items():
            assert isinstance(types, set)
            if len(types) == len(binopcons.ALL_TYPES) or types == set():
                self.variable_types[var] = set([any_type])
            else:
                self.variable_types[var] = types
    
    def clear_list(self):
        self.parameters = []    

    def powerset(self, seq):
        ''' Returns all the subsets of this set. This is a generator.
            Copy pasta from http://www.technomancy.org/python/powerset-generator-python/
        '''
        if len(seq) <= 1:
            yield seq
            yield []
        else:
            for item in self.powerset(seq[1:]):
                yield [seq[0]]+item
                yield item
            
    def find_largest_set_in_list_of_dicts(self, lod):
        ''' Given a list of dicts, then each for key in the dicts the largest set
            in the values is found. A dict containing the key and the largest
            set is returned. '''
        result_d = {}
        for d in lod:
            for k,v in d.items():
                if k not in result_d:
                    result_d[k] = v
                elif len(d[k]) > len(result_d[k]):
                    result_d[k] = v
        return result_d
    
    def some_in_set(self, candidates):
        ''' There needs to be at least one element in set_to_check which is also in
        candidates. '''
        return lambda set_to_check: any(x in set_to_check for x in candidates)

    def matching_element(self, set1, set2):
        ''' There needs to be at least one matching element in each set. '''
        return any(x in set2 for x in set1)

    def limit_to_set(self, limiting_set):
        ''' Every element in set_to_limit must also be in the limiting set. '''
        return lambda set_to_limit: all(x in limiting_set for x in set_to_limit)

    def required_elements_in_set(self, elements):
        ''' All members of set1 must also be present in elements. '''
        return lambda set1: all(x in set1 for x in elements)
    
    def do_Name(self,node):
        ''' We want to return the name if it's a parameter, otherwise we want
            to return the type. '''
        if node.id in self.parameters:
            return [node.id]
    
    def do_BinOp(self, left_types, right_types, op_kind, lineno):
        ''' Function must still return types.
            TODO: sub / mult '''
        #pprint(left_types)
        #pprint(right_types)
        if left_types not in self.parameters and right_types not in self.parameters:
            #return super(TypeInferrer, self).do_BinOp(node)
            return
        
        assert op_kind in binopcons.OP_TYPES.keys(), "Line " + str(lineno) + ": " + op_kind + " is not a valid op"
        
        if left_types in self.parameters and right_types in self.parameters:
            # We only need to worry about what types are limited by the operator
            limiting_types = binopcons.OP_TYPES[op_kind]
            # Limit the types of both variables
            self.csp_problem.addConstraint(self.limit_to_set(set(limiting_types)), [left_types])
            self.csp_problem.addConstraint(self.limit_to_set(set(limiting_types)), [right_types])
            # Force the parameters to share at least one type.
            self.csp_problem.addConstraint(self.matching_element, [left_types, right_types])
            return [set(limiting_types)]
        
        if left_types in self.parameters:
            param_to_constrain = left_types
            contributing_types = right_types
        elif right_types in self.parameters:
            param_to_constrain = right_types
            contributing_types = left_types
            
        for a_type in contributing_types:
            if isinstance(a_type, Any_Type):
                limiting_types = binopcons.OP_TYPES[op_kind]
            else:
                limiting_types = binopcons.BIN_OP_CONSTRAINTS[op_kind][a_type]
            self.csp_problem.addConstraint(self.limit_to_set(set(limiting_types)), [param_to_constrain])
            
        return [set(limiting_types)]
    
    def do_Attribute(self, value, attr, lineno):
        ''' Attempts to find all classes which has attr has a variable.
        
            Value is the parameter we are limiting. '''
        possible_types = set()
        for t in ALL_TYPES:
            if attr in t.get_vars():
                possible_types.add(t)
        # If no matches were found then return any_type
        if not possible_types:
            return [set([any_type])]
        self.csp_problem.addConstraint(self.limit_to_set(possible_types), [value])
        return [possible_types]
        
    def do_Call(self, accepted_types, param_to_constrain):
        ''' We're given all of the accept types and a parameter. The allowed
            types for this parameter must be within the allowed types. '''
        # No information can be extracted here.
        if any_type in accepted_types:
            return
        self.csp_problem.addConstraint(self.limit_to_set(accepted_types), [param_to_constrain])
        