import types, re, dynamic

#These fields are not displayed in the simple-mapping of
#an object's to_string function. They instead must be handled
#separately because their strings cannot be easily represented.
protected_fields = ["child", "children", "variables"]

#If this field is empty, it will not appear in to_string's output.
ignore_if_none = ["error", "results", "expression", "evaluated_against"]


class Abstract:
   def __init__(self, expression):
      self.expression = expression
      
      self.result = "Not Evaluated"
      self.results = None
      self.error = None
      
   def __repr__(self):
      return self.to_string().rstrip()

   def err(self, error):
      self.error = error
      raise Exception(error)

   def reduce(self):
      obj = {}
      for key, val in self.__dict__.iteritems():
         if key not in protected_fields:
            if key not in ignore_if_none or val is not None:
               obj[key] = (str(val.__name__) if isinstance(val, types.FunctionType) else str(val))
      obj["name"] = self.__class__.__name__.upper()
      if "child" in self.__dict__ and self.child:
         obj["child"] = self.child.reduce()
      if "children" in self.__dict__:
         obj["children"] = [child.reduce() for child in self.children]
      return obj

   def to_string(self, level = 0):
      spacesDot = ""
      spacesPoint = ""
      for i in xrange(level): 
         spacesDot += "..." if i == level - 1 else "   "
         spacesPoint += "   "
      spacesPoint += "-"
      
      #Write title
      build = spacesDot + self.__class__.__name__.upper() + "\n"
      
      #Populate fields
      for key, val in self.__dict__.iteritems():
         if key not in protected_fields:
            if key not in ignore_if_none or val is not None:
               build += spacesPoint + key + ": "
               build += (str(val.__name__) if isinstance(val, types.FunctionType) else str(val)) + "\n"

      #Populate children recursively
      if "child" in self.__dict__ and self.child:
         build += self.child.to_string(level + 1)
      if "children" in self.__dict__:
         for child in self.children:
            build += child.to_string(level + 1)
      return build.rstrip() + "\n"
   
   #Reset the results fields for a new bug for this object,
   #and recursively do the same for its children.
   def clear(self):
      self.result = "Not Evaluated"
      self.results = None
      self.error = None
      
      if "evaluated_against" in self.__dict__:
         self.evaluated_against = None
      
      if "child" in self.__dict__ and self.child:
         self.child.clear()
      if "children" in self.__dict__:
         for child in self.children:
            child.clear()

   #Recursively dives into deeper levels of dictionaries
   #previously indicated by dot-separated data fields in the expression.
   #I.e. type.type.forEach() dives into the first level of type, then the second.
   def data_dive(self, data):
      for dive in self.data:
         try:
            data = data[dive]
         except:
            self.err("%s is not a valid member of data." % dive)
      return data


#Always returns the given value on evaluation.
#Used for error handling (never go into, i.e. False)
#and objects without expressions (always go into, i.e. True)
class AlwaysReturn(Abstract):
   def __init__(self, boolean):
      Abstract.__init__(self, None)
      self.boolean = boolean

   def evaluate(self, data):
      self.result = self.boolean
      return self.result


#Returns the opposite of whatever result it gets.
class Not(Abstract):
   def __init__(self, expression, child):
      Abstract.__init__(self, expression)
      self.child = child

   def evaluate(self, data):
      self.result = not self.child.evaluate(data)
      return self.result 


#If ANY of its components are true returns true.
class Or(Abstract):
   def __init__(self, expression):
      Abstract.__init__(self, expression)
      self.children = []
      
   def evaluate(self, data):
      for child in self.children:
         #ORing functionality
         if child.evaluate(data):
            self.result = True
            return True
      
      #Boolean, matches, error messages
      self.result = False
      return False


#If ALL of its components are true, returns true
class And(Abstract):
   def __init__(self, expression):
      Abstract.__init__(self, expression)
      self.children = []
      
   def evaluate(self, data):
      for child in self.children:
         #ANDing functionality
         if not child.evaluate(data):
            self.result = False
            return False
      self.result = True
      return True
   

#Iterates through an array data field (or a string, character-by-character)
class ForEach(Abstract):
   def __init__(self, expression, data, child):
      Abstract.__init__(self, expression)
      self.child = child
      self.data = data
      
   def evaluate(self, data):
      #Dive into selected data field
      data = self.data_dive(data)
      if type(data) is not list and type(data) is not str:
         self.err("ForEach can only be called on arrays or strings.")
      
      #Evaluate child against each element, and compile results
      self.results = []
      for child in data:
         if self.child.evaluate(child):
            self.results.append(child)

      self.result = len(self.results) > 0
      return self.result
   

