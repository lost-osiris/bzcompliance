import re
import req_objects as objs
import req_functions as funcs

#Character code definitions
C_AND = 0
C_OR = 1
C_DOT = 2
C_BACK = 3
C_QUOTE = 4
C_OPEN = 5
C_CLOSE = 6
C_AT = 7
C_NOT = 8
C_COMMA = 9
C_ALPHA = 10
C_SPACE = 11


#Simple char-type matching for code clarity
def char_type(c):
   if c == "&":
      return C_AND
   if c == "+":
      return C_OR
   if c == ".":
      return C_DOT
   if c == "\\":
      return C_BACK
   if c == "\"":
      return C_QUOTE
   if c == "(":
      return C_OPEN
   if c == ")":
      return C_CLOSE
   if c == "@":
      return C_AT
   if c == "!":
      return C_NOT
   if c == ",":
      return C_COMMA
   if re.search("\w", c):
      return C_ALPHA
   if re.search("\s", c):
      return C_SPACE


def params_to_array(params, variables):
   #States
   START = 0
   STRING = 1
   NUMBER = 2
   NEED_COMMA = 3
   VARIABLE = 4
   STRING_VAR = 5
   
   #Space-relevant states
   USE_SPACE = [STRING, VARIABLE, STRING_VAR]
   
   #Setup
   params = params.strip()
   state = START
   array = []
   var_params = []
   build = ""
   var_build = ""
   count = 0
   var_seen = False
   escape = False
   
   #Iterate through characters using FSM
   for c in params:
      #Get character type
      char = char_type(c)
      
      #Ignore irrelevant space
      if char == C_SPACE and state not in USE_SPACE:
         continue;
      
      #Expecting token
      if state is START:
         if c.isdigit():
            state = NUMBER
            count = count * 10 + int(c)
         elif char is C_QUOTE:
            state = STRING
         elif char is C_AT:
            state = VARIABLE
         else:
            raise Exception("Number or string expected, got %s" % c)
      
      #Currently reading a stand-alone variable
      elif state is VARIABLE:
         if char is C_ALPHA:
            var_build += c
         elif char is C_AT:
            if not any(var_build in variable["name"] for variable in variables):
               raise Exception("No variable named @%s@ in scope." % var_build)
            var_params.append("@%s@" % var_build)
            var_build = ""
            state = NEED_COMMA
         else:
            raise Exception("Unexpected character %s while reading variable @%s..." % (c, var_build))   
         
      elif state is STRING:
         if escape:
            build += "\\" + c;
            escape = False
         elif char is C_BACK:
            escape = True;
         elif char is C_AT:
            state = STRING_VAR
         elif char is C_QUOTE:
            if var_seen:
               #Need to keep escape character if variable exists within parameter
               var_params.append(build)
            else:
               #Otherwise, throw them away.
               array.append(objs.unescape(build))
            build = ""
            var_seen = False
            state = NEED_COMMA
         else:
            build += c
      
      #Currently reading a variable nested within a string
      elif state is STRING_VAR:
         if char is C_ALPHA:
            var_build += c
         elif char is C_AT:
            if not any(var_build in variable["name"] for variable in variables):
               raise Exception("No variable named @%s@ in scope." % var_build)
            build += "@%s@" % var_build
            var_build = ""
            var_seen = True
            state = STRING
         else:
            raise Exception("Unexpected character %s while reading variable @%s..." % (c, var_build))
         
      elif state is NUMBER:
         if c.isdigit():
            count = count * 10 + int(c)
         elif c == ',':
            array.append(str(count))
            count = 0
            state = START
         else:
            raise Exception("Number or comma expected, got: %s" % c)
      
      elif state is NEED_COMMA:
         if char is C_COMMA:
            state = START
         else:
            raise Exception("Comma expected, got: %s" % c)
   
   if state is NUMBER:
      array.append(str(count))
      state = START
   
   if state is not START and state is not NEED_COMMA:
      raise Exception("Last parameter not closed within (%s)." % params)
   
   return array, var_params


'''
Returns the delta position of the first 0-level close
parenthesis. The expression passed in must have the
opening parenthesis trimmed off. Makes sure to find the
correct group closing, regardless of potential parenthesis
in strings or subgroups.

Ex:
"a + b + c)" -> 9
"a + (b + c))" -> 11
'''
def match_paren(expression):
   string = False
   ignore = False
   level = 0
   for pos, c in enumerate(expression):
      if ignore:
         ignore = False
         continue
   
      if c == '"':
         string = not string
      elif c == "\\":
         if not string:
            #Error. Backslash outside of string
            raise Exception("Unexepected escape character outside of string.")
         else:
            ignore = True
      elif c == "(" and not string:
         level += 1
      elif c == ")" and not string:
         if level == 0:
            return pos
         else:
            level -= 1
   raise Exception("Missing parenthesis to close the group containing: %s" % expression)


