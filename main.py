import webapp2
from google.appengine.ext import ndb
import json
import datetime
from types import *
import sys

methods = set(webapp2.WSGIApplication.allowed_methods)
methods.add('PATCH')
webapp2.WSGIApplication.allowed_methods = frozenset(methods)

#boat model
class Boat (ndb.Model):
	name = ndb.StringProperty(required=True)
	type = ndb.StringProperty(required=True)
	length = ndb.IntegerProperty(required=True)
	at_sea = ndb.BooleanProperty()
	id = ndb.StringProperty()

#slip model
class Slip (ndb.Model):
	number = ndb.IntegerProperty(required=True)
	current_boat = ndb.StringProperty()
	arrival_date = ndb.StringProperty()
	id = ndb.StringProperty()

#history of boats model
class HistoryBoat(ndb.Model):
	name = ndb.StringProperty(required=True)
	type = ndb.StringProperty(required=True)
	length = ndb.IntegerProperty(required=True)
	at_sea = ndb.BooleanProperty()
	id = ndb.StringProperty()
	slip_number = ndb.IntegerProperty()

#check if argument is integer
def intCheck(length):
	if (type(length) is not IntType):
		return False
	else:
		return True

#check if argument is string
def stringCheck(string):
	if (type(string) is not UnicodeType):
		return False
	else:
		return True

#check if argument is bool
def boolCheck(value):
	if (type(value) is not BooleanType):
		return False
	else:
		return True

#setup bad request error message
def badRequest(self, message):
	self.response.status = "400 Bad Request"
	self.response.write(message)
	return

#check if all variables in request body is valid
def checkRequestBody(self, data):
	if ('name' in data):
		if (not stringCheck(data['name'])):
			badRequest(self, "Error: name should be a string")
			return False
	if ('type' in data):
		if (not stringCheck(data['type'])):
			badRequest(self, "Error: type should be a string")
			return False
	if ('length' in data):
		if (not intCheck(data['length'])):
			badRequest(self, "Error: length should be integer")
			return False
	if ('at_sea' in data):
		if (not boolCheck(data['at_sea'])):
			badRequest(self, "Error: at_sea should be boolean")
			return False
	if ('number' in data):
		if (not intCheck(data['number'])):
			badRequest(self, "Error: number should be integer")
			return False
	if ('current_boat' in data):
		if (not stringCheck(data['current_boat'])):
			badRequest(self, "Error: current_boat should be a string")
			return False
	if ('arrival_date' in data):
		if (not stringCheck(data['arrival_date'])):
			badRequest(self, "Error: arrival_date should be a string")
			return False
	return True


class BoatHandler(webapp2.RequestHandler):
	#create a new boat
	def post(self):
		boat_data = json.loads(self.request.body)
		#check if all required variables of Boat are presented in request body
		#if name, type or length is not sent, return with error
		if ('name' not in boat_data) or ('length' not in boat_data) or ('type' not in boat_data): 
			badRequest(self, "Error: name, type and length are required")
			return

		#check if request body is valid
		if (not checkRequestBody(self, boat_data)):
			return

		#check for at_sea, all new boat starts with at_sea = true
		#if at_sea is given to be false, return with error
		if ('at_sea' in boat_data):
			if (not boat_data['at_sea']):
				badRequest(self, "Error: All new boat starts at sea")
				return

		#no possible errors detected, create new boat 
		new_boat = Boat(name=boat_data['name'], type=boat_data['type'], length=boat_data['length'], at_sea=True)

		new_boat.put()
		new_boat.id = str(new_boat.key.urlsafe())
		new_boat.put()
		boat_dict = new_boat.to_dict()
		boat_dict['self'] = "/boats/" + new_boat.id
		self.response.write(json.dumps(boat_dict))

	#delete all boats
	def delete(self):		
		boat_query_objects = ndb.gql("SELECT * FROM Boat")

		for boat_query in boat_query_objects:
			boat_key = ndb.Key(urlsafe=boat_query.key.urlsafe())
			boat = boat_key.get()

			#create a new HistoryBoat object
			history_boat = HistoryBoat(name=boat.name, type=boat.type, length=boat.length, id=boat.id, at_sea=boat.at_sea)

			#check if boat is at slip, if yes, empty slip
			if (boat.at_sea == False):
				slip_query_object = Slip.query(Slip.current_boat == boat.id)
				for slip_query in slip_query_object:
					slip_key = ndb.Key(urlsafe=slip_query.key.urlsafe())
					slip = slip_key.get()
					history_boat.slip_number = slip.number
					slip.current_boat = None
					slip.arrival_date = None
					slip.put()

			history_boat.put()
			boat.key.delete()
			
	#get all boat entities
	def get(self):
		boat_query_objects = ndb.gql("SELECT * FROM Boat")
		boats = []
		for boat_query in boat_query_objects:
			boat = boat_query.to_dict()
			boat['self'] = "/boats/" + boat['id']
			boats.append(boat)
		self.response.write(json.dumps(boats))