#Where the action happens. Calls one of the preset requirement functions
#to get a boolean result (and potentially also list) on given data and parameters.
class Function(Abstract):
   
   CHAR_MATCHER = re.compile(r"\w")
   
   def __init__(self, expression, data, function, params, var_params, variables, child):
      #Make the 'this' keyword automatically assumed
      if type(data) is list and len(data) > 0 and data[0] == "this":
         data = data[1:]
      
      Abstract.__init__(self, expression)
      self.data = data
      self.function = function
      self.params = params
      self.var_params = var_params
      self.variables = variables
      self.child = child
      self.evaluated_against = None
   
   #Populates the list of parameters
   @staticmethod
   def populate_variables(knowns, populate, data):
      result = []
      
      for variable in populate:
         result += Function.populate_variable(knowns, variable, data)

      return result
      
   @staticmethod
   def populate_variable(knowns, variable, data, names = []):
      result = []
      
      #Find the variable:
      escape = False
      found = False
      for i, c in enumerate(variable):
         if escape:
            continue
         elif c == "\\":
            escape = True
         elif c == "@":
            first = variable[0:i]
            build = ""
            
            #Find variable name
            for j, v in enumerate(variable[i + 1:]):
               if v == "@":
                  #Empty variable. No good
                  if build == "":
                     raise Exception("Empty variable encountered while parsing %s" % variable)
                  
                  #End of variable. Good to go.
                  found = True
                  break;
               
               #Keep building variable name until @ encountered
               elif re.search(Function.CHAR_MATCHER, v):
                  build += v
                  
               else:
                  raise Exception("Unexpected character %s while parsing variable in expression %s" % (v, variable))
            
            #Unclosed variable
            if not found:
               raise Exception("Variable not closed in expression %s" % variable)
            
            #Get part after variable, and break out of search loop
            last = variable[i + j + 2:]
            break
         
      #If we didn't find any nested variables to explore, just go ahead and return this value
      if not found:
         return [unescape(str(variable))]
      
      #Otherwise, make sure we've not gotten ourselves into a varaible loop
      elif build in names:
         raise Exception("Variable loop detected %s" % variable)
         
      #Variable found and expression split. Match to correct dictionary
      my_var = None
      for known in knowns:
         if build == known["name"]:
            my_var = known
            break;
      
      #If no dictionary found
      if not my_var:
         raise Exception("No variable named @%s@ found in current scope." % build)
      
      #Handle type
      if my_var["type"] == "dynamic":
         values = Function.populate_dynamic([value["value"] for value in my_var["values"]], data)
      else:
         values = [value["value"] for value in my_var["values"]]
      
      #Make sure the results are iterable
      if not hasattr(values, "__iter__"):
         values = [values]
      
      #Now apply recursive brute-force population 
      for value in values:
         #The value that has already been evaluated gets the current build variable to detect loops
         mergeA = Function.populate_variable(knowns, str(value), data, [build] + names)
         #The untouched last part does not need the current build, because it could have the same
         #build on the same level, which is legal.
         mergeB = Function.populate_variable(knowns, last, data, names)
         
         #Merge the two results sets in every way possible
         first = unescape(first)
         for a in mergeA:
            for b in mergeB:
               result.append(first + a + b)
         
      return result
   
   
   #Handles the value of a dynamic variable, calling the correct function with
   #the correct parameters
   @staticmethod
   def populate_dynamic(value, data):
      
      return value
   
      
   def evaluate(self, data):
      params = self.params + self.populate_variables(self.variables, self.var_params, data)
      self.evaluated_against = params
      
      #Evaluate based on results of child function
      if self.child:
         self.child.evaluate(data)
         try:
            self.results = self.function(self.child.results, params)
         except Exception as e:
            self.err(e.args[0])
      #Evaluate based on results of selected data
      else:
         #Dive into selected data field
         data = self.data_dive(data)
         
         #Run function
         try:
            self.results = self.function(data, params)
         except Exception as e:
            self.err(e.args[0])
      
      #Handle results
      if type(self.results) is bool:
         self.result = self.results
         self.results = None
      elif self.results is None:
         self.result = False
      else:
         self.result = len(self.results) > 0

      return self.result
      

#Un-escapes parameters
def unescape(string):
   escape = False
   build = ""
   for c in string:
      if escape:
         build += c
         escape = False
      elif c == "\\":
         escape = True
      else:
         build += c
   if escape:
      raise Exception("Escape character not followed.")
   return build
      