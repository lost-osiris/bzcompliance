import re, inspect, sys, types
from datetime import datetime


format_string = "%Y%m%dT%H:%M:%S"
user_format = "%Y-%m-%d"
user_format_time = "%Y-%m-%dT%H:%M:%S"


def __lower(data, params):
   if type(data) is list:
      data = [str(element).lower() for element in data]
   else:
      data = str(data).lower()
   params = [str(param).lower() for param in params]
   return data, params


def __ints_only(params, name):
   for param in params:
      if not param.isdigit():
         raise Exception("%s only accept integer parameters, got %s" % (name, param))
   

def __one_param(params, name):
   if len(params) > 1:
      raise Exception("%s accepts only 1 parameter, got %d" % (name, len(params)))


def __parse_date(string):
   try:
      return datetime.strptime(string, user_format_time), True
   except:
      return datetime.strptime(string, user_format), False


def is_(data, params):
   data, params = __lower(data, params)
   return is_case(data, params)


def is_case(data, params):
   data = str(data)
   for param in params:
      if param == data:
         return True
   return False


def is_greater_than(data, params):
   data, params = __lower(data, params)
   return is_greater_than_case(data, params)


def is_greater_than_case(data, params):
   data = str(data)
   for param in params:
      if param > data:
         return True
   return False


def is_less_than(data, params):
   data, params = __lower(data, params)
   return is_less_than_case(data, params)


def is_less_than_case(data, params):
   data = str(data)
   for param in params:
      if param < data:
         return True
   return False


def is_in(data, params):
   data, params = __lower(data, params)
   return is_in_case(data, params)


def is_in_case(data, params):
   data = str(data)
   for param in params:
      if data in param:
         return True
   return False


def are_all_in(data, params):
   data, params = __lower(data, params)
   return are_all_in_case(data, params)


def are_all_in_case(data, params):
   if type(data) is not list:
      data = str(data)
   for item in data:
      if str(item) not in params:
         return False
   return True


def contains_(data, params):
   data, params = __lower(data, params)
   return contains_case(data, params)


def contains_case(data, params):
   if type(data) is not list:
      data = str(data)
   else:
      data = [str(i) for i in data]
   for param in params:
      if param in data:
         return True
   return False


def contains_all(data, params):
   data, params = __lower(data, params)
   return contains_all_case(data, params)


def contains_all_case(data, params):
   if type(data) is not list:
      data = str(data)
   else:
      data = [str(i) for i in data]
   for param in params:
      if param not in data:
         return False
   return True


def size_is(data, params):
   __ints_only(params, "SizeIs")
   return str(len(data)) in params


def size_at_least(data, params):
   __ints_only(params, "SizeAtLeast")
   for param in params:
      if str(len(data)) >= int(param):
         return True
   return False


def size_at_most(data, params):
   __ints_only(params, "SizeAtMost")
   for param in params:
      if str(len(data)) <= int(param):
         return True
   return False


def date_is(data, params):
   data = datetime.strptime(data, format_string)
   for param in params:
      dt, use_time = __parse_date(param)
      if use_time and data == dt:
         return True
      elif not use_time and data.date() == dt.date():
         return True
   return False


def date_at_least(data, params):
   data = datetime.strptime(data, format_string)
   for param in params:
      dt, use_time = __parse_date(param)
      if use_time and data >= dt:
         return True
      elif not use_time and data.date() >= dt.date():
         return True
   return False


def date_at_most(data, params):
   data = datetime.strptime(data, format_string)
   for param in params:
      dt, use_time = __parse_date(param)
      if use_time and data <= dt:
         return True
      elif not use_time and data.date() <= dt.date():
         return True
   return False


def date_is_format(data, params):
   data = datetime.strptime(data, params[0])
   for param in params[1:]:
      dt, use_time = __parse_date(param)
      if use_time and data == dt:
         return True
      elif not use_time and data.date() == dt.date():
         return True
   return False


def date_at_least_format(data, params):
   data = datetime.strptime(data, params[0])
   for param in params[1:]:
      dt, use_time = __parse_date(param)
      if use_time and data >= dt:
         return True
      elif not use_time and data.date() >= dt.date():
         return True
   return False


def date_at_most_format(data, params):
   data = datetime.strptime(data, params[0])
   for param in params[1:]:
      dt, use_time = __parse_date(param)
      if use_time and data <= dt:
         return True
      elif not use_time and data.date() <= dt.date():
         return True
   return False


def has_field(data, params):
   __one_param(params, "HasField")
   try:
      data[params[0]]
   except:
      return False
   return True


def regex(data, params):
   for param in params:
      regex = re.compile(param)
      if re.search(regex, str(data)):
         return True
   return False


#Populate function map
func_map = {}
for member in inspect.getmembers(sys.modules[__name__]):
   if not member[0].startswith("_") and type(member[1]) is types.FunctionType:
      func_map[member[0].replace("_", "").lower()] = member[1]
      
      