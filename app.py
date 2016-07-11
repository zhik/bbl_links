from flask import Flask, jsonify, abort, url_for
from BeautifulSoup import BeautifulSoup
from flask_cors import CORS, cross_origin
from datetime import datetime, date
import time
import json
from geojson import MultiPoint
import requests
import sqlite3
import os 

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

conn = sqlite3.connect('location.db',check_same_thread=False)
db = conn.cursor()

db.execute('''
	CREATE TABLE IF NOT EXISTS location (
	bbl TEXT,
	lat TEXT,
	lng TEXT,
	time_stamp TEXT
	)
	''')
conn.commit()

def findlatlong(bbl):
	bbl = list(bbl)
	boro = bbl[0]
	block = ''.join(bbl[1:6])
	lot = ''.join(bbl[6:10])
	try:
		url = "http://a030-goat.nyc.gov/goat/bl.aspx?boro="+ boro +"&block_num="+ block +"&lot_num=" + lot
		r = requests.get(url)
		soup = BeautifulSoup(r.text)
		lotloc = soup.find(id="label_f1a_lat_long").getText().split()
	except:
		return ['0', '', '0']
	else:
		return lotloc


def create(bbl, lotloc):
	lat = lotloc[0] 
	lng = lotloc[2]
	unix = time.time()
	date = str(datetime.fromtimestamp(unix).strftime('%Y-%m-%d %H:%M:%S'))
	db.execute('''
		INSERT INTO location(bbl, lat, lng, time_stamp) VALUES(?, ?, ?, ?)
		''', (bbl, lat, lng, date))
	conn.commit()


# def converttounix(date_str):
# 	#date_str = "2016-07-07 16:09:28"
# 	time_tuple = time.strptime(date_str, "%Y-%m-%d %H:%M:%S")
# 	#float
# 	return repr(time.mktime(time_tuple))


# @app.route('/mapdata', methods=['GET'])
# def mapdata():
# 	db.execute('SELECT * FROM location')

# 	longlatlist = []
# 	timestamplist = []
# 	for row in db.fetchall():
# 		longlatlist.append((float(row[2]) , float(row[1])))
# 		timestamplist.append(converttounix(row[3]))

# 	return jsonify(MultiPoint(longlatlist , properties={"time": timestamplist}))

# @app.route('/')
# @cross_origin()
# def index():
# 	return render_template('index.html')


@app.route('/location/<string:bbl>', methods=['GET'])
@cross_origin()
def location(bbl):
	if len(bbl) != 10:
		abort(404)
	db.execute('''SELECT * FROM location WHERE bbl=?''', (bbl,))
	if db.fetchone():
		print(bbl, "found")
		for i in db.execute('''SELECT * FROM location WHERE bbl=?''', (bbl,)):
			lat = i[1]
			lng = i[2]
		return jsonify({'lat': lat, 'lng': lng})
	else:
		lotloc = findlatlong(bbl)
		create(bbl, lotloc)
		for i in db.execute('''SELECT * FROM location WHERE bbl=?''', (bbl,)):
			lat = i[1]
			lng = i[2]
			time_stamp = i[3]
		print(bbl, "not found, creating a new one", time_stamp)
		return jsonify({'lat': lat, 'lng': lng})

if __name__ == '__main__':
    app.run(debug='True')