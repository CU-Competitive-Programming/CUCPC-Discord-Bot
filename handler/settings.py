import os
import json
import urllib.parse
from pymongo import MongoClient

path = os.path.dirname(os.path.realpath(__file__))

"""
these will be hardcoded until we have
a function to set everything up automatically.
for more info about the database structure check
../db
"""

username = urllib.parse.quote_plus("root")
password = urllib.parse.quote_plus("")
mongo = MongoClient("mongodb://%s:%s@localhost:27017/" % (username, password))

db = mongo["tank-game"]
s = db.settings.find_one({})

serverName = s.get("server")  # Name of server : str
matches = s.get("matches")  # Scheduled matches : dict with str keys and values str
logFile = s.get("log")  # File used for the logging : str
token = s.get("token")  # Token for the discord bot : str
compileOut = s.get("compileOut")  # Timeout for compiler
admins = s.get("admins")  # The usernames of the admins
specs = s.get("specs")  # Tournament specs
engineLink = s.get("engineLink")  # Link with info about engine
handlerUser = s.get("handlerUser")  # Username of the user that runs enviroment handler
engine = s.get("engine")  # Engine information
signup = s.get("signup")  # Get invite link

g = db.game.find_one({})  # Get game settings

print("Loaded Settings")
