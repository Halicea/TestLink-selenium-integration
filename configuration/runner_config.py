import os
#IMPORTANT: DO NOT CHANGE THE PROJECT_PATH VARIABLE
PROJECT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#How characters are replaced
name_correction=lambda item:\
    item.replace(' ', '_')\
   .replace('-','')\
   .replace('/', '')\
   .replace(';', '')\
   .replace(':', '')\
   .replace('<>','_diff_')\
   .replace('<','_lt_')\
   .replace('>','_gt_')\
   .replace('>','_eq_')\
   .replace('\"','')\
   .replace("'",'')\
   .replace(".",'')\
   .replace("(",'_')\
   .replace(")",'')

DEFAULT_PLAN = os.path.join(PROJECT_PATH, 'testplans', 'regression.xml')

