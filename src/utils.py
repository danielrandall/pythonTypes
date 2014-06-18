import ast
from src.generators import *
class Utils:
    
    '''A class containing utility methods and pre-defined objects.
    
    This is a lightweight class; it may be instantiated freely.
    
    Important: this class no longer contains application globals.
    '''

    #@+others
    #@+node:ekr.20121114043443.4006: *3*  u.ctor
    def __init__ (self):
        
        # Unit tests should create new App instances to ensure these get inited properly.

        # Used by modified pyflackes code.
            # self.attrs_def_dict = {} # Keys formatted expressions, values lists of attributes.
            # self.attrs_ref_dict = {} # Ditto.

        # These ivars allow tracing code to be independent of Leo.
        # if use_leo_globals:
            # self.runningAllUnitTests = g.app.runningAllUnitTests
            # # self.enable_trace = not g.app.runningAllUnitTests
        # else:
            # self.runningAllUnitTests = False
            # # self.enable_trace = True

        # Set by u.format().
        self.formatter_instance = None
        self.pattern_formatter_instance = None
        
        # Set by u.all_statement/node/statement_generator()
        self.all_statement_generator_instance = None
        self.local_node_generator_instance = None
        self.node_generator_instance = None 
        self.statement_generator_instance = None
    #@+node:ekr.20130318180500.9630: *3*  u.generators
    #@+node:ekr.20140319074626.5387: *4* u.all_nodes and u.local_nodes
    def all_nodes(self,node):
        u = self
        if not u.node_generator_instance:
            u.node_generator_instance = NodeGenerator()
        return u.node_generator_instance.run(node)
        
    def local_nodes(self,node):
        u = self
        if not u.local_node_generator_instance:
            u.local_node_generator_instance = LocalNodeGenerator()
        return u.local_node_generator_instance.run(node)
    #@+node:ekr.20140319074626.5388: *4* u.all_statements and u.local_statements
    def all_statements(self,context_node):
        '''Yield *all* statements of a context node.'''
        # This is used only by the context generator.
        u = self
        if not u.all_statement_generator_instance:
            u.all_statement_generator_instance = AllStatementsPseudoGenerator()
        return u.all_statement_generator_instance.run(context_node)
        
    def local_statements(self,context_node):
        '''Yield all  local statements of a context node.'''
        u = self
        if not u.statement_generator_instance:
            u.statement_generator_instance = LocalStatementGenerator()
        return u.statement_generator_instance.run(context_node)
    #@+node:ekr.20130318180500.9633: *4* u.assignments
    def assignments(self,statement):
        
        '''A generator returning all assignment nodes in statement's tree.'''
        
        for statement2 in self.local_statements(statement):
            if isinstance(statement2,(ast.Assign,ast.AugAssign)):
                yield statement2
    #@+node:ekr.20130322073758.9553: *4* u.assignments_to
    def assignments_to (self,cx,target_name):

        u = self
        result = []
        for statement in u.assignments(cx):
            if isinstance(statement,ast.Assign):
                #  Assign(expr* targets, expr value)
                for target in statement.targets:
                    s = u.format(target)
                    kind2 = u.kind(target)
                    if kind2 == 'Name':
                        if target_name == target.id:
                            result.append(statement)
                    elif kind2 == 'Tuple':
                        # Tuple(expr* elts, expr_context ctx)
                        for item2 in target.elts:
                            if u.kind(item2) == 'Name' and target_name == item2.id:
                                result.append(statement)
            elif isinstance(statement,ast.AugAssign):
                if u.kind(statement.target) == 'Name' and target_name == statement.target.id:
                    result.append(statement)
            else:
                # The assignments generator returns only Assign and AugAssign nodes.
                assert False,kind
        # if result: # g.trace(target_name,','.join([u.format(z) for z in result]))
        return result
    #@+node:ekr.20130318180500.9634: *4* u.attributes
    def attributes(self,node):
        
        '''A generator returning all ast.Attribute nodes in node's tree.'''
        
        for node2 in self.local_nodes(node):
            if isinstance(node2,ast.Attribute):
                yield node2
    #@+node:ekr.20130318180500.9635: *4* u.calls
    def calls(self,statement):

        '''A generator returning all ast.Call nodes in statement's tree.'''
        
        for statement2 in self.local_statements(statement):
            if isinstance(statement2,ast.Call):
                yield statement2
    #@+node:ekr.20130318180500.9636: *4* u.contexts
    def contexts(self,statement):
        '''
        A generator returning all ast.Module,ast.ClassDef,ast.FunctionDef
        and ast.Lambda nodes in statement's tree.
        '''
        assert isinstance(statement,ast.Module),repr(statement)
        yield statement
        for statement2 in self.all_statements(statement):
            if isinstance(statement2,(ast.ClassDef,ast.FunctionDef,ast.Lambda,ast.Module)):
                yield statement2
    #@+node:ekr.20130403041858.5530: *4* u.definitions_of
    # FunctionDef(identifier name, arguments args, stmt* body, expr* decorator_list)
    # arguments (expr* args, identifier? vararg, identifier? kwarg, expr* defaults)

    def definitions_of (self,cx,target_name):

        u = self
        result = []

        # Look for defintions in the context node itself.
        if isinstance(cx,ast.FunctionDef):
            if cx.name == target_name:
                result.append(cx)
            assert isinstance(cx.args,ast.arguments)
            assert isinstance(cx.args.args,(list))
            args = cx.args
            for arg in args.args:
                if hasattr(arg,'id') and arg.id == target_name:
                    result.append(cx)
            if args.vararg and args.vararg == target_name:
                result.append(cx)
            if args.kwarg and args.kwarg == target_name:
                result.append(cx)
        elif isinstance(cx,ast.ClassDef):
            if cx.name == target_name:
                result.append(cx)
                
        # Search all the local nodes.
        for node in u.local_nodes(cx):
            kind = u.kind(node)
            if kind == 'Assign':
                #  Assign(expr* targets, expr value)
                for target in node.targets:
                    s = u.format(target)
                    kind2 = u.kind(target)
                    if kind2 == 'Name':
                        if target_name == target.id:
                            result.append(node)
                    elif kind2 == 'Tuple':
                        # Tuple(expr* elts, expr_context ctx)
                        for item2 in target.elts:
                            if u.kind(item2) == 'Name' and target_name == item2.id:
                                result.append(node)
            elif kind == 'AugAssign':
                if u.kind(node.target) == 'Name' and target_name == node.target.id:
                    result.append(node)
            elif kind == 'For':
                s = u.format(node)
                assert s.startswith('for ')
                i = s.find(' in ')
                assert i > -1
                s2 = s[4:i].strip('()')
                aList = s2.split(',')
                for z in aList:
                    if z.strip() == target_name:
                        result.append(node)
            elif kind == 'ListComp':
                # node.generators is a comprehension.
                for item in node.generators:
                    target = item.target
                    kind2 = u.kind(target)
                    if kind2 == 'Name':
                        if target_name == target.id:
                            result.append(node)
                            break
                    elif kind2 == 'Tuple':
                        for item2 in target.elts:
                            if u.kind(item2) == 'Name' and target_name == item2.id:
                                result.append(node)
                                break
                    else:
                        assert False,kind2
            else:
                pass
                # assert False,kind
        result = list(set(result))
        # if result: g.trace('%20s: %s' % (target_name,','.join([u.format(z) for z in result])))
        return result
    #@+node:ekr.20130318180500.9637: *4* u.defs
    def defs(self,statement):
        '''A generator returning all ast.FunctionDef nodes in statement's tree.'''
        for statement2 in self.local_statements(statement):
            if isinstance(statement2,ast.FunctionDef):
                yield statement2
    #@+node:ekr.20130403041858.5536: *4* u.imports
    def imports(self,statement):
        
        '''A generator returning all import statements in node's tree.'''
        
        for statement2 in self.local_statements(statement):
            if isinstance(statement2,(ast.Import,ast.ImportFrom)):
                yield statement2
    #@+node:ekr.20130318180500.9640: *4* u.returns
    def returns(self,statement):
        
        '''A generator returning all ast.Return nodes in node's tree.'''

        for statement2 in self.local_statements(statement):
            if isinstance(statement2,ast.Return):
                yield statement2
    #@+node:ekr.20121022121729.4041: *3* u.clean_project_name
    def clean_project_name(self,s):
        
        i = s.find(' ')
        if i > -1:
            s = s[:i].strip()

        return s.replace('(','').replace(')','').replace(' ','_').strip()
    #@+node:ekr.20130317112835.9349: *3* u.collect
    def collect(self,tag=None,trace=False):

        if trace:
            s1 = '%5s' % '' if tag is None else tag
            s2 = '%4s %4s %4s' % gc.get_count()
            print('gc: %s %s' % (s1,s2))
        gc.collect()
        # This is always 0,0,0
        # print('gc: %s %s %s' % gc.get_count())
    #@+node:ekr.20130331062640.5486: *3* u.compute_context_level
    def compute_context_level(self,node):
        
        '''Compute the indentation of a node.
        This method eliminates the need to inject an stc_level var into the tree.
        '''
        
        # The kinds of nodes that increase indentation level.
        if hasattr(node,'stc_parent'):
            level,parent = 0,node.stc_parent
            while parent:
                if isinstance(parent,(ast.ClassDef,ast.FunctionDef,ast.Module)):
                    level += 1
                parent = parent.stc_parent
            return level
        else:
            g.trace('** no stc_parent field!',node)
            return 0
    #@+node:ekr.20130329073341.5513: *3* u.compute_module_cx
    def compute_module_cx(self,node):
        '''Return the module context for the given node.'''
        parent = node
        while parent:
            if isinstance(parent,ast.Module):
                return parent
            else:
                parent = parent.stc_parent
        else:
            assert False,node
    #@+node:ekr.20140403052958.5520: *3* u.compute_class_or_module_cx
    def compute_class_or_module_cx(self,node):
        '''Return the class or module context of node.'''
        parent = node
        while parent:
            if isinstance(parent,(ast.ClassDef,ast.Module,ast.Module)):
                return parent
            else:
                parent = parent.stc_parent
        else:
            assert False,node
    #@+node:ekr.20130329114558.5695: *3* u.compute_node_cx
    def compute_node_cx(self,node):
        '''Return the nearest enclosing context for the given node.'''
        parent = node
        while parent:
            if isinstance(parent,(ast.ClassDef,ast.FunctionDef,ast.Module,ast.Lambda,ast.Module)):
                return parent
            else:
                parent = parent.stc_parent
        else:
            assert False,node
    #@+node:ekr.20130318222300.9442: *3* u.compute_node_level
    def compute_node_level(self,node):
        
        '''Compute the indentation of a node.
        This method eliminates the need to inject an stc_level var into the tree.
        '''
        
        # The kinds of nodes that increase indentation level.
        level_changers = (
            ast.ClassDef,ast.FunctionDef,ast.Module,
            ast.For,ast.If,ast.TryExcept,ast.TryFinally,ast.While,ast.With,
        )
        if hasattr(node,'stc_parent'):
            level,parent = 0,node.stc_parent
            while parent:
                if isinstance(parent,level_changers):
                    level += 1
                parent = parent.stc_parent
            return level
        else:
            g.trace('** no stc_parent field!',node)
            return 0
    #@+node:ekr.20130316193354.9276: *3* u.diff_time, get_time & time_format
    def diff_time(self,t):
        
        return '%4.2f sec.' % (time.time()-t)
        
    def get_time(self):
        
        # Used to put timestamps in headlines.
        return time.strftime('%Y/%m/%d/%H:%M:%S',time.localtime())

    def time_format(self,t):
        
        return '%4.2f sec.' % t
    #@+node:ekr.20130320065023.9551: *3* u.drivers: p0,p01,p012,p0_s,p01_s,p012_s
    # For use by unit tests.
    #@+node:ekr.20130320065023.9552: *4* u.p0
    def p0(self,files,project_name,report):
        '''Parse all files in a list of file names.'''
        u = self
        if report and not g.app.runningAllUnitTests:
            print(project_name)
        t = time.time()
        d = dict([(fn,u.parse_file(fn)) for fn in files])
        p0_time = u.diff_time(t)
        if report:
            u.p0_report(len(files),p0_time)
        return d
    #@+node:ekr.20130320065023.9556: *4* u.p01
    def p01(self,files,project_name,report):
        '''Parse and run P1 on all files in a list of file names.'''
        u = self
        if report and not g.app.runningAllUnitTests:
            print(project_name)
        # Pass 0.
        t0 = time.time()
        d = dict([(fn,u.parse_file(fn)) for fn in files])
        p0_time = u.diff_time(t0)
        # Pass 1.
        t = time.time()
        n_attrs = 0
        # n_contexts = 0
        # n_defined = 0
        n_nodes = 0
        u.p1 = p1 = P1() # Set u.p1 for stats.
        for fn in files:
            root = d.get(fn)
            p1(fn,root)
            n_attrs += p1.n_attributes
            n_nodes += p1.n_nodes
        p1_time = u.diff_time(t)
        tot_time = u.diff_time(t0)
        if report:
            u.p01_report(len(files),p0_time,p1_time,tot_time,
                n_attrs=n_attrs,n_nodes=n_nodes)
        return d
    #@+node:ekr.20130320065023.9562: *4* u.p012
    def p012(self,files,project_name,report):
        '''Parse and run P1 and TypeInferrer on all files in a list of file names.'''
        u = self
      #  if report and not g.app.runningAllUnitTests:
      #      print(project_name)
        # Pass 0.
        t0 = time.time()
        d = dict([(fn,u.parse_file(fn)) for fn in files])
        p0_time = u.diff_time(t0)
        # Pass 1.
        t = time.time()
        p1 = P1()
        for fn in files:
            root = d.get(fn)
            p1(fn,root)
        p1_time = u.diff_time(t)
        # Pass 2.
        t = time.time()
        ti = TypeInferrer()
        for fn in files:
            ti(d.get(fn))
        p2_time = u.diff_time(t)
        tot_time = u.diff_time(t0)
        if report:
            u.p012_report(len(files),p0_time,p1_time,p2_time,tot_time)
        return d
    #@+node:ekr.20130320065023.9553: *4* u.p0_report
    def p0_report(self,n,t0):
        
        '''Report stats for p0 and p0s.'''
        if not g.app.runningAllUnitTests:
            if n > 0:
                print('files: %s' % n)
            print('parse: %s' % t0)
    #@+node:ekr.20130320065023.9558: *4* u.p01_report
    def p01_report(self,n,t0,t1,tot_t,n_attrs=None,n_nodes=None):
        
        '''Report stats for p01 and p01s.'''
        if not g.app.runningAllUnitTests:
            if n > 0:
                print('files: %s' % n)
            print('parse: %s' % t0)
            if n_attrs is None:
                print('   p1: %s' % t1)
            else:
                print('   p1: %s nodes: %s attrs: %s' % (t1,n_nodes,n_attrs))
            print('  tot: %s' % tot_t)
    #@+node:ekr.20130320065023.9564: *4* u.p012_report
    def p012_report(self,n,t0,t1,t2,tot_t,n_attrs=None,n_nodes=None):
        
        '''Report stats for p012 and p012s.'''
        if not g.app.runningAllUnitTests:
            if n > 0:
                print('files: %s' % n)
            print('parse: %s' % t0)
            if n_attrs is None:
                print('   p1: %s' % t1)
            else:
                print('   p1: %s nodes: %s attrs: %s' % (t1,n_nodes,n_attrs))
            print('infer: %s' % t2)
            print('  tot: %s' % tot_t)

    #@+node:ekr.20130320065023.9560: *4* u.p0s
    def p0s(self,s,report=True):
        
        '''Parse an input string.'''
        u = self
        t = time.time()
        node = ast.parse(s,filename='<string>',mode='exec')
        p0_time = u.diff_time(t)
        if report:
            u.p0_report(1,p0_time)
        return node
    #@+node:ekr.20130320065023.9554: *4* u.p01s
    def p01s(self,s,report=True):
        
        '''Parse and run P1 on an input string.'''
        u = self
        t0 = time.time()
        node = ast.parse(s,filename='<string>',mode='exec')
        p0_time = u.diff_time(t0)
        t = time.time()
        P1().run('<string>',node)
        p1_time = u.diff_time(t)
        tot_time = u.diff_time(t0)
        if report:
            u.p01_report(1,p0_time,p1_time,tot_time)
        return node
    #@+node:ekr.20130320065023.9566: *4* u.p012s
    def p012s(self,s,report=True):
        
        '''Parse and run P1 and TypeInferrer on an input strin.'''
        u = self
        t0 = time.time()
        node = ast.parse(s,filename='<string>',mode='exec')
        p0_time = u.diff_time(t0)
        t = time.time()
        P1().run('<string>',node)
        p1_time = u.diff_time(t)
        t = time.time()
        TypeInferrer().run(node)
        p2_time = u.diff_time(t)
        tot_time = u.diff_time(t0)
        if report:
            u.p012_report(None,1,p0_time,p1_time,p2_time,tot_time)
        return node
    #@+node:ekr.20121119162429.4139: *3* u.dump_ast & helpers
    # Adapted from Python's ast.dump.

    def dump_ast(self,node,annotate_fields=True,disabled_fields=None,
        include_attributes=False,indent=2
    ):
        """
        Return a formatted dump (a string) of the AST node.
        
        annotate_fields:    True: show names of fields (can't eval the dump).
        disabled_field:     List of names of fields not to show: e.g. ['ctx',]
        include_attributes: True: show line numbers and column offsets.
        indent:             Number of spaces for each indent.
        
        """
        
        #@+others
        #@+node:ekr.20121206222535.7800: *4* class AstDumper
        class AstDumper:
            
            def __init__(self,u,annotate_fields,disabled_fields,format,include_attributes,indent_ws):
            
                self.u = u
                self.annotate_fields = annotate_fields
                self.disabled_fields = disabled_fields
                self.format = format
                self.include_attributes = include_attributes
                self.indent_ws = indent_ws

            #@+others
            #@+node:ekr.20121119162429.4140: *5* dump
            def dump(self,node,level=0):
                sep1 = '\n%s' % (self.indent_ws*(level+1))
                if isinstance(node,ast.AST):
                    fields = [(a,self.dump(b,level+1)) for a,b in self.get_fields(node)]
                        # ast.iter_fields(node)]
                    if self.include_attributes and node._attributes:
                        fields.extend([(a,self.dump(getattr(node,a),level+1))
                            for a in node._attributes])
                    aList = self.extra_attributes(node)
                    if aList: fields.extend(aList)
                    if self.annotate_fields:
                        aList = ['%s=%s' % (a,b) for a,b in fields]
                    else:
                        aList = [b for a,b in fields]
                    compressed = not any([isinstance(b,list) and len(b)>1 for a,b in fields])
                    name = node.__class__.__name__
                    if compressed and len(','.join(aList)) < 100:
                        return '%s(%s)' % (name,','.join(aList))
                    else:
                        sep = '' if len(aList) <= 1 else sep1
                        return '%s(%s%s)' % (name,sep,sep1.join(aList))
                elif isinstance(node,list):
                    compressed = not any([isinstance(z,list) and len(z)>1 for z in node])
                    sep = '' if compressed and len(node) <= 1 else sep1
                    return '[%s]' % ''.join(
                        ['%s%s' % (sep,self.dump(z,level+1)) for z in node])
                else:
                    return repr(node)
            #@+node:ekr.20121119162429.4141: *5* extra_attributes & helpers
            def extra_attributes (self,node):
                
                '''Return the tuple (field,repr(field)) for all extra fields.'''
                
                d = {
                    'e':      self.do_repr,
                    # '_parent':self.do_repr,
                    'cache':self.do_cache_list,
                    # 'ivars_dict': self.do_ivars_dict,
                    'reach':self.do_reaching_list,
                    'typ':  self.do_types_list,
                }

                aList = []
                for attr in sorted(d.keys()):
                    if hasattr(node,attr):
                        val = getattr(node,attr)
                        f = d.get(attr)
                        s = f(attr,node,val)
                        if s:
                            aList.append((attr,s),)
                return aList
            #@+node:ekr.20121206222535.7802: *6* AstDumper.helpers
            def do_cache_list(self,attr,node,val):
                return self.u.dump_cache(node)
                
            # def do_ivars_dict(self,attr,node,val):
                # return repr(val)

            def do_reaching_list(self,attr,node,val):
                assert attr == 'reach'
                return '[%s]' % ','.join(
                    [self.format(z).strip() or repr(z)
                        for z in getattr(node,attr)])

            def do_repr(self,attr,node,val):
                return repr(val)

            def do_types_list(self,attr,node,val):
                assert attr == 'typ'
                return '[%s]' % ','.join(
                    [repr(z) for z in getattr(node,attr)])
            #@+node:ekr.20121206222535.7803: *5* get_fields
            def get_fields (self,node):
                
                fields = [z for z in ast.iter_fields(node)]
                result = []
                for a,b in fields:
                    if a not in self.disabled_fields:
                        if b not in (None,[]):
                            result.append((a,b),)
                return result
            #@+node:ekr.20121208161542.7875: *5* kind
            def kind(self,node):
                
                return node.__class__.__name__
            #@-others
        #@-others
        
        if isinstance(node,ast.AST):
            indent_ws = ' '*indent
            dumper = AstDumper(self,annotate_fields,disabled_fields or [],
                self.format,include_attributes,indent_ws)
            return dumper.dump(node)
        else:
            raise TypeError('expected AST, got %r' % node.__class__.__name__)
    #@+node:ekr.20121225045023.5126: *3* u.dump_ivars_dict
    def dump_ivars_dict(self,d):
        
        def format_list(key):
            return self.format(d.get(key))
            # return ','.join([self.format(val) for val in d.get(key)])

        return 'ivars_dict: {%s}' % ','.join(
            ['%s:%s' % (z,format_list(z)) for z in sorted(d.keys())])
    #@+node:ekr.20120708080855.3526: *3* u.error/note/warning
    errors_given = []

    def error (self,s):
        
        # self.stats.n_errors += 1
        if s not in self.errors_given:
            self.errors_given.append(s)
            if g.app.unitTesting:
                pass
            elif g.unitTesting:
                print('Error: %s' % s)
            else:
                print('\nError: %s\n' % s)
        
    def note (self,s):
        
        print('Note: %s' % s)

    def warning (self,s):
        
        # self.stats.n_warnings += 1
        print('\nWarning: %s\n' % s)
    #@+node:ekr.20120626085227.11460: *3* u.files_in_dir
    def files_in_dir (self,theDir,recursive=True,extList=None,excludeDirs=None):
        
        '''Return a list of all Python files in the directory.
        
        Include all descendants if recursiveFlag is True.
        
        Include all file types if extList is None.
        '''
        
        # if extList is None: extList = ['.py']
        if excludeDirs is None: excludeDirs = []
        result = []

        if recursive:
            for root, dirs, files in os.walk(theDir):
                for z in files:
                    fn = g.os_path_finalize_join(root,z)
                    junk,ext = g.os_path_splitext(fn)
                    if not extList or ext in extList:
                        result.append(fn)
                if excludeDirs and dirs:
                    for z in dirs:
                        if z in excludeDirs:
                            dirs.remove(z)
        else:
            for ext in extList:
                result.extend(glob.glob('%s.*%s' % (theDir,ext)))
            
        return sorted(list(set(result)))
    #@+node:ekr.20130310085949.8440: *3* u.first_line
    def first_line(self,s):
        
        i = s.find('\n')
        return s if i == -1 else s[:i]
    #@+node:ekr.20130319130339.9446: *3* u.format & pattern_format
    def format(self,node,first_line=True,pattern=False):
        
        u = self
        if pattern:
            if not u.pattern_formatter_instance:
                u.pattern_formatter_instance = PatternFormatter()
            s = u.pattern_formatter_instance(node)
            return u.first_line(s) if first_line else s
        else:
            if not u.formatter_instance:
                u.formatter_instance = AstFormatter()
            s = u.formatter_instance(node)
            return u.first_line(s) if first_line else s
            
    def pattern_format(self,node,first_line=True):
        
        return self.format(node,first_line,True)
    #@+node:ekr.20130301092508.9753: *3* u.get_project_directory
    def get_project_directory(self,name):
        
        u = self
        # Ignore everything after the first space.
        i = name.find(' ')
        if i > -1:
            name = name[:i].strip()
        leo_path,junk = g.os_path_split(__file__)
        d = { # Change these paths as required for your system.
            'coverage': r'C:\Python26\Lib\site-packages\coverage-3.5b1-py2.6-win32.egg\coverage',
            'leo':      r'C:\leo.repo\leo-editor\leo\core',
            'lib2to3':  r'C:\Python26\Lib\lib2to3',
            'pylint':   r'C:\Python26\Lib\site-packages\pylint-0.25.1-py2.6.egg\pylint',
            'rope':     r'C:\Python26\Lib\site-packages\rope-0.9.4-py2.6.egg\rope\base',
        }
        dir_ = d.get(name.lower())
        # g.trace(name,dir_)
        if not dir_:
            g.trace('bad project name: %s' % (name))
        if not g.os_path_exists(dir_):
            g.trace('directory not found:' % (dir_))
        return dir_ or ''
    #@+node:ekr.20120626085227.11464: *3* u.get_source
    def get_source (self,fn):
        
        '''Return the entire contents of the file whose name is given.'''
        
        try:
            fn = g.toUnicode(fn)
            # g.trace(g.os_path_exists(fn),fn)
            f = open(fn,'r')
            s = f.read()
            f.close()
            return s
        except IOError:
            return '' # Caller gives error message.
    #@+node:ekr.20121217181837.7735: *3* u.kind
    def kind(self,node):
        
        return node.__class__.__name__
    #@+node:ekr.20120723140502.3620: *3* u.last_top_level_node
    def last_top_level_node(self,c):

        p = c.rootPosition()
        while p.hasNext():
            p = p.next()
        return p
    #@+node:ekr.20130403133155.5485: *3* u.lookup
    def lookup(self,cx,key):
        
        '''Return the symbol table for key, starting the search at node cx.'''

        trace = False and not g.app.runningAllUnitTests
        # contexts = ast.Module,ast.ClassDef,ast.FunctionDef,ast.Lambda
        
        cx2 = cx
        while cx2:
            st = cx.stc_symbol_table
            if key in st.d.keys():
                return st
            else:
                cx2 = cx2.stc_context
        ############################
        assert False
        for d in (self.builtins_d,self.special_methods_d):
            if key in d.keys():
                return d
        else:
            if trace:
                g.trace('** (ScopeBinder) no definition for %20s in %s' % (
                    key,self.u.format(cx)))
            return None
    #@+node:ekr.20120626085227.11607: *3* u.module_name
    def module_name (self,fn):
        
        fn = g.shortFileName(fn)
        if fn.endswith('.py'):
            fn = fn[:-3]
        return fn
    #@+node:ekr.20120626085227.11466: *3* u.node_after_tree
    # The _parent must have been injected into all parent nodes for this to work.
    # This will be so, because of the way in which visit traverses the tree.

    def node_after_tree (self,tree):
        
        trace = False
        u = self
        tree1 = tree # For tracing
        
        if not isinstance(tree,ast.AST):
            return None
        
        def children(tree):
            return [z for z in ast.iter_child_nodes(tree)]
            
        def parent(tree):
            if not hasattr(tree,'_parent'): g.trace('***no _parent: %s' % repr(tree))
            return getattr(tree,'_parent',None)

        def next(tree):
            if parent(tree):
                sibs = children(parent(tree))
                if tree in sibs:
                    i = sibs.index(tree)
                    if i + 1 < len(sibs):
                        return sibs[i+1]
            return None

        result = None
        while tree:
            result = next(tree)
            if result:
                break
            else:
                tree = parent(tree)

        if trace:
            def info(node):
                kind = node and node.__class__.__name__
                return '%s: %9s' % (kind,id(node))
                
            for z in (ast.Module,ast.ClassDef,ast.FunctionDef):
                if isinstance(tree1,z):
                    g.trace('node: %22s, parent: %22s, after: %22s' % (
                        info(tree1),info(parent(tree1)),info(result)))
                    break

        return result
    #@+node:ekr.20130310085949.8438: *3* u.parse_...
    def parse_file(self,fn):
        
        s = self.get_source(fn)
        return ast.parse(s,filename=fn,mode='exec')

    def parse_string(self,fn,s):
        
        return ast.parse(s,filename=fn,mode='exec')
        
    def parse_files_in_list(self,aList):
        
        return dict([(fn,self.parse_file(fn)) for fn in aList])
    #@+node:ekr.20121021110813.3885: *3* u.profile
    def profile(self,c,project_name,verbose=True):
        
        '''Run a full project test with profiling enabled.'''
        
        import pstats # May fail on some Linux installations.
        import cProfile

        u = self
        clean_project_name = u.clean_project_name(project_name)
        path,junk = g.os_path_split(c.fileName())
        fn = g.os_path_finalize_join(path,'report','stc_profile_data.txt')
        command = 'import statictypechecking as stc; stc.Utils().test_wrapper("%s")' % (
            project_name)
        cProfile.run(command,fn)
        f = g.fileLikeObject()
        ps = pstats.Stats(fn,stream=f)
        ps.strip_dirs()
        ps.sort_stats('time',) # 'calls','cumulative','time')
        ps.print_stats()
        s = f.read()
        f.close()
        fn2 = g.os_path_finalize_join(path,'report','stc_report_%s.txt' % (clean_project_name))
        f2 = open(fn2,'w')
        f2.write(s)
        f2.close()
        if verbose:
            print('profile written to %s' % (fn2))
        # print(s)
        # os.system('ed "%s"' % (fn2))
    #@+node:ekr.20120626085227.11463: *3* u.project_files
    def project_files(self,name,force_all=False):
        u = self
        # Ignore everything after the first space.
        i = name.find(' ')
        if i > -1:
            name = name[:i].strip()
        leo_path,junk = g.os_path_split(__file__)
        d = { # Change these paths as required for your system.
            'coverage': (
                r'C:\Python26\Lib\site-packages\coverage-3.5b1-py2.6-win32.egg\coverage',
                ['.py'],['.bzr','htmlfiles']),
            'leo':(
                r'C:\leo.repo\leo-editor\leo\core',
                # leo_path,
                ['.py'],['.bzr']),
            'lib2to3': (
                r'C:\Python26\Lib\lib2to3',
                ['.py'],['tests']),
            'pylint': (
                r'C:\Python26\Lib\site-packages\pylint-0.25.1-py2.6.egg\pylint',
                ['.py'],['.bzr','test']),
            'rope': (
                # r'C:\Python26\Lib\site-packages\rope',['.py'],['.bzr']),
                r'C:\Python26\Lib\site-packages\rope-0.9.4-py2.6.egg\rope\base',['.py'],['.bzr']),
        }
        data = d.get(name.lower())
        if not data:
            g.trace('bad project name: %s' % (name))
            return []
        theDir,extList,excludeDirs=data
        files = u.files_in_dir(theDir,recursive=True,extList=extList,excludeDirs=excludeDirs)
        if name.lower() == 'leo':
            for exclude in ['__init__.py','format-code.py']:
                files = [z for z in files if not z.endswith(exclude)]
            fn = g.os_path_finalize_join(theDir,'..','plugins','qtGui.py')
            if fn and g.os_path_exists(fn):
                files.append(fn)
        if g.app.runningAllUnitTests and len(files) > 1 and not force_all:
            return [files[0]]
        else:
            return files
    #@+node:ekr.20130305090136.9666: *3* u.showAttributes
    # Used by modified pyflakes code.

    def showAttributes(self,def_d,ref_d):

        def_keys = sorted(def_d.keys())
        ref_keys = sorted(ref_d.keys())
        g.trace('Dumps of attributes...')
        def show_list(aList):
            return ','.join(aList)
        if 0:
            g.trace('Defined attributes...')
            for key in def_keys:
                print('%30s %s' % (key,show_list(def_d.get(key))))
        if 0:
            print('\nReferenced attributes...')
            for key in ref_keys:
                print('%30s %s' % (key,show_list(ref_d.get(key))))
        if 0:
            print('\nReferenced, not defined attributes...')
            result = []
            for key in ref_keys:
                if key not in def_keys:
                    aList = ref_d.get(key,[])
                    for z in aList:
                        result.append('%s.%s' % (key,z))
            for s in sorted(result):
                print(s)
        if 0:
            print('\nDefined, not referenced attributes...')
            result = []
            for key in def_keys:
                if key not in ref_keys:
                    aList = def_d.get(key,[])
                    for z in aList:
                        result.append('%s.%s' % (key,z))
            for s in sorted(result):
                print(s)
        if 1:
            table = (
                "'",'"',
                'aList','aList2','u','at',
                'baseEditCommandsClass',
                'c','c1','c2','ch','cc',
                # 'c.frame',
                # 'c.frame.body.bodyCtrl','c.frame.body.bodyCtrl.widget',
                # 'c.frame.tree','c.frame.tree.widget',
                'd','d1','d2','g','g.app','k',
                'lm','menu','mf',
                'p','p1','p2', # 'p.v','p2','p2.v','p.b','p.h',
                'QFont','QtCore','QtGui',
                'pc','qt','rf','root',
                's','s1','s2',
                'table','theFile','tc','tm','tt','tree',
                'u','ui',
                'v','v2','vnode',# 'v.b','v.h','v2.b','v2.h',
                'w','w2','widget','wrapper','wrapper2',
                'x',
                'os','pdb','re','regex','string','StringIO','sys','subprocess',
                'tabnanny','time','timer','timeit','token','traceback','types',
                'unittest','urllib','urlparse','xml',
                'leoApp','leoBody','leoCache','leoColor','leoCommands','leoConfig',
                'leoFind','leoFrame','leoGui','leoIPython','leoImport',
                'leoLog','leoMenu','leoNodes','leoPlugins','leoRst',
                'leoTangle','leoTest','leoTree',
            )
            print('\nAll attributes...')
            result = []
            for key in def_keys:
                aList = def_d.get(key,[])
                for z in aList:
                    result.append('%s.%s' % (key,z))
            for key in ref_keys:
                aList = ref_d.get(key,[])
                for z in aList:
                    result.append('%s.%s' % (key,z))
            if 1:
                result = [s for s in result
                    if not any([s.startswith(s2+'.') or s.startswith(s2+'[') for s2 in table])]
                table2 = ('join','strip','replace','rstrip')
                result = [s for s in result
                    if not s.startswith("'") or not any([s.endswith('.'+s2) for s2 in table2])]
                table3 = ('__init__','__name__','__class__','__file__',)
                result = [s for s in result
                    if not any([s.endswith('.'+s2) for s2 in table3])]
            if 1:
                for s in sorted(set(result)):
                    if not s.startswith('self.'):
                        print(s)
            print('%s attributes' % len(result))
    #@+node:ekr.20121114124910.4019: *3* u.test_wrapper
    def test_wrapper(self,project_name):
        
        import statictypechecking as stc
            # no need to reload stc.

        u = stc.Utils()
        aList = u.project_files(project_name)
        for fn in aList:
            # u.module(fn=fn)
            root = u.parse_file(fn)
            # print(u.first_line(u.format(root)))
    #@+node:ekr.20130319130339.9445: *3* u.update_run_count
    def update_run_count(self,verbose=False):
        
        # Bump the cumulative script count.
        d = g.app.permanentScriptDict
        d['n'] = n = 1 + d.get('n',0)
        if verbose and not g.app.runningAllUnitTests:
            print('run %s...' % (n))