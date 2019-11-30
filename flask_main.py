from flask import Flask, abort, render_template, request
from flask_cors import CORS
import traceback
import json
import random
import pickle
from datetime import datetime

THRESHOLD_LOADS = 100
worker_json_data = dict()

app = Flask(__name__)
CORS(app)

FILENAME_DB = "db/worker.pkl"
db_lastupdate_time = datetime.now()

def isValidId(workerID):
    if workerID == "":
        return False
    
    if workerID not in worker_json_data:
        generateDataById(workerID)
    
    checkDone(workerID)
    return True
    
    
def generateDataById(workerID):
    worker_json_data[workerID] = {
        'loads': 0,
        'loadsM': 0,
        'loadsP': 0,
        'generatedTime': datetime.now(),
        'surveyKey': "",
    }


def checkDone(workerID):
    timedelta = datetime.now() - worker_json_data[workerID]['generatedTime']
    if timedelta.days >= 6:
        generateSurveyKey(workerID)
    

def generateSurveyKey(workerID):
    worker_json_data[workerID]['surveyKey'] = random.randint(1000000, 9999999)
    updateDB()
    
    
def updateDB():
    global db_lastupdate_time
    
    # DB 업데이트
    pickle.dump(worker_json_data, open(FILENAME_DB, "wb"))
    
    # DB 백업
    db_timedelta = datetime.now() - db_lastupdate_time
    if db_timedelta.seconds > 3600: # 1 hours
        try:
            pickle.dump(worker_json_data, open(FILENAME_DB + ".backup-%s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "wb"))
            db_lastupdate_time = datetime.now()
        except Exception as e:
            print(e)
    

def updateDataById(workerID, data):
    worker_json_data[workerID]['loads'] += len(data['pageDataList'])
    if "Android" in data['user-agent']: # Android
        worker_json_data[workerID]['loadsM'] += len(data['pageDataList'])
    else:
        # Windows or something else
        worker_json_data[workerID]['loadsP'] += len(data['pageDataList'])
    
    updateDB()
    

def getNumberOfData(workerID):
    return (worker_json_data[workerID]["loadsP"], worker_json_data[workerID]["loadsM"])

def getSurveyKeyMsg(workerID):
    tmp_str = ""
    
    if worker_json_data[workerID]['surveyKey'] == "":
        tmp_str = "(The key will appear here)"
    else:
        tmp_str = worker_json_data[workerID]['surveyKey']
    
    return tmp_str

@app.route("/")
def helloWorld():
    return "Hello!!!"



@app.route("/data", methods=['POST'])
def handle_data():
    data = request.get_json()
    try:
        workerID = data['workerID'].lower() # ALWAYS LOWER

        num_keys = len(data['pageDataList'])
        print("NUM " + str(num_keys))
        print("KEYS" + str(list(data.keys())))
        
        print(request.user_agent)
        data['user-agent'] = request.user_agent.string
        
        # 데이터 저장!
        filename = datetime.now().strftime('data/%Y-%m-%d %H:%M:%S-' + workerID + '.log')
        with open(filename, 'w') as f:
            json.dump(data, f, sort_keys=True, indent=2, separators=(',', ': '))


        # 가공 및 DB 작성
        if not isValidId(workerID):
            return '{"result": "done", "len": %d}' % num_keys
        updateDataById(workerID, data)
            
        return '{"result": "done", "len": %d}' % worker_json_data[workerID]['loads']
        
    except Exception:
        print("에러 발생!")
        print(traceback.print_exc())
        return '{"result": "fail", "len": -1}'
    

@app.route("/msgs", methods=['GET'])
def handle_loads():
    workerID = request.args.get('id').lower() # ALWAYS LOWER
    
    isValid = "False"
    msg1, msg2, msg3 = "", "", ""
    if isValidId(workerID):
        isValid = "True"
        msg1 = "Survey Code: %s" % getSurveyKeyMsg(workerID)
        msg2 = "The number of data (PC): %d<br>The number of data (Mobile): %d" % getNumberOfData(workerID)
        msg3 = "Thank you for your participation!"
    return '{"isValid": "%s", "msg1": "%s", "msg2": "%s", "msg3": "%s"}' % (isValid, msg1, msg2, msg3)


# Deprecated
@app.route("/surveyKey", methods=['GET'])
def handle_surveykey():
    workerID = request.args.get('id')
    print(workerID)
    if workerID == "" or workerID not in worker_json_data:
        return '{"isValid": "False", "done": "False", "surveyKey": ""}'
    else:
        return '{"isValid": "True", "done": "%s", "surveyKey": "%s"}' % (worker_json_data[workerID]['done'], worker_json_data[workerID]['surveyKey'])


if __name__ == "__main__":
    try:
        worker_json_data = pickle.load(open(FILENAME_DB, "rb"))
    except Exception as e:
        print(e)
        pickle.dump(worker_json_data, open(FILENAME_DB, "wb"))
        
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)