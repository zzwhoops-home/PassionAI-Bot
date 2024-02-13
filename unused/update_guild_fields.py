import pymongo

from dotenv import load_dotenv
import os

# load env variables
load_dotenv()
MONGO_USER = os.getenv('USER')
MONGO_PWD = os.getenv('PWD')

client = pymongo.MongoClient(f"mongodb+srv://{MONGO_USER}:{MONGO_PWD}@passionaibot.4dwr2me.mongodb.net/?retryWrites=true&w=majority")
db = client['PassionAIDB']

chat_history = db['chat_history']

chat_history.update_many({
    'guild_id': "1074091124114866186",
    'guild_name': "Passion AI"
},
{ 
    '$set': {
        'guild_id': 1074091124114866186,
        'guild_name': 'Passion AI'
    }
})