class SingleBoatHandler(webapp2.RequestHandler):
	#get a boat
	def get(self, *args, **kwargs):
		try:
			boat_key = ndb.Key(urlsafe=args[0])
			boat = boat_key.get()
			boat_dict = boat.to_dict()
			boat_dict['self'] = "/boats/" + boat.id
			self.response.write(json.dumps(boat.to_dict()))
		except (Exception):
			badRequest(self, "Error: Invalid boatID")
			return

	#delete a boat, add boat to history boat list, clear slip boat is currently in
	def delete(self, *args, **kwargs):
		try:
			#get boat to be deleted
			boat_key = ndb.Key(urlsafe=args[0])
			boat = boat_key.get()

			#create a new HistoryBoat object
			history_boat = HistoryBoat(name=boat.name, type=boat.type, length=boat.length, id=boat.id, at_sea=boat.at_sea)

			#check if boat is at_sea
			if (boat.at_sea == False):
				#get slip number using query
				slip_query_object = Slip.query(Slip.current_boat == boat.id)
				#empty the slip where the boat is
				if (slip_query_object.count() > 0):
					for slip_query in slip_query_object:
						slip_key = ndb.Key(urlsafe=slip_query.key.urlsafe())
						slip = slip_key.get()
						history_boat.slip_number = slip.number
						slip.current_boat = None
						slip.arrival_date = None
						slip.put()
			history_boat.put()
			boat.key.delete()
		except (Exception):
			badRequest(self, "Error: Invalid boatID")
			return

	#modify boat's data - changing name, type, length or setting boat to At Sea
	def put(self, *args, **kwargs):
		try:
			#get boat we are modifying
			boat_key = ndb.Key(urlsafe=args[0])
			boat_data = boat_key.get()
			boat_new_data = json.loads(self.request.body)

			#check for valid request body
			if (not checkRequestBody(self, boat_new_data)):
				return

			#update name, length, or type where appropriate
			if ('name' in boat_new_data):
				boat_data.name = boat_new_data['name']
			if ('type' in boat_new_data):
				boat_data.type = boat_new_data['type']
			if ('length' in boat_new_data):
				boat_data.length = boat_new_data['length']

			#set boat's at_sea if at_sea is set in request body
			if ('at_sea' in boat_new_data):
				#setting boat to at sea
				if (boat_new_data['at_sea'] == True):
					#get occupied slip and empty slip
					slip_query_object = Slip.query(Slip.current_boat == boat_data.id)
					if (slip_query_object.count() > 0):
						for slip_query in slip_query_object:
							slip_key = ndb.Key(urlsafe=slip_query.key.urlsafe())
							slip = slip_key.get()
							slip.current_boat = None
							slip.arrival_date = None
							slip.put()
					boat_data.at_sea = boat_new_data['at_sea']
				else:
					badRequest(self, "Error: Invalid setting of boat to slip")
					return

			boat_data.put()
			boat_dict = boat_data.to_dict()
			boat_dict['self'] = "/boats/" + boat_data.id
			self.response.write(json.dumps(boat_dict))

		except (Exception):
			badRequest(self, "Error: Invalid boatID")
			return

	#replace a boat
	def patch(self, *args, **kwargs):
		try:
			#get boat to replace from datastore
			boat_key = ndb.Key(urlsafe=args[0])
			boat_data = boat_key.get()

			#get information of new boat
			new_boat_data = json.loads(self.request.body)

			#check if all required information (name, type, length) is present
			if ('name' not in new_boat_data) or ('length' not in new_boat_data) or ('type' not in new_boat_data): 
				badRequest(self, "Error: name, type and length are required")
				return

			#check if request body is all valid
			if (not checkRequestBody(self, new_boat_data)):
				return

			#check for at_sea, all new boat starts with at_sea = true
			#if at_sea is given to be false, return with error
			if ('at_sea' in new_boat_data):
				if (not new_boat_data['at_sea']):
					badRequest(self, "Error: All new boat starts at sea")
					return

			#replace boat information with new information
			boat_data.name = new_boat_data['name']
			boat_data.type = new_boat_data['type']
			boat_data.length = new_boat_data['length']
			boat_data.at_sea = True

			#put boat with new information into datastore
			boat_data.put()
			boat_dict = boat_data.to_dict()
			boat_dict['self'] = "/boats/" + boat_data.id
			self.response.write(json.dumps(boat_dict))

		except (Exception):
			badRequest(self, "Error: Invalid boatID")
			return

