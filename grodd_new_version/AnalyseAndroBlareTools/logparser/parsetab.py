
# parsetab.py
# This file is automatically generated. Do not edit.
_tabversion = '3.8'

_lr_method = 'LALR'

_lr_signature = 'C58510D9AC32013DBCCC03C0E28BBAC4'
    
_lr_action_items = {'{':([21,],[22,]),'STRING':([9,11,13,14,15,],[10,13,15,13,15,]),'TIMESTAMP':([4,],[6,]),'}':([23,24,26,],[25,-8,-7,]),'INTEGER':([2,15,16,17,19,22,23,24,26,],[5,-4,-5,20,-6,24,26,-8,-7,]),'[':([1,7,8,],[4,-2,9,]),'$end':([3,25,],[0,-1,]),']':([6,10,],[8,11,]),'<':([0,],[2,]),'>':([5,12,18,20,],[7,14,21,-3,]),}

_lr_action = {}
for _k, _v in _lr_action_items.items():
   for _x,_y in zip(_v[0],_v[1]):
      if not _x in _lr_action:  _lr_action[_x] = {}
      _lr_action[_x][_k] = _y
del _lr_action_items

_lr_goto_items = {'container':([11,14,],[12,18,]),'level':([0,],[1,]),'flow':([22,],[23,]),'alert':([0,],[3,]),'container_name2':([13,15,],[16,16,]),'container_name':([13,15,],[17,19,]),}

_lr_goto = {}
for _k, _v in _lr_goto_items.items():
   for _x, _y in zip(_v[0], _v[1]):
       if not _x in _lr_goto: _lr_goto[_x] = {}
       _lr_goto[_x][_k] = _y
del _lr_goto_items
_lr_productions = [
  ("S' -> alert","S'",1,None,None,None),
  ('alert -> level [ TIMESTAMP ] [ STRING ] container > container > { flow }','alert',14,'p_alert','logconverter.py',146),
  ('level -> < INTEGER >','level',3,'p_level','logconverter.py',174),
  ('container -> STRING container_name INTEGER','container',3,'p_container','logconverter.py',178),
  ('container_name -> STRING','container_name',1,'p_container_name','logconverter.py',206),
  ('container_name -> container_name2','container_name',1,'p_container_name','logconverter.py',207),
  ('container_name2 -> STRING container_name','container_name2',2,'p_container_name2','logconverter.py',211),
  ('flow -> flow INTEGER','flow',2,'p_flow','logconverter.py',216),
  ('flow -> INTEGER','flow',1,'p_flow_single_lement','logconverter.py',221),
]
