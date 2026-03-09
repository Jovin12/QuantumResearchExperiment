from pymongo import MongoClient

# client = MongoClient("mongodb://127.0.0.1:27017")
# these 2 do not create the collection and libraries yet, 
# the collections nad libraries are only created when you do the first write instance

# uri = "mongodb://jovin:4562FrozenLoner$%^/@@127.0.0.1:27017/?authSource=admin"

# client = MongoClient(uri)

client = MongoClient(
    host="127.0.0.1",
    port=27017,
    username="jovin",
    password="4562FrozenLoner$%^@",
    authSource="admin"  # Usually 'admin' for most setups
)

cmd_line_opts = client.admin.command("getCmdLineOpts")
print(cmd_line_opts['parsed'].get('security'))

db = client["QAdapt_DB"]
collection_config = db["IBM_configs"]
collection_user = db["users"]
collection_files = db['results_files']
collection_QuBound_file = db['QuBound_Results_files']
collection_QuCAD_file = db['QuCAD_qbank_data']
# client.admin.command('ping')
# print(client.admin.command('ping'))