class SlipHandler(webapp2.RequestHandler):
	#create a new slip
	def post(self):
		slip_data = json.loads(self.request.body)

		#check if request body is all valid
		if (not checkRequestBody(self, slip_data)):
			return

		#check if request boy contain number
		if ('number' not in slip_data):
			badRequest(self, "Error: number is required")
			return

		#check if request body contain current_boat information
		#return error if yes because all new slip starts with empty
		if ('current_boat' in slip_data) or ('arrival_date' in slip_data):
			badRequest(self, "Error: All new slip should be empty")
			return

		#check if slip with the same number already exists. if yes, return error
		slip_number = str(slip_data['number'])
		slip_exist = ndb.gql("SELECT * FROM Slip WHERE number = " + slip_number)
		if (slip_exist.count() > 0):
			badRequest(self, "Error: Slip number has to be unique")
			return

		#if slip does not exists yet, create new slip
		else:
			new_slip = Slip(number=slip_data['number'])
			new_slip.put()
			new_slip.id = str(new_slip.key.urlsafe())
			new_slip.put()
			slip_dict = new_slip.to_dict()

			#create a link to itself
			slip_dict['self'] = "/slips/" + new_slip.id
			self.response.write(json.dumps(slip_dict))
			
	#get all slip entities
	def get(self):
		slip_query_object = ndb.gql("SELECT * FROM Slip")
		slips = []
		for slip_query in slip_query_object:
			slip = slip_query.to_dict()
			slip['self'] = "/slips/" + slip['id']
			current_boat_id = slip['current_boat']
			if (current_boat_id is not None):
				slip['current_boat_url'] = "/boats/" + current_boat_id
			slips.append(slip)
		self.response.write(json.dumps(slips))

	#delete all slip entities
	def delete(self):
		slip_query_object = ndb.gql("SELECT * FROM Slip")
		for slip_query in slip_query_object:
			slip_key = ndb.Key(urlsafe=slip_query.key.urlsafe())
			slip = slip_key.get()
			#check if any boat is currently occupying the slip to be deleted, if yes, set boat to at_sea
			if (slip.current_boat is not None):
				boat_key = ndb.Key(urlsafe=slip.current_boat)
				boat = boat_key.get()
				boat.at_sea = True
				boat.put()
			#delete slip
			slip.key.delete()

