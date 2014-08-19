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
        ''' If no asname is specified then it is just the name '''
        return self.as_name if self.as_name else self.name
    
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