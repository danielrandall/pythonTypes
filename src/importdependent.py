from src.typeclasses import Module_Type, any_type
from src.typechecking.basictypevariable import BasicTypeVariable

class ImportDependent(object):

    def __init__(self, name, import_from, as_name):
        self.name = name
        self.import_from = import_from
        self.as_name = as_name
        
    def is_import_from(self):
        ''' Returns class name if it's import_from otherwise None. '''
        return self.import_from
    
    def get_class_name(self):
        return self.name
        
    def get_module_name(self):
        ''' Returns only the module name in a string.
            e.g. "a.b.c" -> "c" '''
        module_path = self.import_from if self.import_from else self.name
        split_string = module_path.split('.')
        return split_string.pop()
    
    def get_as_name(self):
        ''' If no asname is specified then it is just the first package '''
        if self.as_name:
            return self.as_name
        split_string = self.name.split('.')
        return split_string[0]
    
    
    def convert_to_directories(self):
        module_path = self.import_from if self.import_from else self.name
        return module_path.replace('.', '/')
    
    def get_directory_no_name(self):
        converted = self.convert_to_directories()
        name = self.get_module_name()
 #       print(converted)
 #       print(name)
        if name == self.import_from:
            return "."
        # We want to remove the last '/' as well
        return converted[:converted.rfind(name) - 1]        
    
class ImportFrom():
    ''' item can be a module, package or a function/class/variable.
        The import statement first tests whether the item is defined in the package;
        if not, it assumes it is a module and attempts to load it. If it fails to find it, an ImportError exception is raised.
        Can only wildcard import modules - last item must be module
        import a.b.c defines:
            a
            a.b
            a.b.c
        You can import relative to the current directory using ellipses.
        . is current directory  - level = 1
        .. is one above         - level = 2
        ... is two above, and so on...
        This is represented in the levels variable '''
    def __init__(self, item, path = "", as_name = None, level = None):
        self.path = path
        self.item = item
        self.as_name = as_name
        self.level = level
    
    def convert_to_directories(self, path):
        return self.path.split('.')
    
    def get_as_name(self):
        if self.as_name:
            return self.as_name
        else:
            return self.item

    def find(self, file_tree, current_dir):
        if self.level:
            # Rolls back the dir for every level - 1
            for _ in range(self.level - 1):
                current_dir = current_dir.split('/')
                if len(current_dir) == 1:
                    current_dir = ""
                else:
                    current_dir.pop()
                current_dir = '/'.join(current_dir)
            self.path = current_dir + "." + self.path
            
        path = self.convert_to_directories(self.path)
        module_name = path.pop()
        path  = '/'.join(path)
        if not path:
            path = "."
                
        if self.item == "*":
            return self.do_wildcard_imports(file_tree, current_dir, path, module_name)
        
        # Regular import
        
        return [(self.get_as_name(), BasicTypeVariable([any_type]))]

       
    def do_wildcard_imports(self, file_tree, current_dir, path, module_name):
        
        if not path:
            concat_path = current_dir
        else:
            concat_path = '/'.join(path)
        
        if concat_path in file_tree:
            if module_name in file_tree[concat_path]:
                module = file_tree[concat_path][module_name].get_module_type()
                module_vars = module.get_vars()
                return [(name, var) for name, var in module_vars.items()]
            else:
                return []
        else:
            # What do we do here?
            return []
        
            
        
    
class Import():
    ''' Can only import modules and packages.
        Can not import classes/functions.
        If no as_name then define the first as a module:
            import a.b
            a -> module_type
              -> b -> module_type '''
    def __init__(self, path, as_name = None):
        self.path = path
        self.as_name = as_name
    
    def convert_to_directories(self, path):
        return path.split('.')
    
    def get_as_name(self):
        if self.as_name:
            return self.as_name
        return self.convert_to_directories(self.path)[0]
    
    def find(self, dirs, current_dir):
        path = self.convert_to_directories(self.path)
        
        if len(path) == 1:
            # Top level
            file_in_dir = path[0]
            as_name = self.as_name if self.as_name else file_in_dir
            if file_in_dir in dirs[current_dir]:
                return [(as_name, BasicTypeVariable([dirs[current_dir][file_in_dir].get_module_type()]))]
            else:
                # Can't find it
                return [(as_name, BasicTypeVariable([any_type]))]
        elif self.as_name:
            # We can just grab the module/package
            # Check module first
            name = path.pop()
            path_to_module = '/'.join(path)
                
            if path_to_module not in dirs:
                return [(self.as_name, BasicTypeVariable([any_type]))]
                
            return_type = None
            if name in dirs[path_to_module]:
                return [(self.as_name, BasicTypeVariable([dirs[path_to_module][name].get_module_type()]))]
            else:
                return [(self.as_name, BasicTypeVariable([any_type]))]
        else:
            return [(path[0], BasicTypeVariable([any_type]))]
                
                
                # First check if the last item is a module
          #      if path[-1] in dirs['/'.join(path[:-1])]:
          #          current_package = {path.pop(): [dirs['/'.join(path[:-1])]].get_module_type()}
                    
                # Else check if there is a package
          #      elif path in '/'.join(path):
          #          current_package = {path.pop(), Module_Type()}
          #      else:
                    # Can't find it
          #          return [(path[0], BasicTypeVariable([any_type]))]
           #     while not path:
           #         current_package =
                                             
            
        