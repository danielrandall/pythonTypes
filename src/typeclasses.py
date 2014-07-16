from utils import Utils

''' TODO - add variables and functions to global_vars '''

class BaseType:
    '''BaseType is the base class for all type classes.

    Subclasses of BaseType represent inferenced types.

    Do not change self.kind casually: self.kind (and __repr__ which simply
    returns self.kind) are real data: they are used by the TypeInferer class.
    The asserts in this class illustrate the contraints on self.kind.

    '''
    
    def __init__(self,kind):
        self.kind = kind
        self.global_vars = {}
        
    def __repr__ (self):
        return self.kind
    __str__ = __repr__
    
    ''' Does not detect subtypes aside from those involving Any.
        Previously used self.kind <= other.kind e.t.c. Not sure why... '''
    def is_type(self,other): return issubclass(other.__class__,BaseType)
    def __eq__(self, other): return self.is_type(other) and self.kind == other.kind
    def __ge__(self, other): return self.is_type(other) and ( (self.kind == 'Any' or other.kind == 'Any') or self.__eq__(other)  )
    def __gt__(self, other): return self.is_type(other) and (self.kind == 'Any' or other.kind == 'Any')
    def __hash__(self):      return hash(self.kind)
    def __le__(self, other): return self.is_type(other) and ( (self.kind == 'Any' or other.kind == 'Any') or self.__eq__(other) or issubclass(self.__class__, other.__class__) )
    def __lt__(self, other): return self.is_type(other) and (self.kind == 'Any' or other.kind == 'Any')
    def __ne__(self, other): return self.is_type(other) and self.kind != other.kind
    
    def contains_waiting_type(self):
        ''' Should be overriden for a type which may contain an Awaiting_Type.
        '''
        return False
    
    def is_callable(self):
        ''' Should be overriden for a type which is callable. '''
        return False
    
    def get_vars(self):
        ''' Returns the variables/functions contained in this class. '''
        return self.global_vars

class Any_Type(BaseType):    
    def __init__(self):
        BaseType.__init__(self,'Any')

class Bool_Type(BaseType):    
    ''' Contains no varibles/functions. '''
    def __init__(self):
        BaseType.__init__(self,'Bool')

class Builtin_Type(BaseType):    
    def __init__(self):
        BaseType.__init__(self,'Builtin')

class Bytes_Type(BaseType):    
    def __init__(self):
        BaseType.__init__(self,'Bytes')
        
class Callable_Type(BaseType):
    def __init__(self, kind):
        super().__init__(kind)
        self.supports_calling = True
        # Variables used for analysis of callable types
        self.parameter_types = []
        self.return_types = set()
        self.arg_default_length = 0
    
    def is_callable(self):
        return self.supports_calling
    
    def get_parameter_types(self):
        return self.parameter_types
    
    def get_return_types(self):
        return self.return_types
    
    def get_arg_default_length(self):
        return self.arg_default_length
    
class Attribute_Type():
        def __init__(self, class_type, variable_type):
            self.class_type = class_type
            self.variable_type = variable_type

class Class_Base():
    pass

# Note: ClassType is a Python builtin.
class Class_Type(Callable_Type, Class_Base):
    ''' Class to define classes. This is always callable due to init.
    
        TODO: Bultin functions such as __class__ .
        TODO: Only allow static functions to be called from here. '''
    def __init__(self, name, global_vars, has_call_func):
        ''' global_vars are variables accessible outside of the class. ''' 
        kind = 'Class Def: %s' % name
        super().__init__(kind)
        self.name = name
        self.global_vars = global_vars
        self.has_call_func = has_call_func
        self.call_param_types = None
        self.call_return_types = None
        
    def __repr__(self):
        return 'Class Dec: %s' % self.name
    
    def add_to_vars(self, name, new_var):
        if name in self.global_vars:
            self.global_vars[name] |= new_var
        else:
            self.global_vars[name] = new_var
    
    def set_init_params(self, parameter_types):
        self.parameter_types = parameter_types
    
    def set_callable_params(self, call_param_types, call_return_types):
        self.call_param_types = call_param_types
        self.call_return_types = call_return_types
    
    def get_return_types(self):
        ''' We want to return a new instance every time. '''
        return set([Class_Instance(self.name, self.global_vars.copy(), \
                              self.has_call_func, self.call_param_types, \
                              self.call_return_types)])
        
    def check_contains_variable(self, var):
        return var in self.global_vars
    