'''
Transforms the provided expression into an object-based data structure into
which bug data can be passed and evaluated. The resulting data structure maintains
error handling that can be used to debug expressions. This tokenizer also detects
and reports top-level syntactical errors.
'''
def tokenize(expression, variables):
   if len(expression.strip()) == 0:
      raise Exception("Cannot process empty expression.")
   
   #States used in the tokenizer's FSM
   START = 0
   DATA = 1
   FUNCTION = 2
   ENDED = 3
   
   #Default state is start for each expression and subexpression
   state = START
   
   #Internal variables for the FSM
   dot_okay = False  #Used in the ENDED state to determine whether a nested funciton is appropriate
   seen_not = False
   andor = None      #Assigned once we know how the level is grouped   
   data = None 
   function = None
   temp = None
   current_parent = None
   my_function = None   #Can actually be a group or a function
   
   #Set-up for iteration
   char = None
   end_of_exp = len(expression)
   pos = 0
   
   #Use a while loop to iterate through expression string, so we can jump around.
   #(With a for loop in python, you cannot dynamically change the index within the loop)  
   while pos < end_of_exp:
      #Get current char, and type of that char
      c = expression[pos]
      char = char_type(c)
      
      #First char of expression (or recursion), or state after we see an AND or OR
      if state == START:
         #Open a fresh new sub-expression
         if char == C_OPEN:
            #Determine the extent of the group
            pos += 1
            try:
               group_end = pos + match_paren(expression[pos:])
               sub = expression[pos : group_end]
               
            #Handle bad expressions detected by parenthesis matcher
            except:
               raise 
            
            #Tokenize the group recursively
            my_function = tokenize(sub, variables)
            my_function.expression = "(" + my_function.expression + ")"
            
            #Pretend that this iteration of the loop was on the closing parenthesis.
            #So, we'll start reading after the ) on the next iteration. 
            pos = group_end
            state = ENDED
            
         #Start reading the data element.
         elif char == C_ALPHA:
            data = c
            state = DATA
            
         #Note if we see not character
         elif char == C_NOT:
            seen_not = not seen_not
         
         #Safely ignore spaces when not reading tokens.
         elif char == C_SPACE:
            pass
         
         #Anything else is an error
         else:
            raise Exception("Unexpected character at start of new token.")
      
   
      elif state == DATA:
         #Append alpha-numeric characters to the data field
         if char == C_ALPHA:
            data += c
         #On dot, we're now reading function instead of data
         elif char == C_DOT:
            state = FUNCTION
            data = [data]
         #Give a special message for spaces
         elif char == C_SPACE:
            raise Exception("Unexpected end to data field. Dot (.) expected, got space.")
         #Anything else is an error
         else:
            raise Exception("Unexpected character while reading data field: %s" % c)
   
   
      #Read the name of the function to be called on the just-named data
      elif state == FUNCTION:
         #Append alpha-numeric characters to the data field
         if char == C_ALPHA:
            if not function:
               function = ""
            function += c
         
         #Error if different character without function being initialized
         elif not function:
            raise Exception("Missing function after data field, %s." % data)
         
         #Handle nested data
         elif char == C_DOT:
            data.append(function)
            function = None
            
         #On (, we're now reading parameters instead of function
         elif char == C_OPEN:
            #Build first bit of object expression before things start changing
            exp = ".".join(data) + "." + function + "(" if not temp else temp.expression + function + "("
            
            #Find extent of parameters
            pos += 1
            try:
               group_end = pos + match_paren(expression[pos:])
               sub = expression[pos : group_end]
               exp += sub + ")"
               
            #Handle bad expressions detected by parenthesis matcher
            except:
               raise 
            
            #Test if function is special loop function (previously named within)
            function = function.lower()
            within = function == "foreach"
            if within:
               #Create the within object, populating its child structure by recursively calling tokenize
               my_function = objs.ForEach(exp, data, tokenize(sub, variables))

            #Standard function handling
            else:
               try:
                  #Match the function name to it's python object
                  function = funcs.func_map[function]
               except:
                  raise Exception("Call to unknown function, %s." % function) 
               
               #Parse the parameters from within the parenthesis set
               params, var_params = params_to_array(sub, variables)
               if len(params) + len(var_params) == 0:
                  raise Exception("Function parameters cannot be empty, %s" % exp)
               
               
               #Check if nested function, and create appropriate object
               if temp:
                  my_function = objs.Function(exp, None, function, params, var_params, variables, temp)
               else:
                  my_function = objs.Function(exp, data, function, params, var_params, variables, None)            
            
            #Clear used up variables
            data = None
            function = None
            
            #Couple last housekeeping items
            dot_okay = True
            pos = group_end
            state = ENDED

         #Special message for spaces
         elif char == C_SPACE:
            raise Exception("Unexpected end to function field. '(' expected, got space.")       
         #Anything else is an error
         else:
            raise Exception("Unexpected character while reading function field.")         
      

      #We've just seen the end of a function or a group.
      elif state == ENDED:
         #Safely ignore spaces while waiting for & or +
         if char == C_SPACE:
            #However, a space does mean that a dot no longer makes sense
            dot_okay = False
         
         #Processor operators
         elif char == C_OR or char == C_AND:
            #Mismatched operators in same group level
            if andor != None and andor != char:
               raise Exception("Operator mismatch. AND and OR cannot coexist on the same group level.")
            
            #If this is the first and/or operator seen
            elif not andor:
               andor = char
               current_parent = objs.And(expression) if char == C_AND else objs.Or(expression)
            
            #Handle NOTs
            if seen_not:
               my_function = objs.Not("!" + my_function.expression, my_function)
               seen_not = False
            
            #Add last token as a child
            current_parent.children.append(my_function)
            my_function = None
            
            #Housekeeping
            dot_okay = False
            state = START            
                              
         #Handle nested functions
         elif dot_okay and char == C_DOT:
            temp = my_function
            state = FUNCTION
            
         #Anything else is an error
         else:
            raise Exception("Blah")
         
      pos += 1
   
   #Cleanup after iteration complete
   if state == ENDED:
      #Handle NOTs
      if seen_not:
         my_function = objs.Not("!" + my_function.expression, my_function)
         seen_not = False
      
      if current_parent:
         current_parent.children.append(my_function)
      else:
         current_parent = my_function
      
   #Raise error if unexpected stuff at the end.
   else:
      raise Exception("Unexpected end of expression.")
   
   return current_parent


