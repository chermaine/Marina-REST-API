# Marina-REST-API

REST API planning and implementation that model a simple marina with boats and slips (parking spots for boats). Boats can either be "at sea" or they can be currently in a slip. Slips can be assigned to multiple boats but only one boat can be at one slip at the same time. 

# Entities and Properties:
Boat {
  "id": string
  "name": string
  "type": string
  "length": integer
  "at_sea": boolean
 }
 
 Slip {
  "id": string
  "number": integer
  "current_boat": string
  "arrival_data": string
 }
 
 # Supported Functions:
 - add, delete, modify, replace and view Boats and Slips entities
 - setting a boat to "at sea" will empty the slip the boat is occupying
 - boat arrival can be assigned to an empty slip
 
 # API Documentation:
 Refer to API pdf