class SingleSlipHandler(webapp2.RequestHandler):
	#get a single slip
	def get(self, *args, **kwargs):
		try:
			slip_key = ndb.Key(urlsafe=args[0])
			slip = slip_key.get()
			slip_dict = slip.to_dict()
			slip_dict['self'] = "/slips/" + slip.id
			current_boat_id = slip_dict['current_boat']
			if (current_boat_id is not None):
				slip_dict['current_boat_url'] = "/boats/" + current_boat_id
			self.response.write(json.dumps(slip_dict))
		except (Exception):
			badRequest(self, "Error: Invalid slipID")
			return

	#delete a single slip
	def delete(self, *args, **kwargs):
		try:
			slip_key = ndb.Key(urlsafe=args[0])
			slip = slip_key.get()
			boats = []
			if (slip.current_boat is not None):
				boat_query_objects = Boat.query(Boat.id == slip.current_boat)
				if (boat_query_objects.count() > 0):
					for boat_query in boat_query_objects:
						boat = boat_query.to_dict()
						boat['at_sea'] = True
						boat.put()
						boats.append(boat)
			self.response.write(json.dumps(boats))
			slip.key.delete()

		except (Exception):
			badRequest(self, "Error: Invalid slipID")
			return

	#modify a slip, change slip information, assign a boat to slip
	def put(self, *args, **kwargs):	
		try:
			#get slip	
			slip_key = ndb.Key(urlsafe=args[0])
			slip = slip_key.get()

			#get new slip's information and validate new slip's information
			new_data = json.loads(self.request.body)
			if (not checkRequestBody(self, new_data)):
				return

			#update slip's number
			if ('number' in new_data):
				#first check if number is already in used
				#if yes, print out error message and return
				#if no, update slip's number
				slip_query_object = Slip.query(Slip.number == new_data['number'])
				if (slip_query_object.count() > 0):
					badRequest(self, "Error: Slip number should be unique")
					return
				else:
					slip.number = new_data['number']

			#update slip's current_boat information i.e. assign boat to slip
			if ('current_boat' in new_data):
				#check if slip is currently occupied by another boat
				#if slip is occupied, return with error
				#if not, assigned boat to current slip
				if (slip.current_boat is not None):
					self.response.status = "403 Forbidden Message"
					self.response.write("Error 403 Forbidden Message")
					return
				else:
					slip.current_boat = new_data['current_boat']
					#update boat's at_sea status to false
					boat_key = ndb.Key(urlsafe=slip.current_boat)
					boat = boat_key.get()
					boat.at_sea = False
					boat.put()

			#update slip's arrival_date
			if ('arrival_date' in new_data):
				slip.arrival_date = str(new_data['arrival_date'])

			slip.put()

			#create a self link
			slip_dict = slip.to_dict()
			slip_dict['self'] = "/slips/" + slip.id

			#create a url link to current_boat 
			if (slip.current_boat is not None):
				slip_dict['current_boat_url'] = "/boats/" + slip.id
				
			self.response.write(json.dumps(slip_dict))
		except (Exception):
			badRequest(self, "Error: Invalid slipID")
			return

	#replace a slip - only allow the changing the of slip number
	#if slip is occupied, the new slip will be occupied by the same boat
	def patch(self, *args, **kwargs):
		try:
			#get new slip data and validate data
			new_slip_data = json.loads(self.request.body)
			if (not checkRequestBody(self, new_slip_data)):
				return

			#number is required
			if ('number' not in new_slip_data):
				badRequest(self, "Error: number is required")
				return

			#if current_boat and arrival_date are provided, return with error
			if ('current_boat' in new_slip_data) or ('arrival_date' in new_slip_data):
				badRequest(self, "Error: Invalid replacement")
				return

			#check if number is unique
			slip_number = str(new_slip_data['number'])
			slip_exist = ndb.gql("SELECT * FROM Slip WHERE number = " + slip_number)
			if (slip_exist.count() > 0):
				badRequest(self, "Error: Slip number should be unique")
				return

			else:
				#get old slip we are replacing
				slip_key = ndb.Key(urlsafe=args[0])
				slip = slip_key.get()

				#replace information of old slip to new slip
				slip.number = new_slip_data['number']
				slip.put()

				#create self link and link to boat if slip is not empty
				slip_dict = slip.to_dict()
				slip_dict['self'] = "/slips/" + slip.id
				if (slip_dict['current_boat'] is not None):
					slip_dict['current_boat_url'] = "/boats/" + slip_dict['current_boat']
				self.response.write(json.dumps(slip_dict))

		except (Exception):
			badRequest(self, "Error: Invalid slipID")
			return

#print out boat currently in slip
#if not boat is at this slip, return empty list
#else return boat information
class BoatInSlipHandler(webapp2.RequestHandler):
	def get(self, *args, **kwargs):
		try:
			slip_key = ndb.Key(urlsafe=args[0])
			slip = slip_key.get()
			boats = []
			if (slip.current_boat is not None):
				boat_key = ndb.Key(urlsafe=slip.current_boat)
				boat = boat_key.get()
				boat_dict = boat.to_dict()
				boat_dict['self'] = "/boats/" + boat.id
				boats.append(boat_dict)
			self.response.write(json.dumps(boats))
			
		except (Exception):
			badRequest(self, "Error: Invalid slipID")
			return

class BoatHistoryHandler(webapp2.RequestHandler):
	#display a list of boats deleted
	def get(self):
		boat_query_objects = ndb.gql("SELECT * FROM HistoryBoat")
		history = []
		for boat_query in boat_query_objects:
			boat_key = ndb.Key(urlsafe=boat_query.key.urlsafe())
			boat = boat_key.get()
			history.append(boat.to_dict())
		self.response.write(json.dumps(history))

	#clear history list
	def delete(self):
		boat_query_objects = ndb.gql("SELECT * FROM HistoryBoat")
		for boat_query in boat_query_objects:
			boat_key = ndb.Key(urlsafe=boat_query.key.urlsafe())
			boat = boat_key.get() 
			boat.key.delete()

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Hello World')


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/boats', BoatHandler),
    ('/boats/history', BoatHistoryHandler),
    ('/boats/(.*)', SingleBoatHandler),
    ('/slips', SlipHandler),
    ('/slips/(.*)/boats', BoatInSlipHandler),
    ('/slips/(.*)', SingleSlipHandler), 
], debug=True)
