# WQoE-RESTful-Server
A RESTful API server for web Quality-of-Experience measuring tools

## Introduction
WQoE-RESTful-Server is an RESTful API server for [An environment-independent web Quality-of-Experience measuring tool](https://github.com/ku-asteam/WQoE-Extension). It generates ID, sends ID to the measuring tool, and receives data from the measuring tool and saves them to files. The data are stored as pickle and json format.

## Requirements and Dependencies
* Python 3
* Python libraries: flask, flask_cors, json, pickle

## Instructions
* You can run the server by the command: python flask_main.py
* If you want to change port or IP address of the server, modify the last line of "flask_main.py"
