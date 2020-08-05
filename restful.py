
from os import mkdir
from flask import Flask, request
from flask_restful import Resource, Api
from time import time_ns, strftime
import json

app = Flask(__name__)
api = Api(app)

class BSD(Resource):
    def get(self):
        return "Hi"
    def post(self):
        if request.json:
            reqj = request.json
            try:
                idd = reqj["playerID"]
            except KeyError:
                idd = "Unknown"
            try:
                idd = "BSDlogs/" + idd
                mkdir(idd)
            except:
                pass
            with open(idd + '/' + strftime('%Y-%m-%d-%H-%M-%S'), 'w') as jsonf:
                json.dump(request.json, jsonf)
            return {"message": "Ok"}
        else:
            return {"message": "NOk, not a valid json req"}

api.add_resource(BSD, '/')
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
