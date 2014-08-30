from utils import Utils
from src.typechecking.basictypevariable import BasicTypeVariable

''' TODO - add variables and functions to global_vars '''

class BaseType:
    '''BaseType is the base class for all type classes.

    Subclasses of BaseType represent inferenced types.

    Do not change self.kind casually: self.kind (and __repr__ which simply
    returns self.kind) are real data: they are used by the TypeInferer class.
    The asserts in this class illustrate the contraints on self.kind.

    '''
    
    def __init__(self, kind, global_vars = {}):
        self.kind = kind
        self.global_vars = global_vars
        
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
    
    def is_callable(self):
        ''' Should be overriden for a type which is callable. '''
        return False
    
    def get_contents_types(self):
        ''' Needs to be overriden by tuples/lists.'''
        return set()
    
    def get_global_var(self, var):
        ''' Returns the variables/functions contained in this class. '''
        if var in self.global_vars:
            return self.global_vars[var]
        else:
            return None
        
    def has_any_base(self):
        return False
        
    def get_vars(self):
        return self.global_vars
    
    def set_var(self, name, var):
        self.global_vars[name] = var
        
    def get_return_types(self):
        return None

class Any_Type(BaseType):    
    def __init__(self):
        BaseType.__init__(self,'Any')
        
    def get_contents_types(self):
        return set([Any_Type()])
    
    def is_callable(self):
        return True
    
    def get_return_types(self):
        return BasicTypeVariable([Any_Type()])

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
        
        self.global_vars = { # capitalize(self) -> str
                            'capitalize' : BasicTypeVariable([Def_Type([],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            
                            # center(self, width: int, fillchar: str = ' ') -> str
                            'center' : BasicTypeVariable([Def_Type([BasicTypeVariable([Int_Type()]), BasicTypeVariable([self])],
                                                                    BasicTypeVariable([self]),
                                                                    1)]),
                            # count(self, x: str) -> int
                            'count' : BasicTypeVariable([Def_Type([BasicTypeVariable([self])],
                                                                    BasicTypeVariable([Int_Type()]),
                                                                    0)]),
                            
                            # decode(self, encoding: str = 'utf-8', errors: str = 'strict') -> str
                    #        'decode' : BasicTypeVariable([Def_Type([BasicTypeVariable([String_Type(), String_Type()]), BasicTypeVariable([self])],
                     #                                               BasicTypeVariable([String_Type()]),
                     #                                               2)]),
                            
                            # endswith(self, suffix: str, start: int = 0, end: int = None) -> bool
                            'endswith': BasicTypeVariable([Def_Type([ BasicTypeVariable([self]), BasicTypeVariable([Int_Type()]), BasicTypeVariable([Int_Type()])],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    2)]),
                            
                            # expandtabs(self, tabsize: int = 8) -> str
                            'expandtabs': BasicTypeVariable([Def_Type([ BasicTypeVariable([Int_Type()])],
                                                                    BasicTypeVariable([self]),
                                                                    1)]),
                            
                            # find(self, sub: str, start: int = 0, end: int = 0) -> int:
                            'find': BasicTypeVariable([Def_Type([ BasicTypeVariable([self]), BasicTypeVariable([Int_Type()]), BasicTypeVariable([Int_Type()])],
                                                                    BasicTypeVariable([self]),
                                                                    2)]),
                            
                            # format(self, *args: Any, **kwargs: Any) -> str
                            'format': BasicTypeVariable([Def_Type([],
                                                                    BasicTypeVariable([Any_Type()]),
                                                                    0,
                                                                    True)]),
                            
                            # format_map(self, map: Mapping[str, Any]) -> str
                            'format_map': BasicTypeVariable([Def_Type([ BasicTypeVariable([Any_Type()])],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            
                            # index(self, sub: str, start: int = 0, end: int = 0) -> int
                            'index': BasicTypeVariable([Def_Type([ BasicTypeVariable([self]), BasicTypeVariable([Int_Type()]), BasicTypeVariable([Int_Type()])],
                                                                    BasicTypeVariable([Int_Type()]),
                                                                    2)]),
                            
                            # isalnum(self) -> bool
                            'isalnum': BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                            
                            # isalpha(self) -> bool
                            'isalpha': BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                            
                            # isdecimal(self) -> bool
                            'isdecimal': BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                            
                            # isdigit(self) -> bool
                            'isdigit': BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                            
                            # isidentifier(self) -> bool
                            'isidentifier': BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                            
                            # islower(self) -> bool
                            'islower': BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                            
                            # isnumeric(self) -> bool
                            'isnumeric': BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                            
                            # isprintable(self) -> bool
                            'isprintable': BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                            
                            # isspace(self) -> bool
                            'isspace': BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                            
                            # istitle(self) -> bool
                            'istitle': BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                            
                            # isupper(self) -> bool
                            'isupper': BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                      
                            #  join(self, iterable: Iterable[str]) -> str:
                            'join': BasicTypeVariable([Def_Type([BasicTypeVariable([Any_Type()])],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            
                            # ljust(self, width: int, fillchar: str = ' ') -> str
                            'ljust': BasicTypeVariable([Def_Type([  BasicTypeVariable([Int_Type()]),   BasicTypeVariable([self])],
                                                                    BasicTypeVariable([self]),
                                                                    1)]),
                            
                            # lower(self) -> str
                            'lower': BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            
                            # lstrip(self, chars: str = None) -> str
                            'lstrip': BasicTypeVariable([Def_Type([ BasicTypeVariable([self]) ],
                                                                    BasicTypeVariable([self]),
                                                                    1)]),
                            
                            # partition(self, sep: str) -> Tuple[str, str, str]
                            'lstrip': BasicTypeVariable([Def_Type([ BasicTypeVariable([self]) ],
                                                                    BasicTypeVariable([Tuple_Type()]),
                                                                    0)]),
                            
                            # replace(self, old: str, new: str, count: int = -1) -> str
                            'replace': BasicTypeVariable([Def_Type([BasicTypeVariable([self]), BasicTypeVariable([self]), BasicTypeVariable([Int_Type()])],
                                                                    BasicTypeVariable([self]),
                                                                    1)]),
                            
                            # rfind(self, sub: str, start: int = 0, end: int = 0) -> int
                            'rfind': BasicTypeVariable([Def_Type([BasicTypeVariable([self]), BasicTypeVariable([Int_Type()]), BasicTypeVariable([Int_Type()])],
                                                                    BasicTypeVariable([Int_Type()]),
                                                                    2)]),
                            
                            # rindex(self, sub: str, start: int = 0, end: int = 0) -> int
                            'rindex': BasicTypeVariable([Def_Type([BasicTypeVariable([self]), BasicTypeVariable([Int_Type()]), BasicTypeVariable([Int_Type()])],
                                                                    BasicTypeVariable([Int_Type()]),
                                                                    2)]),         
                            
                            # rjust(self, width: int, fillchar: str = ' ') -> str
                            'rindex': BasicTypeVariable([Def_Type([  BasicTypeVariable([Int_Type()]),  BasicTypeVariable([self])  ],
                                                                    BasicTypeVariable([self]),
                                                                    1)]),                  
                            
                            # rpartition(self, sep: str) -> Tuple[str, str, str]
                            'rpartition': BasicTypeVariable([Def_Type([  BasicTypeVariable([self])  ],
                                                                    BasicTypeVariable([Tuple_Type()]),
                                                                    0)]),   
                            
                            # rsplit(self, sep: str = None, maxsplit: int = -1) -> List[str]
                            'rsplit': BasicTypeVariable([Def_Type([  BasicTypeVariable([self]), BasicTypeVariable([Int_Type()]) ],
                                                                    BasicTypeVariable([List_Type()]),
                                                                    2)]),   
                            
                            # rstrip(self, chars: str = None) -> str
                            'rstrip': BasicTypeVariable([Def_Type([  BasicTypeVariable([self])  ],
                                                                    BasicTypeVariable([self]),
                                                                    1)]),  
                            
                            # split(self, sep: str = None, maxsplit: int = -1) -> List[str]
                            'split': BasicTypeVariable([Def_Type([BasicTypeVariable([self]), BasicTypeVariable([Int_Type()])],
                                                                    BasicTypeVariable([List_Type()]),
                                                                    2)]),
                            
                            # splitlines(self, keepends: bool = False) -> List[str]
                            'splitlines': BasicTypeVariable([Def_Type([  BasicTypeVariable([Bool_Type()])  ],
                                                                    BasicTypeVariable([List_Type()]),
                                                                    1)]),
                            
                            # startswith(self, prefix: str, start: int = 0, end: int = None) -> bool
                            'startswith': BasicTypeVariable([Def_Type([  BasicTypeVariable([self]), BasicTypeVariable([Int_Type()]), BasicTypeVariable([Int_Type()])  ],
                                                                    BasicTypeVariable([ Bool_Type() ]),
                                                                    2)]),
                            
                            # strip(self, chars: str = None) -> str
                            'strip': BasicTypeVariable([Def_Type([  BasicTypeVariable([self])  ],
                                                                    BasicTypeVariable([self]),
                                                                    1)]),  
                            
                            # swapcase(self) -> str
                            'swapcase': BasicTypeVariable([Def_Type([  ],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            
                            # title(self) -> str
                            'title': BasicTypeVariable([Def_Type([  ],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),  
                            
                            # translate(self, table: Dict[int, Any]) -> str
                            'translate': BasicTypeVariable([Def_Type([ BasicTypeVariable([Dict_Type()]) ],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),  
                            
                            # upper(self) -> str
                            'upper': BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            
                            # zfill(self, width: int) -> str
                            'zfill': BasicTypeVariable([Def_Type([  BasicTypeVariable([Int_Type()]) ],
                                                                    BasicTypeVariable([self]),
                                                                    0)]), 
                            
                            # __getitem__(self, i: Union[int, slice]) -> str
                            '__getitem__' : BasicTypeVariable([Def_Type([Any_Type()],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            
                            # __add__(self, s: str) -> str
                            '__add__' : BasicTypeVariable([Def_Type([self],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            
                            # __len__(self) -> int
                            '__len__' : BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([Int_Type()]),
                                                                    0)]),
                            
                            # __contains__(self, s: object) -> bool
                            '__contains__' : BasicTypeVariable([Def_Type([ Any_Type() ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                            
                            # __iter__(self) -> Iterator[str]
                            '__iter__' : BasicTypeVariable([Def_Type([],
                                                                    BasicTypeVariable([Any_Type()]),
                                                                    0)]),
                            
                            # __str__(self) -> str
                            '__str__' : BasicTypeVariable([Def_Type([],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            
                            # __repr__(self) -> str
                            '__repr__' : BasicTypeVariable([Def_Type([],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            
                            # __int__(self) -> int
                            '__int__' : BasicTypeVariable([Def_Type([],
                                                                    BasicTypeVariable([Int_Type()]),
                                                                    0)]),
                            
                            # __float__(self) -> float
                            '__float__' : BasicTypeVariable([Def_Type([],
                                                                    BasicTypeVariable([Float_Type()]),
                                                                    0)]),
                            
                            # __hash__(self) -> int
                            '__hash__' : BasicTypeVariable([Def_Type([],
                                                                    BasicTypeVariable([Int_Type()]),
                                                                    0)]),
                            
                            
                            '__dict__' : BasicTypeVariable([Any_Type()]),

                            }
        
    def is_callable(self):
        ''' Can always initialise a class definition. '''
        return True
        
    def get_return_types(self):
        ''' We want to return a new instance every time. '''
        #  return BasicTypeVariable([self])
        # Need to copy as it is liable to change
        return BasicTypeVariable([self])
        
class Callable_Type():
    def __init__(self):
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
    ''' The types of global class variables are kept here. '''
    def __init__(self):
        self.any_base_class = False
    
    
    def has_any_base(self):
        return self.any_base_class

# Note: ClassType is a Python builtin.
class Class_Type(Class_Base, BaseType):
    ''' Class to define classes. This is always callable due to init.
    
        TODO: Bultin functions such as __class__ .
        TODO: Only allow static functions to be called from here. '''
    def __init__(self, name, global_vars, has_call_func=False):
        ''' global_vars are variables accessible outside of the class. ''' 
        kind = 'Class Def: %s' % name
        Class_Base.__init__(self)
        BaseType.__init__(self, kind)
        self.name = name
        self.global_vars = global_vars
        self.has_call_func = has_call_func
        self.call_param_types = None
        self.call_return_types = None
        self.any_base_class = False
        
        if "__name__" not in self.global_vars:
            self.global_vars["__name__"] = BasicTypeVariable([Any_Type()])
        if "__class__" not in self.global_vars:
            self.global_vars["__class__"] = BasicTypeVariable([Any_Type()])
        if "__dict__" not in self.global_vars:
            self.global_vars["__class__"] = BasicTypeVariable([Any_Type()])
        if "__doc__" not in self.global_vars:
            self.global_vars["__class__"] = BasicTypeVariable([Any_Type()])
        if "__weakref__" not in self.global_vars:
            self.global_vars["__class__"] = BasicTypeVariable([Any_Type()])
        if "__init__" not in self.global_vars:
            self.global_vars["__class__"] = BasicTypeVariable([Any_Type()])
        if "__module__" not in self.global_vars:
            self.global_vars["__class__"] = BasicTypeVariable([Any_Type()])
        
            
        
    def get_contents_types(self):
        return set([Any_Type()])
        
    def __repr__(self):
        return 'Class Dec: %s' % self.name
    
    def get_name(self):
        return self.name
    
    def set_any_base(self):
        self.any_base_class = True
    
    def set_init_params(self, parameter_types):
        self.parameter_types = parameter_types
        
    
    
    def set_callable_params(self, call_param_types, call_return_types):
        self.call_param_types = call_param_types
        self.call_return_types = call_return_types
        
    def is_callable(self):
        ''' Can always initialise a class definition. '''
        return True
    
    def get_return_types(self):
        ''' We want to return a new instance every time. '''
      #  return BasicTypeVariable([self])
        # Need to copy as it is liable to change
        return BasicTypeVariable([Class_Instance(self.name, self.global_vars.copy(), \
                              self.has_any_base())])
    
class Class_Instance(Class_Base, BaseType):
    ''' Used to represent initialised classes. '''
    def __init__(self, name, global_vars, any_base):
        kind = 'Class Instance: %s' % name
        Class_Base.__init__(self)
        BaseType.__init__(self, kind)
        self.name = name
        self.global_vars = global_vars
        self.any_base_class = any_base
    
    def __repr__(self):
        return 'Class Instance: %s' % self.name
    
    def is_callable(self):
        return "__call__" in self.global_vars
    
    def get_return_types(self):
        if "__call__" in self.global_vars:
            return self.global_vars["__call__"]
        
    def get_contents_types(self):
        if "__getitem__" in self.global_vars:
            return set([Any_Type()])
        else:
            return BaseType.get_contents_types(self)
            
class Module_Type(Class_Base, BaseType):
    def __init__(self, global_vars):
        kind = 'Module()'
        BaseType.__init__(self, kind, global_vars)
        Class_Base.__init__(self)

class Def_Type(Callable_Type, BaseType):    
    ''' TODO: deal with kind. '''
    def __init__(self, parameter_types, return_types, arg_default_length, is_kwarg_vaarg=False):
        kind = 'Def(%s)' % id(parameter_types)
        BaseType.__init__(self, kind)
        Callable_Type.__init__(self)
        self.parameter_types = parameter_types
        self.return_types = return_types
        self.arg_default_length = arg_default_length
        self.is_kwarg_vaarg = is_kwarg_vaarg
        
    def get_return_types(self):
        return self.return_types
    
    def get_is_kwarg(self):
        return self.is_kwarg_vaarg
    
    def get_default_length(self):
        return self.arg_default_length
    
    def get_parameter_types(self):
        return self.parameter_types

class Inference_Failure(BaseType):
    def __init__(self, kind, node):
        BaseType.__init__(self,kind)
        u = Utils()
        self.node = node

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
        
class Container_Type():
    def __init__(self, node, contents, c_types):
        ''' contents is used to for assignment and anything which may find
            knowing the elements of the list helpful. '''
        self.contents = contents 
        self.content_types = c_types
        
    def infer_types(self):
        ''' Calculate the types contained in the list.
            Check if any element is a list and calculate their types. '''
        self.content_types = set([Any_Type()])
        # Don't infer it's already been done
     #   if not self.content_types:
         # All elements are sets.
     #   for element in self.contents:
     #       for t in element:
     #           if isinstance(t, Container_Type):
     #               t.infer_types()
     #               self.content_types.add(t)
     #           else:
     #               print(element)
     #               self.content_types |= element
        self.define_kind()
        
    def get_contents_types(self):
        return set([Any_Type()])
        
    def update_content_types(self, new_types):
        self.content_types |= new_types
        self.infer_types()
    
    def define_kind(self):
        ''' Override this. '''
        raise NotImplementedError
    
class ContainerUpdate():
        ''' Used to indicate a slice/index update is occurring. '''
        def __init__(self, container_list, slice_update):
            self.container_list = container_list
            self.slice_update = slice_update
            
        def get_container_list(self):
            return self.container_list
        
        def is_slice(self):
            return self.slice_update
        
class Dict_Type(Container_Type, Class_Base, BaseType):
    ''' TODO: Add values contained in a dict. '''
    def __init__(self):
        kind = 'dict(@%s)'
        BaseType.__init__(self, kind)
        Class_Base.__init__(self)
        Container_Type.__init__(self, None, [], set([Any_Type()]))
        
        self.global_vars = {
                            # clear(self) -> None
                            'clear' : BasicTypeVariable([Def_Type([  ],
                                                         BasicTypeVariable([None_Type()]),
                                                          0)]),
                            
                            # copy(self) -> Dict[KT, VT]
                            'copy' : BasicTypeVariable([Def_Type([  ],
                                                         BasicTypeVariable([self]),
                                                          0)]),
                            
                            # get(self, k: KT, default: VT=None) -> VT
                            'get' : BasicTypeVariable([Def_Type([ BasicTypeVariable([Any_Type()]), BasicTypeVariable([Any_Type()]) ],
                                                         BasicTypeVariable([Any_Type()]),
                                                          1)]),
                            
                            # pop(self, k: KT, default: VT=None) -> VT
                            'pop' : BasicTypeVariable([Def_Type([ BasicTypeVariable([Any_Type()]), BasicTypeVariable([Any_Type()]) ],
                                                         BasicTypeVariable([Any_Type()]),
                                                          1)]),
                            
                            # popitem(self) -> Tuple[KT, VT]
                            'popitem' : BasicTypeVariable([Def_Type([ ],
                                                         BasicTypeVariable([Tuple_Type()]),
                                                          0)]),
                            
                            # setdefault(self, k: KT, default: VT=None) -> VT
                            'setdefault' : BasicTypeVariable([Def_Type([ BasicTypeVariable([Any_Type()]), BasicTypeVariable([Any_Type()]) ],
                                                         BasicTypeVariable([Any_Type()]),
                                                          1)]),
                            
                            # update(self, m: Mapping[KT, VT]) -> None
                            'update' : BasicTypeVariable([Def_Type([ BasicTypeVariable([Any_Type()]) ],
                                                         BasicTypeVariable([None_Type()]),
                                                          0)]),
            
                            
                            # keys returns a dict view object - not yet supported
                            'keys' : BasicTypeVariable([Def_Type([],
                                                        BasicTypeVariable([Any_Type()]),
                                                        0)]),
                            
                            # items returns a dict view object - not yet supported
                            'items' : BasicTypeVariable([Def_Type([],
                                                         BasicTypeVariable([Any_Type()]),
                                                          0)]),
                            
                            # values returns a dict view object - not yet supported
                            'values' : BasicTypeVariable([Def_Type([],
                                                           BasicTypeVariable([Any_Type()]),
                                                           0)]),
                            
                            # fromkeys(seq: Sequence[_T]) -> Dict[_T, Any]: pass  # TODO: Actually a class method
                            # fromkeys(seq: Sequence[_T], value: _S) -> Dict[_T, _S]
                            'fromKeys' : BasicTypeVariable([Def_Type([Any_Type() ],
                                                           BasicTypeVariable([Any_Type()]),
                                                           0)]),
                            
                            # __len__(self) -> int
                            '__len__' : BasicTypeVariable([Def_Type([ ],
                                                           BasicTypeVariable([Int_Type()]),
                                                           0)]),
                            
                            # __getitem__(self, k: _KT) -> _VT: pass
                            '__getitem__' : BasicTypeVariable([Def_Type([Any_Type()],
                                                           BasicTypeVariable([Any_Type()]),
                                                           0)]),
                            
                            # __setitem__(self, k: _KT, v: _VT) -> None
                            '__setitem__' : BasicTypeVariable([Def_Type([ Any_Type(), Any_Type() ],
                                                           BasicTypeVariable([None_Type()]),
                                                           0)]),
                            
                            # __delitem__(self, v: _KT) -> None
                            '__delitem__' : BasicTypeVariable([Def_Type([ Any_Type() ],
                                                           BasicTypeVariable([None_Type()]),
                                                           0)]),
                            
                            # __contains__(self, o: object) -> bool
                            '__contains__' : BasicTypeVariable([Def_Type([Any_Type()],
                                                           BasicTypeVariable([Bool_Type()]),
                                                           0)]),
                            
                            # __iter__(self) -> Iterator[_KT]
                            '__iter__' : BasicTypeVariable([Def_Type([ ],
                                                           BasicTypeVariable([Any_Type()]),
                                                           0)]),
                            
                            # __str__(self) -> str
                            #'__str__' : BasicTypeVariable([Def_Type([ ],
                             #                              BasicTypeVariable([String_Type()]),
                              #                             0)]),
                            
                            
                            '__dict__' : BasicTypeVariable([Any_Type()]),
                            }
        
    def is_callable(self):
        ''' Can always initialise a class definition. '''
        return True
    
    def get_return_types(self):
        ''' We want to return a new instance every time. '''
      #  return BasicTypeVariable([self])
        # Need to copy as it is liable to change
        return BasicTypeVariable([self])
        
    def define_kind(self):
        self.kind = 'dict(%s)' % repr(self.content_types)
        
class Set_Type(Container_Type, Class_Base, BaseType):
    ''' TODO: Add new types when the function append is called or similar. '''
    def __init__(self):
        kind = 'set({})'
        BaseType.__init__(self, kind)
        Container_Type.__init__(self, None, [], set())
        Class_Base.__init__(self)
        
        self.global_vars = {
                            # add(self, element: T) -> None
                            'add' : BasicTypeVariable([Def_Type([ BasicTypeVariable([Any_Type()]) ],
                                                         BasicTypeVariable([None_Type()]),
                                                          0)]),
                            
                            # clear(self) -> None
                            'clear' : BasicTypeVariable([Def_Type([],
                                                                    BasicTypeVariable([None_Type()]),
                                                                    0)]),
                            
                            # copy(self) -> set[T]
                            'copy' : BasicTypeVariable([Def_Type([],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            
                            # difference(self, s: Iterable[Any]) -> set[T]
                            'difference' : BasicTypeVariable([Def_Type([  BasicTypeVariable([Any_Type()])  ],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            
                            # difference_update(self, s: Iterable[Any]) -> None
                            'difference_update' : BasicTypeVariable([Def_Type([  BasicTypeVariable([Any_Type()])  ],
                                                                    BasicTypeVariable([None_Type()]),
                                                                    0)]),
                            
                            # discard(self, element: T) -> None
                            'discard' : BasicTypeVariable([Def_Type([  BasicTypeVariable([Any_Type()])  ],
                                                                    BasicTypeVariable([None_Type()]),
                                                                    0)]),
                            
                            # intersection(self, s: Iterable[Any]) -> set[T]
                            'intersection' : BasicTypeVariable([Def_Type([  BasicTypeVariable([Any_Type()])  ],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            
                            # intersection_update(self, s: Iterable[Any]) -> None
                            'intersection_update' : BasicTypeVariable([Def_Type([  BasicTypeVariable([Any_Type()])  ],
                                                                    BasicTypeVariable([None_Type()]),
                                                                    0)]),
                            
                            # isdisjoint(self, s: AbstractSet[Any]) -> bool
                            'isdisjoint' : BasicTypeVariable([Def_Type([  BasicTypeVariable([Any_Type()])  ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                            
                            # issubset(self, s: AbstractSet[Any]) -> bool
                            'isdisjoint' : BasicTypeVariable([Def_Type([  BasicTypeVariable([Any_Type()])  ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                            
                            # issuperset(self, s: AbstractSet[Any]) -> bool
                            'issuperset' : BasicTypeVariable([Def_Type([  BasicTypeVariable([Any_Type()])  ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                            
                            # pop(self) -> T
                            'issuperset' : BasicTypeVariable([Def_Type([    ],
                                                                    BasicTypeVariable([Any_Type()]),
                                                                    0)]),
                            
                            # remove(self, element: T) -> None
                            'remove' : BasicTypeVariable([Def_Type([  BasicTypeVariable([Any_Type()])  ],
                                                                    BasicTypeVariable([None_Type()]),
                                                                    0)]),
                            
                            # symmetric_difference(self, s: Iterable[T]) -> set[T]
                            'symmetric_difference' : BasicTypeVariable([Def_Type([  BasicTypeVariable([Any_Type()])  ],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            
                            # symmetric_difference_update(self, s: Iterable[T]) -> None
                            'symmetric_difference_update' : BasicTypeVariable([Def_Type([  BasicTypeVariable([Any_Type()])  ],
                                                                    BasicTypeVariable([None_Type()]),
                                                                    0)]),
                            
                            # union(self, s: Iterable[T]) -> set[T]
                            'union' : BasicTypeVariable([Def_Type([  BasicTypeVariable([Any_Type()])  ],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            
                            # update(self, s: Iterable[T]) -> None
                            'update' : BasicTypeVariable([Def_Type([  BasicTypeVariable([Any_Type()])  ],
                                                                    BasicTypeVariable([None_Type()]),
                                                                    0)]),
                            
                            # __len__(self) -> int
                            '__len__' : BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([Int_Type()]),
                                                                    0)]),
                            
                            # __contains__(self, o: object) -> bool
                            '__contains__' : BasicTypeVariable([Def_Type([ Any_Type() ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                            
                            # __iter__(self) -> Iterator[T]
                            '__iter__' : BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([Any_Type()]),
                                                                    0)]),
                            
                            # __str__(self) -> str
                            '__str__' : BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([String_Type()]),
                                                                    0)]),      
                            
                            # __and__(self, s: AbstractSet[Any]) -> set[_T]
                             '__and__' : BasicTypeVariable([Def_Type([ Any_Type() ],
                                                                    BasicTypeVariable([ self ]),
                                                                    0)]),                   
                            
                            '__dict__' : BasicTypeVariable([Any_Type()]),

                            }
        
    def is_callable(self):
        ''' Can always initialise a class definition. '''
        return True
    
    def get_return_types(self):
        ''' We want to return a new instance every time. '''
      #  return BasicTypeVariable([self])
        # Need to copy as it is liable to change
        return BasicTypeVariable([self])
        
    def define_kind(self):
        self.kind = 'set(%s)' % repr(self.content_types)

class List_Type(Container_Type, Class_Base, BaseType):
    ''' TODO: Add new types when the function append is called or similar. '''
    def __init__(self):
        kind = 'List({})'
        BaseType.__init__(self, kind)
        Container_Type.__init__(self, None, [], set())
        Class_Base.__init__(self)
        
        self.global_vars = {#clear(self) -> None
                            'clear' : BasicTypeVariable([Def_Type([],
                                                                    BasicTypeVariable([None_Type()]),
                                                                    0)]),
                            # copy(self) -> List[T]
                            'copy' : BasicTypeVariable([Def_Type([],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            # append(self, object: T) -> None
                            'append' : BasicTypeVariable([Def_Type([BasicTypeVariable([Any_Type()])],
                                                                    BasicTypeVariable([None_Type()]),
                                                                    0)]),
                            
                            # extend(self, iterable: Iterable[_T]) -> None
                            'extend' : BasicTypeVariable([Def_Type([BasicTypeVariable([Any_Type()])],
                                                                    BasicTypeVariable([None_Type()]),
                                                                    0)]),
                            
                            # pop(self, index: int = -1) -> T
                            'pop' : BasicTypeVariable([Def_Type([BasicTypeVariable([Int_Type()])],
                                                                    BasicTypeVariable([Any_Type()]),
                                                                    1)]),
                            # index(self, object: T, start: int = 0, stop: int = Undefined(int)) -> int
                            'index' : BasicTypeVariable([Def_Type([BasicTypeVariable([Any_Type()]), BasicTypeVariable([Int_Type()]), BasicTypeVariable([Int_Type()])],
                                                                    BasicTypeVariable([Int_Type()]),
                                                                    2)]),
                            # count(self, object: T) -> int
                            'count' : BasicTypeVariable([Def_Type([BasicTypeVariable([Any_Type()])],
                                                                    BasicTypeVariable([Int_Type()]),
                                                                    0)]),
                            # insert(self, index: int, object: T) -> None
                            'insert' : BasicTypeVariable([Def_Type([BasicTypeVariable([Int_Type()]), BasicTypeVariable([Any_Type()])],
                                                                    BasicTypeVariable([None_Type()]),
                                                                    0)]),
                            # remove(self, object: T) -> None
                            'remove' : BasicTypeVariable([Def_Type([BasicTypeVariable([Any_Type()])],
                                                                    BasicTypeVariable([None_Type()]),
                                                                    0)]),
                            # reverse(self) -> None
                            'remove' : BasicTypeVariable([Def_Type([],
                                                                    BasicTypeVariable([None_Type()]),
                                                                    0)]),
                            # sort(self, *, key: Function[[T], Any] = None, reverse: bool = False) -> None
                            'sort' : BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([None_Type()]),
                                                                    0,
                                                                    True)]),
                            
                            # __len__(self) -> int
                            '__len__': BasicTypeVariable([Def_Type([],
                                                                    BasicTypeVariable([Int_Type()]),
                                                                    0)]),                            
                            
                            # __iter__(self) -> Iterator[T]
                            '__iter__' : BasicTypeVariable([Def_Type([],
                                                                    BasicTypeVariable([Any_Type()]),
                                                                    0)]),
                            
                            # __str__(self) -> str
                   #         '__str__' : BasicTypeVariable([Def_Type([ ],
                    #                                                BasicTypeVariable([String_Type()]),
                    #                                                0)]),
                            
                           # __hash__(self) -> int
                           '__str__' : BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([Int_Type()]),
                                                                    0)]),
                            
                           # __getitem__(self, i: int) -> _T
                           # __getitem__(self, s: slice) -> List[_T]
                           '__getitem__': BasicTypeVariable([Def_Type([Any_Type()],
                                                                    BasicTypeVariable([Any_Type()]),
                                                                    0)]),
                            
                            # __setitem__(self, i: int, o: _T) -> None: pass
                            # __setitem__(self, s: slice, o: Sequence[_T]) -> None
                            '__setitem__': BasicTypeVariable([Def_Type([ Any_Type(), Any_Type() ],
                                                                    BasicTypeVariable([None_Type()]),
                                                                    0)]),
                            
                           # __delitem__(self, i: int) -> None
                           # __delitem__(self, s: slice) -> None
                           '__delitem__': BasicTypeVariable([Def_Type([ Any_Type() ],
                                                                    BasicTypeVariable([None_Type()]),
                                                                    0)]),
                            
                            # __add__(self, x: List[_T]) -> List[_T]
                            '__add__': BasicTypeVariable([Def_Type([ self ],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            
                            # __iadd__(self, x: Iterable[_T]) -> List[_T]
                            '__iadd__': BasicTypeVariable([Def_Type([ Any_Type() ],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            
                            # __contains__(self, o: object) -> bool
                            '__contains__': BasicTypeVariable([Def_Type([ Any_Type() ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                            
                            '__dict__' : BasicTypeVariable([Any_Type()]),

                            }
        
    def is_callable(self):
        ''' Can always initialise a class definition. '''
        return True
    
    def get_return_types(self):
        ''' We want to return a new instance every time. '''
      #  return BasicTypeVariable([self])
        # Need to copy as it is liable to change
        return BasicTypeVariable([self])
        
    def define_kind(self):
        self.kind = 'List(%s)' % repr(self.content_types)
        
class Generator_Type(Container_Type, Class_Base, BaseType):
    ''' TODO: Add new types when the function append is called or similar. '''
    def __init__(self):
        kind = 'List({})'
        Container_Type.__init__(self, None, [], set())
        Class_Base.__init__(self)
        BaseType.__init__(self, kind)
        
        self.global_vars = { # __init__(self, ?)
                            '__init__' : BasicTypeVariable([Def_Type([ Any_Type() ],
                                                                    BasicTypeVariable([None_Type()]),
                                                                    1)]),                          
                            
                            # __iter__(self) -> Iterator[T]
                            '__iter__' : BasicTypeVariable([Def_Type([],
                                                                    BasicTypeVariable([Any_Type()]),
                                                                    0)]),
                            
                            # __next__(self) -> any
                            '__next__' : BasicTypeVariable([Def_Type([],
                                                                    BasicTypeVariable([Any_Type()]),
                                                                    0)]),
                            
                            }
        
    def define_kind(self):
        self.kind = 'List(%s)' % repr(self.content_types)
    
    
class Tuple_Type(Container_Type, Class_Base, BaseType):
    def __init__(self):
        kind = 'Tuple({})'
        Container_Type.__init__(self, None, [], set())
        Class_Base.__init__(self)
        BaseType.__init__(self, kind)
        
        self.global_vars = {
                            
                            
                            # __getitem__(self, x: int) -> Any
                            '__getitem__' : BasicTypeVariable([Def_Type([Int_Type()],
                                                                    BasicTypeVariable([Any_Type()]),
                                                                    0)]),

                            # __len__(self) -> int
                            '__len__' : BasicTypeVariable([Def_Type([],
                                                                    BasicTypeVariable([Int_Type()]),
                                                                    0)]),
                            
                            # __contains__(self, x: object) -> bool
                            '__contains__' : BasicTypeVariable([Def_Type([ Any_Type() ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                            
                            # __getitem__(self, x: int) -> Any
                            # __getitem__(self, x: slice) -> tuple
                            '__getitem__' : BasicTypeVariable([Def_Type([ Any_Type() ],
                                                                    BasicTypeVariable([Any_Type()]),
                                                                    0)]),
                            
                            # __iter__(self) -> Iterator[T]
                            '__iter__' : BasicTypeVariable([Def_Type([],
                                                                    BasicTypeVariable([Any_Type()]),
                                                                    0)]),
                            
                            # __add__(self, x: tuple) -> tuple
                            '__add__' : BasicTypeVariable([Def_Type([self],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            
                            '__dict__' : BasicTypeVariable([Any_Type()]),

                            }
        
    def is_callable(self):
        ''' Can always initialise a class definition. '''
        return True
    
    def get_return_types(self):
        ''' We want to return a new instance every time. '''
      #  return BasicTypeVariable([self])
        # Need to copy as it is liable to change
        return BasicTypeVariable([self])
        
    def define_kind(self):
        self.kind = 'Tuple(%s)' % repr(self.content_types)

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
        
class String_Type(Container_Type, Class_Base, BaseType):
    def __init__(self):
        BaseType.__init__(self, 'String')
        Class_Base.__init__(self)
        self.content_types = set([self])
               
        self.global_vars = {  # capitalize(self) -> str
                            'capitalize' : BasicTypeVariable([Def_Type([],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            
                            # center(self, width: int, fillchar: str = ' ') -> str
                            'center' : BasicTypeVariable([Def_Type([BasicTypeVariable([Int_Type()]), BasicTypeVariable([self])],
                                                                    BasicTypeVariable([self]),
                                                                    1)]),
                            # count(self, x: str) -> int
                            'count' : BasicTypeVariable([Def_Type([BasicTypeVariable([self])],
                                                                    BasicTypeVariable([Int_Type()]),
                                                                    0)]),
                            
                            # encode(self, encoding: str = 'utf-8', errors: str = 'strict') -> bytes
                            'encode' : BasicTypeVariable([Def_Type([BasicTypeVariable([self]), BasicTypeVariable([self])],
                                                                    BasicTypeVariable([Bytes_Type()]),
                                                                    2)]),
                            
                            # endswith(self, suffix: str, start: int = 0, end: int = None) -> bool
                            'endswith': BasicTypeVariable([Def_Type([ BasicTypeVariable([self]), BasicTypeVariable([Int_Type()]), BasicTypeVariable([Int_Type()])],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    2)]),
                            
                            # expandtabs(self, tabsize: int = 8) -> str
                            'expandtabs': BasicTypeVariable([Def_Type([ BasicTypeVariable([Int_Type()])],
                                                                    BasicTypeVariable([self]),
                                                                    1)]),
                            
                            # find(self, sub: str, start: int = 0, end: int = 0) -> int:
                            'find': BasicTypeVariable([Def_Type([ BasicTypeVariable([self]), BasicTypeVariable([Int_Type()]), BasicTypeVariable([Int_Type()])],
                                                                    BasicTypeVariable([self]),
                                                                    2)]),
                            
                            # format(self, *args: Any, **kwargs: Any) -> str
                            'format': BasicTypeVariable([Def_Type([],
                                                                    BasicTypeVariable([self]),
                                                                    0,
                                                                    True)]),
                            
                            # format_map(self, map: Mapping[str, Any]) -> str
                            'format_map': BasicTypeVariable([Def_Type([ BasicTypeVariable([Any_Type()])],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            
                            # index(self, sub: str, start: int = 0, end: int = 0) -> int
                            'index': BasicTypeVariable([Def_Type([ BasicTypeVariable([self]), BasicTypeVariable([Int_Type()]), BasicTypeVariable([Int_Type()])],
                                                                    BasicTypeVariable([Int_Type()]),
                                                                    2)]),
                            
                            # isalnum(self) -> bool
                            'isalnum': BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                            
                            # isalpha(self) -> bool
                            'isalpha': BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                            
                            # isdecimal(self) -> bool
                            'isdecimal': BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                            
                            # isdigit(self) -> bool
                            'isdigit': BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                            
                            # isidentifier(self) -> bool
                            'isidentifier': BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                            
                            # islower(self) -> bool
                            'islower': BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                            
                            # isnumeric(self) -> bool
                            'isnumeric': BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                            
                            # isprintable(self) -> bool
                            'isprintable': BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                            
                            # isspace(self) -> bool
                            'isspace': BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                            
                            # istitle(self) -> bool
                            'istitle': BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                            
                            # isupper(self) -> bool
                            'isupper': BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                      
                            #  join(self, iterable: Iterable[str]) -> str:
                            'join': BasicTypeVariable([Def_Type([BasicTypeVariable([Any_Type()])],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            
                            # ljust(self, width: int, fillchar: str = ' ') -> str
                            'ljust': BasicTypeVariable([Def_Type([  BasicTypeVariable([Int_Type()]),   BasicTypeVariable([self])],
                                                                    BasicTypeVariable([self]),
                                                                    1)]),
                            
                            # lower(self) -> str
                            'lower': BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            
                            # lstrip(self, chars: str = None) -> str
                            'lstrip': BasicTypeVariable([Def_Type([ BasicTypeVariable([self]) ],
                                                                    BasicTypeVariable([self]),
                                                                    1)]),
                            
                            # partition(self, sep: str) -> Tuple[str, str, str]
                            'lstrip': BasicTypeVariable([Def_Type([ BasicTypeVariable([self]) ],
                                                                    BasicTypeVariable([Tuple_Type()]),
                                                                    0)]),
                            
                            # replace(self, old: str, new: str, count: int = -1) -> str
                            'replace': BasicTypeVariable([Def_Type([BasicTypeVariable([self]), BasicTypeVariable([self]), BasicTypeVariable([Int_Type()])],
                                                                    BasicTypeVariable([self]),
                                                                    1)]),
                            
                            # rfind(self, sub: str, start: int = 0, end: int = 0) -> int
                            'rfind': BasicTypeVariable([Def_Type([BasicTypeVariable([self]), BasicTypeVariable([Int_Type()]), BasicTypeVariable([Int_Type()])],
                                                                    BasicTypeVariable([Int_Type()]),
                                                                    2)]),
                            
                            # rindex(self, sub: str, start: int = 0, end: int = 0) -> int
                            'rindex': BasicTypeVariable([Def_Type([BasicTypeVariable([self]), BasicTypeVariable([Int_Type()]), BasicTypeVariable([Int_Type()])],
                                                                    BasicTypeVariable([Int_Type()]),
                                                                    2)]),         
                            
                            # rjust(self, width: int, fillchar: str = ' ') -> str
                            'rindex': BasicTypeVariable([Def_Type([  BasicTypeVariable([Int_Type()]),  BasicTypeVariable([self])  ],
                                                                    BasicTypeVariable([self]),
                                                                    1)]),                  
                            
                            # rpartition(self, sep: str) -> Tuple[str, str, str]
                            'rpartition': BasicTypeVariable([Def_Type([  BasicTypeVariable([self])  ],
                                                                    BasicTypeVariable([Tuple_Type()]),
                                                                    0)]),   
                            
                            # rsplit(self, sep: str = None, maxsplit: int = -1) -> List[str]
                            'rsplit': BasicTypeVariable([Def_Type([  BasicTypeVariable([self]), BasicTypeVariable([Int_Type()]) ],
                                                                    BasicTypeVariable([List_Type()]),
                                                                    2)]),   
                            
                            # rstrip(self, chars: str = None) -> str
                            'rstrip': BasicTypeVariable([Def_Type([  BasicTypeVariable([self])  ],
                                                                    BasicTypeVariable([self]),
                                                                    1)]),  
                            
                            # split(self, sep: str = None, maxsplit: int = -1) -> List[str]
                            'split': BasicTypeVariable([Def_Type([BasicTypeVariable([self]), BasicTypeVariable([Int_Type()])],
                                                                    BasicTypeVariable([List_Type()]),
                                                                    2)]),
                            
                            # splitlines(self, keepends: bool = False) -> List[str]
                            'splitlines': BasicTypeVariable([Def_Type([  BasicTypeVariable([Bool_Type()])  ],
                                                                    BasicTypeVariable([List_Type()]),
                                                                    1)]),
                            
                            # startswith(self, prefix: str, start: int = 0, end: int = None) -> bool
                            'startswith': BasicTypeVariable([Def_Type([  BasicTypeVariable([self]), BasicTypeVariable([Int_Type()]), BasicTypeVariable([Int_Type()])  ],
                                                                    BasicTypeVariable([ Bool_Type() ]),
                                                                    2)]),
                            
                            # strip(self, chars: str = None) -> str
                            'strip': BasicTypeVariable([Def_Type([  BasicTypeVariable([self])  ],
                                                                    BasicTypeVariable([self]),
                                                                    1)]),  
                            
                            # swapcase(self) -> str
                            'swapcase': BasicTypeVariable([Def_Type([  ],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            
                            # title(self) -> str
                            'title': BasicTypeVariable([Def_Type([  ],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),  
                            
                            # translate(self, table: Dict[int, Any]) -> str
                            'translate': BasicTypeVariable([Def_Type([ BasicTypeVariable([Dict_Type()]) ],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),  
                            
                            # upper(self) -> str
                            'upper': BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            
                            # zfill(self, width: int) -> str
                            'zfill': BasicTypeVariable([Def_Type([  BasicTypeVariable([Int_Type()]) ],
                                                                    BasicTypeVariable([self]),
                                                                    0)]), 
                                        
                            # __getitem__(self, i: Union[int, slice]) -> str
                            '__getitem__' : BasicTypeVariable([Def_Type([Any_Type()],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            
                            # __add__(self, s: str) -> str
                            '__add__' : BasicTypeVariable([Def_Type([self],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            
                            # __len__(self) -> int
                            '__len__' : BasicTypeVariable([Def_Type([ ],
                                                                    BasicTypeVariable([Int_Type()]),
                                                                    0)]),
                            
                            # __contains__(self, s: object) -> bool
                            '__contains__' : BasicTypeVariable([Def_Type([ Any_Type() ],
                                                                    BasicTypeVariable([Bool_Type()]),
                                                                    0)]),
                            
                            # __iter__(self) -> Iterator[str]
                            '__iter__' : BasicTypeVariable([Def_Type([],
                                                                    BasicTypeVariable([Any_Type()]),
                                                                    0)]),
                            
                            # __str__(self) -> str
                            '__str__' : BasicTypeVariable([Def_Type([],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            
                            # __repr__(self) -> str
                            '__repr__' : BasicTypeVariable([Def_Type([],
                                                                    BasicTypeVariable([self]),
                                                                    0)]),
                            
                            # __int__(self) -> int
                            '__int__' : BasicTypeVariable([Def_Type([],
                                                                    BasicTypeVariable([Int_Type()]),
                                                                    0)]),
                            
                            # __float__(self) -> float
                            '__float__' : BasicTypeVariable([Def_Type([],
                                                                    BasicTypeVariable([Float_Type()]),
                                                                    0)]),
                            
                            # __hash__(self) -> int
                            '__hash__' : BasicTypeVariable([Def_Type([],
                                                                    BasicTypeVariable([Int_Type()]),
                                                                    0)]),
                            
                            
                            '__dict__' : BasicTypeVariable([Any_Type()]),
                            
                            

                            }

    def get_content_types(self):
        return self.content_types
        
    def update_content_types(self, new_types):
        return
    
    def is_callable(self):
        ''' Can always initialise a class definition. '''
        return True
    
    def get_return_types(self):
        ''' We want to return a new instance every time. '''
      #  return BasicTypeVariable([self])
        # Need to copy as it is liable to change
        return BasicTypeVariable([self])
    
    def define_kind(self):
        self.kind = 'String'
        
        
# Create singleton instances of simple types.

BUILTIN_TYPE_DICT = {
  # builtin double underscores
  '__version__' : BasicTypeVariable([Any_Type()]),
  '__loader__': BasicTypeVariable([Any_Type()]),
  '__package__':BasicTypeVariable([Any_Type()]),
  '__builtins__': BasicTypeVariable([Any_Type()]),
  '__name__': BasicTypeVariable([Any_Type()]),
  '__main__': BasicTypeVariable([Any_Type()]),
  '__doc__': BasicTypeVariable([Any_Type()]),
  '__file__': BasicTypeVariable([Any_Type()]),
  
  # __import__(name: str, globals: Dict[str, Any] = {}, locals: Dict[str, Any] = {}, fromlist: List[str] = [], level: int = -1) -> Any
  '__import__': BasicTypeVariable([Def_Type([  BasicTypeVariable([  String_Type(), Dict_Type(), Dict_Type(), List_Type(), Int_Type()])  ],
                                  BasicTypeVariable([Any_Type()]),
                                  5)]),
                     
  # keywords
  'True': BasicTypeVariable([Bool_Type()]),
  
  'False': BasicTypeVariable([Bool_Type()]),
  
  'None': BasicTypeVariable([None_Type()]),
  # Bit of a hack
  '_' : BasicTypeVariable([Any_Type()]),
  
  # Exceptions/Errors
  'BaseException' : BasicTypeVariable([Any_Type()]),
  'Exception' : BasicTypeVariable([Any_Type()]),
  'KeyError' : BasicTypeVariable([Any_Type()]),
  'AttributeError' : BasicTypeVariable([Any_Type()]),
  'ZeroDivisionError' : BasicTypeVariable([Any_Type()]),
  'NameError' : BasicTypeVariable([Any_Type()]),
  'TypeError' : BasicTypeVariable([Any_Type()]),
  'ValueError' : BasicTypeVariable([Any_Type()]),
  'RuntimeError' : BasicTypeVariable([Any_Type()]),
  'IOError' : BasicTypeVariable([Any_Type()]),
  'KeyboardInterrupt' : BasicTypeVariable([Any_Type()]),
  'OSError' : BasicTypeVariable([Any_Type()]),
  'StandardError' : BasicTypeVariable([Any_Type()]),
  'ArithmeticError' : BasicTypeVariable([Any_Type()]),
  'BufferError' : BasicTypeVariable([Any_Type()]),
  'LookupError' : BasicTypeVariable([Any_Type()]),
  'EnvironmentError' : BasicTypeVariable([Any_Type()]),
  'AssertionError' : BasicTypeVariable([Any_Type()]),
  'EOFError' : BasicTypeVariable([Any_Type()]),
  'FloatingPointError' : BasicTypeVariable([Any_Type()]),
  'GeneratorExit' : BasicTypeVariable([Any_Type()]),
  'ImportError' : BasicTypeVariable([Any_Type()]),
  'IndexError' : BasicTypeVariable([Any_Type()]),
  'MemoryError' : BasicTypeVariable([Any_Type()]),
  'NotImplementedError' : BasicTypeVariable([Any_Type()]),
  'OverflowError' : BasicTypeVariable([Any_Type()]),
  'ReferenceError' : BasicTypeVariable([Any_Type()]),
  'StopIteration' : BasicTypeVariable([Any_Type()]),
  'SyntaxError' : BasicTypeVariable([Any_Type()]),
  'IndentationError' : BasicTypeVariable([Any_Type()]),
  'TabError' : BasicTypeVariable([Any_Type()]),
  'SystemError' : BasicTypeVariable([Any_Type()]),
  'SystemExit' : BasicTypeVariable([Any_Type()]),
  'UnboundLocalError' : BasicTypeVariable([Any_Type()]),
  'UnicodeError' : BasicTypeVariable([Any_Type()]),
  'UnicodeEncodeError' : BasicTypeVariable([Any_Type()]),
  'UnicodeDecodeError' : BasicTypeVariable([Any_Type()]),
  'UnicodeTranslateError' : BasicTypeVariable([Any_Type()]),
  'BlockingIOError' : BasicTypeVariable([Any_Type()]),
  'ChildProcessError' : BasicTypeVariable([Any_Type()]),
  'ConnectionError' : BasicTypeVariable([Any_Type()]),
  'BrokenPipeError' : BasicTypeVariable([Any_Type()]),
  'ConnectionAbortedError' : BasicTypeVariable([Any_Type()]),
  'ConnectionRefusedError' : BasicTypeVariable([Any_Type()]),
  'ConnectionResetError' : BasicTypeVariable([Any_Type()]),
  'FileExistsError' : BasicTypeVariable([Any_Type()]),
  'FileNotFoundError' : BasicTypeVariable([Any_Type()]),
  'InterruptedError' : BasicTypeVariable([Any_Type()]),
  'IsADirectoryError' : BasicTypeVariable([Any_Type()]),
  'NotADirectoryError' : BasicTypeVariable([Any_Type()]),
  'PermissionError' : BasicTypeVariable([Any_Type()]),
  'ProcessLookupError' : BasicTypeVariable([Any_Type()]),
  'TimeoutError' : BasicTypeVariable([Any_Type()]),
  
  # Warnings
  
  'Warning' : BasicTypeVariable([Any_Type()]),
  'UserWarning' : BasicTypeVariable([Any_Type()]),
  'DeprecationWarning' : BasicTypeVariable([Any_Type()]),
  'PendingDeprecationWarning' : BasicTypeVariable([Any_Type()]),
  'SyntaxWarning' : BasicTypeVariable([Any_Type()]),
  'RuntimeWarning' : BasicTypeVariable([Any_Type()]),
  'FutureWarning' : BasicTypeVariable([Any_Type()]),
  'ImportWarning' : BasicTypeVariable([Any_Type()]),
  'UnicodeWarning' : BasicTypeVariable([Any_Type()]),
  'BytesWarning' : BasicTypeVariable([Any_Type()]),
  'ResourceWarning' : BasicTypeVariable([Any_Type()]),
  
  
  # Functions
  
  # abs(n: int) -> int
  # abs(n: float) -> float
  # abs(n: SupportsAbs[T]) -> T
  'abs': BasicTypeVariable([Def_Type([  BasicTypeVariable([Int_Type(), Float_Type()])  ],
                                  BasicTypeVariable([Int_Type(), Float_Type()]),
                                  0)]),
                     
  # all(i: Iterable) -> bool
  'all': BasicTypeVariable([Def_Type([  BasicTypeVariable([Any_Type()])  ],
                                  BasicTypeVariable([Bool_Type()]),
                                  0)]),
                     
  # any(i: Iterable) -> bool
  'any': BasicTypeVariable([Def_Type([  BasicTypeVariable([Any_Type()])  ],
                                  BasicTypeVariable([Bool_Type()]),
                                  0)]),
                     
  # ascii(o: object) -> str
  'ascii': BasicTypeVariable([Def_Type([  BasicTypeVariable([Any_Type()])  ],
                                  BasicTypeVariable([String_Type()]),
                                  0)]),
                     
  # callable(o: object) -> bool
  'callable': BasicTypeVariable([Def_Type([  BasicTypeVariable([Any_Type()])  ],
                                  BasicTypeVariable([String_Type()]),
                                  0)]),

  # chr(code: int) -> str
  'chr':  BasicTypeVariable([Def_Type([BasicTypeVariable([Int_Type()])],
                                  BasicTypeVariable([String_Type()]),
                                  0)]),
                     
  # delattr(o: Any, name: str) -> None
  'delattr':  BasicTypeVariable([Def_Type([  BasicTypeVariable([Int_Type()]), BasicTypeVariable([String_Type()])  ],
                                  BasicTypeVariable([None_Type()]),
                                  0)]),
                     
  # dir(o: object = None) -> List[str]
  'dir':  BasicTypeVariable([Def_Type([  BasicTypeVariable([Any_Type()])  ],
                                  BasicTypeVariable([List_Type()]),
                                  1)]),
                     
  'enumerate' : BasicTypeVariable([Any_Type()]),
  
  'exit' : BasicTypeVariable([Any_Type()]),
                     
  # divmod(a: _N, b: _N) -> Tuple[_N, _N]
  'divmod':  BasicTypeVariable([Def_Type([  BasicTypeVariable([Any_Type()]), BasicTypeVariable([Any_Type()])  ],
                                  BasicTypeVariable([Tuple_Type()]),
                                  1)]),
                     
  # eval(source: str, globals: Dict[str, Any] = None, locals: Mapping[str, Any] = None) -> Any  
  'eval': BasicTypeVariable([Def_Type([  BasicTypeVariable([String_Type()]), BasicTypeVariable([Dict_Type()]), BasicTypeVariable([Any_Type()])  ],
                                  BasicTypeVariable([Any_Type()]),
                                  2)]),
                     
  # filter(function: Function[[T], Any], iterable: Iterable[T]) -> Iterator[T]
  'filter': BasicTypeVariable([Def_Type([  BasicTypeVariable([Any_Type()]), BasicTypeVariable([Any_Type()]) ],
                                  BasicTypeVariable([Any_Type()]),
                                  0)]),
                     
  # format(o: object, format_spec: str = '') -> str
  'format': BasicTypeVariable([Def_Type([  BasicTypeVariable([Any_Type()]), BasicTypeVariable([String_Type()]) ],
                                  BasicTypeVariable([String_Type()]),
                                  1)]),
                     
  # getattr(o: Any, name: str, default: Any = None) -> Any
  'getattr' : BasicTypeVariable([Def_Type([BasicTypeVariable([Any_Type()]), BasicTypeVariable([String_Type()]), BasicTypeVariable([Any_Type()])],
                                  BasicTypeVariable([Any_Type()]),
                                  1)]),
                     
  # globals() -> Dict[str, Any]
  'globals' : BasicTypeVariable([Def_Type([ ],
                                  BasicTypeVariable([Dict_Type()]),
                                  0)]),
                     
  # hasattr(o: Any, name: str) -> bool
  'hasattr' : BasicTypeVariable([Def_Type([ BasicTypeVariable([Any_Type()]), BasicTypeVariable([String_Type()]) ],
                                  BasicTypeVariable([Bool_Type()]),
                                  0)]),                  
                     
  # hash(o: object) -> int
  'hash' : BasicTypeVariable([Def_Type([ BasicTypeVariable([Any_Type()]) ],
                                  BasicTypeVariable([Int_Type()]),
                                  0)]),        
                     
  # hex(i: int) -> str
  'hex' : BasicTypeVariable([Def_Type([ BasicTypeVariable([Int_Type()]) ],
                                  BasicTypeVariable([String_Type()]),
                                  0)]),
          
  # id(o: object) -> int           
  'id':   BasicTypeVariable([Def_Type([BasicTypeVariable([Any_Type()])],
                                  BasicTypeVariable([Int_Type()]),
                                  0)]),
                     
  # input(prompt: str = None) -> str
  'input': BasicTypeVariable([Def_Type([BasicTypeVariable([String_Type()])],
                                  BasicTypeVariable([String_Type()]),
                                  1)]),
                     
  # iter(iterable: Iterable[T]) -> Iterator[T]: pass
  # iter(function: Function[[], T], sentinel: T) -> Iterator[T]
  'iter': BasicTypeVariable([Def_Type([ BasicTypeVariable([Any_Type()]), BasicTypeVariable([Any_Type()])],
                                  BasicTypeVariable([Any_Type()]),
                                  1)]),
  
  # isinstance(o: object, t: Union[type, tuple]) -> bool
  'isinstance': BasicTypeVariable([Def_Type([BasicTypeVariable([Any_Type()]), BasicTypeVariable([Any_Type()])],
                                  BasicTypeVariable([Bool_Type()]),
                                  0)]),  
                     
  # issubclass(cls: type, classinfo: type) -> bool
  'issubclass': BasicTypeVariable([Def_Type([BasicTypeVariable([Any_Type()]), BasicTypeVariable([Any_Type()])],
                                  BasicTypeVariable([Bool_Type()]),
                                  0)]), 
                   
  # len(o: Sized) -> int
  # len(o: tuple) -> int  
  'len':  BasicTypeVariable([Def_Type([BasicTypeVariable([Any_Type()])],
                                  BasicTypeVariable([Int_Type()]),
                                  0)]),
                     
  # locals() -> Dict[str, Any]
  'locals':  BasicTypeVariable([Def_Type([ ],
                                  BasicTypeVariable([Dict_Type()]),
                                  0)]),
                     
  # map(func: Function[[T1], S], iter1: Iterable[T1]) -> Iterator[S]
  # map(func: Function[[T1, T2], S], iter1: Iterable[T1], iter2: Iterable[T2]) -> Iterator[S]
  'map' : BasicTypeVariable([Def_Type([BasicTypeVariable([Any_Type()]), BasicTypeVariable([Any_Type()]), BasicTypeVariable([Any_Type()])],
                                  BasicTypeVariable([Any_Type()]),
                                  1)]),
                     
  # max(iterable: Iterable[T]) -> T
  # max(arg1: T, arg2: T, *args: T) -> T
  'max' : BasicTypeVariable([Def_Type([BasicTypeVariable([Any_Type()]), BasicTypeVariable([Any_Type()])],
                                  BasicTypeVariable([Any_Type()]),
                                  0,
                                  True)]),
               
  # min(iterable: Iterable[T]) -> T: pass
  # min(arg1: T, arg2: T, *args: T) -> T      
  'min' : BasicTypeVariable([Def_Type([BasicTypeVariable([Any_Type()]), BasicTypeVariable([Any_Type()])],
                                  BasicTypeVariable([Any_Type()]),
                                  0,
                                  True)]),
                     
  # next(i: Iterator[T]) -> T
  # nexxt(i: Iterator[T], default: T) -> T
  'next': BasicTypeVariable([Def_Type([  BasicTypeVariable([Any_Type()]), BasicTypeVariable([Any_Type()]) ],
                                  BasicTypeVariable([ Any_Type() ]),
                                  1)]),   
                     
  # oct(i: int) -> str
  'oct': BasicTypeVariable([Def_Type([BasicTypeVariable([Int_Type()])],
                                  BasicTypeVariable([ String_Type() ]),
                                  0)]),      
   
  # open(file: Union[str, bytes, int], mode: str = 'r', buffering: int = -1, encoding: str = None, errors: str = None, newline: str = None, closefd: bool = True) -> IO[Any]
  'open': BasicTypeVariable([Def_Type([BasicTypeVariable([String_Type()]), BasicTypeVariable([String_Type()]), BasicTypeVariable([Int_Type()]), BasicTypeVariable([String_Type()]), BasicTypeVariable([String_Type()]), BasicTypeVariable([String_Type()]), BasicTypeVariable([Bool_Type()]), BasicTypeVariable([Any_Type()])],
                                  BasicTypeVariable([Any_Type()]),
                                  7)]),
                     
  # ord(c: Union[str, bytes, bytearray]) -> int
  'ord':  BasicTypeVariable([Def_Type([BasicTypeVariable([String_Type(), Bytes_Type()])],
                                  BasicTypeVariable([Int_Type()]),
                                  0)]),
                     
  # print(*values: Any, sep: str = ' ', end: str = '\n', file: IO[str] = None) -> None
  'print': BasicTypeVariable([Def_Type([BasicTypeVariable([Any_Type()])],
                                  BasicTypeVariable([None_Type()]),
                                  0,
                                  True)]),
                     
  # pow(x: int, y: int) -> Any
  # pow(x: int, y: int, z: int) -> Any
  # pow(x: float, y: float) -> float
  # pow(x: float, y: float, z: float) -> float
  'pow' : BasicTypeVariable([Def_Type([BasicTypeVariable([Int_Type(), Float_Type()]), BasicTypeVariable([Int_Type(), Float_Type()]), BasicTypeVariable([Float_Type()])],
                                  BasicTypeVariable([Any_Type()]),
                                  1)]),
        
  # reversed(object: Reversible[T]) -> Iterator[T]: pass
  # reversed(object: Sequence[T]) -> Iterator[T]             
  'reversed': BasicTypeVariable([Def_Type([BasicTypeVariable([Any_Type()])],
                                  BasicTypeVariable([Any_Type()]),
                                  0)]),
                     
  # repr(o: object) -> str
  'repr' : BasicTypeVariable([Def_Type([BasicTypeVariable([Any_Type()])],
                                  BasicTypeVariable([ String_Type() ]),
                                  0)]),
        
  # round(number: float) -> int
  # round(number: float, ndigits: int) -> float
  # round(number: SupportsRound[T]) -> T
  # round(number: SupportsRound[T], ndigits: int) -> T
  'round': BasicTypeVariable([Def_Type([  BasicTypeVariable([Any_Type()]) ],
                                  BasicTypeVariable([Any_Type()]),
                                  0)]),
                     
  # setattr(object: Any, name: str, value: Any) -> None
  'setattr': BasicTypeVariable([Def_Type([  BasicTypeVariable([Any_Type()]), BasicTypeVariable([String_Type()]), BasicTypeVariable([Any_Type()]) ],
                                  BasicTypeVariable([None_Type()]),
                                  0)]),
            
  # sorted(iterable: Iterable[T], *, key: Function[[T], Any] = None, reverse: bool = False) -> List[T]         
  'sorted': BasicTypeVariable([Def_Type([BasicTypeVariable([List_Type()]), BasicTypeVariable([Any_Type()]), BasicTypeVariable([Bool_Type()])],
                                  BasicTypeVariable([List_Type()]),
                                  2,
                                  True)]),
                     
  # sum(iterable: Iterable[T], start: T = None) -> T
  'sum' : BasicTypeVariable([Def_Type([BasicTypeVariable([Any_Type()]), BasicTypeVariable([Any_Type()])],
                                  BasicTypeVariable([Any_Type()]),
                                  1)]),
                     
  'super' : BasicTypeVariable([Def_Type([BasicTypeVariable([Any_Type()]), BasicTypeVariable([Any_Type()])],
                                  BasicTypeVariable([Any_Type()]),
                                  2)]),
                     
  'type' : BasicTypeVariable([Def_Type([BasicTypeVariable([Any_Type()]), BasicTypeVariable([Any_Type()]), BasicTypeVariable([Dict_Type()])],
                                  BasicTypeVariable([Any_Type()]),
                                  2)]),
                     
  'vars':  BasicTypeVariable([Def_Type([ BasicTypeVariable([Any_Type()]) ],
                                  BasicTypeVariable([Dict_Type()]),
                                  1)]),
      
  # zip(iter1: Iterable[T1]) -> Iterator[Tuple[T1]]
  # zip(iter1: Iterable[T1], iter2: Iterable[T2]) -> Iterator[Tuple[T1, T2]]
  # zip(iter1: Iterable[T1], iter2: Iterable[T2], iter3: Iterable[T3]) -> Iterator[Tuple[T1, T2, T3]]
  # zip(iter1: Iterable[T1], iter2: Iterable[T2], iter3: Iterable[T3], iter4: Iterable[T4]) -> Iterator[Tuple[T1, T2, T3, T4]]               
  'zip': BasicTypeVariable([Def_Type([BasicTypeVariable([Any_Type()]), BasicTypeVariable([Any_Type()]), BasicTypeVariable([Any_Type()]), BasicTypeVariable([Any_Type()])],
                                  BasicTypeVariable([Any_Type()]),
                                  3)]),
                     
  'int': BasicTypeVariable([Def_Type([BasicTypeVariable([String_Type(), Int_Type(), Float_Type(), Bytes_Type()]), BasicTypeVariable([Int_Type()])],
                                  BasicTypeVariable([Int_Type()]),
                                  2)]),
                     
  'float': BasicTypeVariable([Def_Type([BasicTypeVariable(  [String_Type(), Int_Type(), Float_Type(), Bytes_Type()]) ],
                                  BasicTypeVariable([Float_Type()]),
                                  1)]),
                     
  'tuple': BasicTypeVariable([Def_Type([BasicTypeVariable(  [Any_Type()]) ],
                                  BasicTypeVariable([Tuple_Type()]),
                                  1)]),
                     
  'str':  BasicTypeVariable([Def_Type([BasicTypeVariable([Any_Type()]), BasicTypeVariable([String_Type()]), BasicTypeVariable([String_Type()])],
                                  BasicTypeVariable([String_Type()]),
                                  2)]),            
                     
  'range':  BasicTypeVariable([Def_Type([BasicTypeVariable([Int_Type()]), BasicTypeVariable([Int_Type()]), BasicTypeVariable([Int_Type()])],
                                    BasicTypeVariable([ List_Type() ]),
                                    2)]),
                     
  'list':  BasicTypeVariable([ List_Type() ]),    
                     
            # Should this be a function or class?
  'set': BasicTypeVariable([ Set_Type() ]),
                     
  'dict': BasicTypeVariable([ Dict_Type() ]),
                     
  'bytes' : BasicTypeVariable([ Bytes_Type() ]),
  # TODO: Support this
  'bytearray' : BasicTypeVariable([ Any_Type() ]),
  'bool' : BasicTypeVariable([ Bool_Type() ] ),
            # Classes
  'object' : BasicTypeVariable([Class_Type("object", {}, False)])
} 


ITERATOR_TYPES = BasicTypeVariable([List_Type(), Set_Type(), Tuple_Type(), Dict_Type(), String_Type(), Bytes_Type()])

SLICE_TYPES = [List_Type(), String_Type()]
INDEX_TYPES = [List_Type(), Dict_Type(), String_Type()]
ALL_TYPES = [List_Type(), Dict_Type(), Int_Type(), Float_Type(), Bool_Type(), String_Type(), Bytes_Type()]