class Class_Instance(Callable_Type, Class_Base):
    ''' Used to represent initialised classes. '''
    def __init__(self, name, global_vars, has_call_func, call_parameter_types, \
                 call_return_types):
        kind = 'Class Instance: %s' % name
        super().__init__(kind)
        self.name = name
        self.global_vars = global_vars
        self.supports_calling = has_call_func
        self.parameter_types = call_parameter_types
        self.return_types = call_return_types
    
    def __repr__(self):
        return 'Class Instance: %s' % self.name
    
    def check_contains_variable(self, var):
        return var in self.global_vars
    
    def add_to_vars(self, name, new_var):
        if name in self.global_vars:
            self.global_vars[name] |= new_var
        else:
            self.global_vars[name] = new_var

class Def_Type(Callable_Type):    
    ''' TODO: deal with kind. '''
    def __init__(self, parameter_types, return_types, arg_default_length):
        kind = 'Def(%s)' % id(parameter_types)
        super().__init__(kind)
        self.parameter_types = parameter_types
        self.return_types = return_types
        self.arg_default_length = arg_default_length

class Dict_Type(BaseType):
    ''' TODO: Add values contained in a dict. '''
    def __init__(self):
        # For now, all dicts are separate types.
        # kind = 'Dict(%s)' % (Utils().format(node))
        kind = 'Dict(@%s)'
        BaseType.__init__(self, kind)
        
        self.global_vars = {# keys returns a dict view object - not yet supported
                            'keys' : set([Def_Type([],
                                  set([any_type]),
                                  0)]),
                            # items returns a dict view object - not yet supported
                            'items' : set([Def_Type([],
                                  set([any_type]),
                                  0)]),
                            # values returns a dict view object - not yet supported
                            'values' : set([Def_Type([],
                                  set([any_type]),
                                  0)])
                            }

class Inference_Failure(BaseType):
    def __init__(self, kind, node):
        BaseType.__init__(self,kind)
        u = Utils()
        verbose = False
        self.node = node
        node_kind = u.kind(node)
        suppress_node = ('Assign','Attribute','Call','FunctionDef')
        suppress_kind = ('Un_Arg',)
        
    def __repr__(self):
        return self.kind

    __str__ = __repr__

class Circular_Assignment(Inference_Failure):
    def __init__(self,node):
        kind = 'Circular_Assn'
        Inference_Failure.__init__(self,kind,node)
        
class Inference_Error(Inference_Failure):
    def __init__(self,node):
        kind = 'Inf_Err'
        Inference_Failure.__init__(self,kind,node)

class Recursive_Inference(Inference_Failure):
    def __init__(self,node):
        kind = 'Recursive_Inf'
        Inference_Failure.__init__(self,kind,node)
        
class Unknown_Type(Inference_Failure):
    def __init__(self,node):
        kind = 'Uknown_Type' # Short, for traces.
        Inference_Failure.__init__(self,kind,node)
        
class Unknown_Arg_Type(Inference_Failure):
    def __init__(self,node):
        kind = 'Unkown_Arg_Type'
        Inference_Failure.__init__(self,kind,node)
        
class Container_Type(BaseType):
    def __init__(self, kind, node, contents, c_types):
        ''' contents is used to for assignment and anything which may find
            knowing the elements of the list helpful. '''
        self.contents = contents 
        self.content_types = c_types
        BaseType.__init__(self,kind)
        
    def infer_types(self):
        ''' Calculate the types contained in the list.
            Check if any element is a list and calculate their types. '''
        # Don't infer it's already been done
        if not self.content_types:
            # All elements are sets.
            for element in self.contents:
                for t in element:
                    if isinstance(t, Container_Type):
                        t.infer_types()
                        self.content_types.add(t)
                    else:
           #             pprint(element)
                        self.content_types |= element
        self.define_kind()
        
    def contains_waiting_type(self):
        self.infer_types()
        for e in self.content_types:
            result = e.contains_waiting_type()
            if result:
                return result
        return False
    
    def define_kind(self):
        ''' Override this. '''
        raise NotImplementedError
    

class List_Type(Container_Type):
    ''' TODO: Add new types when the function append is called or similar. '''
    def __init__(self, node, contents, c_types):
        kind = 'List({})'
        Container_Type.__init__(self, kind, node, contents, c_types)
        
    def define_kind(self):
        self.kind = 'List(%s)' % repr(self.content_types)
    
class Tuple_Type(Container_Type):
    def __init__(self, node, contents, c_types):
        self.contents = contents 
        self.content_types = c_types
        kind = 'Tuple({})'
        Container_Type.__init__(self, kind, node, contents, c_types)
        
    def define_kind(self):
        self.kind = 'Tuple(%s)' % repr(self.content_types)

class Module_Type(BaseType):
    def __init__(self,cx,node):
        kind = 'Module(%s)@%s' % (cx,id(node))
        BaseType.__init__(self,kind)
        self.cx = cx # The context of the module.

class None_Type(BaseType):
    def __init__(self):
        BaseType.__init__(self,'None')

class Num_Type(BaseType):
    def __init__(self, type_class):
        BaseType.__init__(self,
            kind = type_class.__name__.capitalize())

''' Float and Int do not really get instantiated, but rather are used for
    for comparison using the kind. '''
class Float_Type(Num_Type):
    def __init__(self):
        Num_Type.__init__(self, float)

class Int_Type(Num_Type):
    def __init__(self):
        Num_Type.__init__(self, int)
        
class String_Type(BaseType):
    def __init__(self):
        BaseType.__init__(self,'String')
        
class Awaiting_Type(BaseType):
    def __init__(self, waitee, waiting_for):
        self.waitee = waitee
        self.waiting_for = waiting_for
            
        kind = 'Awaiting_Type'
        BaseType.__init__(self, kind)
            
    def contains_waiting_type(self):
        return self

class BuildTables:
    '''create global attribute tables.'''
    
    def run(self,files,root_d):
        
        self.attrs_d = {}
            # Keys are attribute names.
            # Values are lists of node.value nodes.
        self.defined_attrs = set()
        # self.classes_d = {}
            # NOT USED YET.
            # Keys are class names. Values are lists of classes.
        # self.defs_d = {}
            # NOT USED YET>
            # Keys are def names. Values are lists of defs.
        self.u = Utils()
        for fn in files:
            self.fn = fn
            for cx in self.u.contexts(root_d.get(fn)):
                self.do_context(cx)

    def do_context(self,cx):
        # Merge symbol table attrs_d into self.attrs_d.
        st = cx.stc_symbol_table
        d = st.attrs_d
        for key in d.keys():
            if self.attrs_d.has_key(key):
                aSet = self.attrs_d.get(key)
                aSet.update(d.get(key))
            else:
                self.attrs_d[key] = d.get(key)
        # Is this useful?
        self.defined_attrs |= st.defined_attrs
        
        
# Create singleton instances of simple types.
bool_type = Bool_Type()
builtin_type = Builtin_Type()
bytes_type = Bytes_Type()
float_type = Float_Type()
int_type = Int_Type()
none_type = None_Type()
string_type = String_Type()
any_type = Any_Type()

ALL_TYPES = [List_Type(None, [], set()), Dict_Type(), int_type, float_type, bool_type, string_type, bytes_type, builtin_type]