from flask import Flask, request, jsonify
import mysql.connector
import requests
#from requests.structures import CaseInsensitiveDict
import json

from urllib.parse import urlencode
app = Flask(__name__)
# Define MySQL connection details
db_config = {
    'host': 'Sustainability.mysql.pythonanywhere-services.com',
    'user': 'Sustainability',
    'password': 'Verofax123',
    'database': 'Sustainability$default'
}

# Route to get data from MySQL and calculate carbon emission
@app.route('/calculate', methods=['GET'])
def calculate():
    req=request.json
    #percentage = req['raw material percentage']
    #material = req['raw material']
    weight = req['product weight']/1000
    data = request.get_json()
    total=raw(data,weight)
    # Return the processed items as a JSON response
    response = {
            'emission': str(total) + ' kg CO2e'
              }
    return jsonify(response)


def raw(data,weight):
    if 'raw material' in data and 'raw material percentage' in data:
        raw_material_array = data['raw material']
        percentage_array = data['raw material percentage']

        # Calculate total emission based on raw material percentages
        tot_result = 0

        # Iterate through each raw material and its percentage
        for i in range(len(raw_material_array)):
            raw_material = raw_material_array[i]
            percentage = percentage_array[i]

            # Perform calculations based on the provided parameters
            result = perform_calculation(percentage, raw_material, weight)
            tot_result += result
        return tot_result


def perform_calculation(percentage, material, weight):
    try:
        conn = mysql.connector.connect(**db_config)
        # Execute SQL query
        cursor = conn.cursor()
        query = 'SELECT Carbon_Emission FROM raw_material where Fibres=%s'
        val=(material,)
        cursor.execute(query,val)

        # Fetch data from query results
        data = cursor.fetchone()[0]

        # Close MySQL connection
        conn.close()

    except Exception as e:
        # Handle errors
        return str(e)

    emission=float(data)*((percentage/100)*weight)

    return emission


#Packaging material
@app.route('/packmaterial', methods=['GET'])
def calc_pack():
    req=request.json
    pack_material = req['packaging material']
    weight = req['packaging material weight(g)']/1000
    # Perform calculations based on the provided parameters
    result = packaging_calculation(pack_material, weight)
    # Prepare the response
    response = {
        'emission': str(result)+' kg CO2e'
    }

    # Return the response as JSON
    return jsonify(response)

def packaging_calculation(pack_material, pack_weight):
    try:
        conn = mysql.connector.connect(**db_config)
        # Execute SQL query
        cursor = conn.cursor()
        query = 'SELECT Carbon_Emission FROM packaging where Material=%s'
        val=(pack_material,)
        cursor.execute(query,val)

        # Fetch data from query results
        data = cursor.fetchone()[0]

        # Close MySQL connection
        conn.close()

    except Exception as e:
        # Handle errors
        return str(e)

    emission=float(data)*pack_weight

    return emission


#Total Carbon Footprint
@app.route('/total', methods=['GET'])
def total_carbon():
    req=request.json
    #percentage = req['raw material percentage']
    #material = req['raw material']
    pack_material = req['packaging material']
    weight = req['product weight']/1000
    pack_weight = req['packaging material weight']/1000
    data = request.get_json()
    result1 = raw(data,weight)
    result2 = packaging_calculation(pack_material, pack_weight)
    result3 = calculate_emissions1()
    tot_result= float(result1 + result2 + result3)
    # Prepare the response
    response = {
        'Emission due to raw materials': str(result1)+' kg CO2e',
        'Emission due to packaging': str(result2)+' kg CO2e',
        'Emission due to transport': str(result3)+' kg CO2e',
        'Carbon Footprint': str(tot_result)+' kg CO2e'
    }

    # Return the response as JSON
    return jsonify(response)


#transportation
#@app.route('/transportation', methods=['GET'])

def get_route(origin,destination,fuel,fuel_eff,weight):
    distance_f=get_distance(origin,destination)
    fuel_con = distance_f/fuel_eff
    result=trans_emission(fuel,fuel_con,weight)
    # Prepare the response
    # Return the response as JSON
    #return jsonify(response)
    return distance_f,result

def get_distance(origin,destination):
    api_key = "AIzaSyDY2q838pzjH8n2Ib1Q2FwkkRcHLiUnVD8"  # Replace with your Google Maps API key

    base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": origin,
        "destinations": destination,
        "mode": "driving",
        "avoid" : "indoor",
        "key": api_key
    }
    url = base_url + "?" + urlencode(params)
    response = requests.get(url)
    data = response.json()
    distance1 = data['rows'][0]['elements'][0]['distance']['text']
    distance2 = distance1.replace(' km', '')
    distance3 = distance2.replace(',','')
    return float(distance3)

#print(get_distance("dubai","sharjah"))
#method 1(driving & airways)
def trans_emission(fuel,fuel_con,weight):
    try:
        conn = mysql.connector.connect(**db_config)
        # Execute SQL query
        cursor = conn.cursor()
        query = 'SELECT Carbon_Emission FROM fuel_type where fuel=%s'
        val=(fuel,)
        cursor.execute(query,val)

        # Fetch data from query results in CO2/L
        data = cursor.fetchone()[0]

        # Close MySQL connection
        conn.close()

    except Exception as e:
        # Handle errors
        return str(e)

    emission=float(data)*fuel_con*weight

    return emission
#print(drive_car("diesel",22))

#method 2(driving truck)
'''def car_emission(distance,weight):
    emission= 0.000105*weight*distance
    return emission'''

#@app.route('/air', methods=['GET'])
def air(origin,destination,weight,mode):

    srcair=get_airport(origin)
    destair=get_airport(destination)
    air=get_distance_air(srcair,destair)
    # Return the processed items as a JSON response
    #fuel_con =air/fuel_eff
    result=og_trans(weight,air,mode)

    return air,result

#testing
'''@app.route('/airr', methods=['GET'])
def airr():
    req=request.json
    dest = req['Destination']
    src = req['Source']
    destair=get_airport(dest)
    srcair=get_airport(src)
    fuel =  req['fuel type']
    fuel_eff = req['fuel efficiency(km/L)']
    air=get_distance_air(srcair,destair)
    # Return the processed items as a JSON response
    fuel_con = air/fuel_eff
    result=trans_emission(fuel,fuel_con)
    response = {
            'source' : src,
            'destination' : dest,
            'source airport' : srcair,
            'destination airport' : destair,
            'emission': str(result) + ' kg CO2e'
              }
    return jsonify(response)'''

#@app.route("/calculate_emissions1", methods=["GET"])
#method 1(air)
def og_trans(weight,distance,mode):
    url = "https://www.carboninterface.com/api/v1/estimates"
    headers = {
        "Authorization": "Bearer Eq8vmxlGJFDQJWlxXPb5A",
        "Content-Type": "application/json"
    }
    payload = {
        "type": "shipping",
        "weight_value": weight,
        "weight_unit": "g",
        "distance_value": distance,
        "distance_unit": "km",
        "transport_method": mode
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    carbon_trans=response.json()["data"]["attributes"]["carbon_kg"]
    return float(carbon_trans)


def get_airport(loct):
    url = "https://aerodatabox.p.rapidapi.com/airports/search/term"

    querystring = {"q":loct,"limit":"1"}

    headers = {
    	"X-RapidAPI-Key": "0415826886mshdf48ecaa59963c6p14dc9bjsn17f920f10499",
    	"X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    dat=response.json()
    airp=dat['items'][0]['iata']
    return airp
#end of testing

def get_distance_air(src,dest):
    typ="iata"
    url = "https://aerodatabox.p.rapidapi.com/airports/{ty}/{source}/distance-time/{destination}".format(ty=typ,source=src,destination=dest)
    headers = {
        	"X-RapidAPI-Key": "0415826886mshdf48ecaa59963c6p14dc9bjsn17f920f10499",
        	"X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"}

    response = requests.get(url, headers=headers)
    data=response.json()
    air_dist=data['greatCircleDistance']['km']
    return air_dist


@app.route("/calculate_emissions", methods=["GET"])
def calculate_emissions():
    # Get the route data from the request body
    data = request.get_json()
    weight = (data['product weight'])
    # Retrieve the routes and additional parameters from the JSON payload
    routes = data.get('routes', [])


    # Iterate over each route in the data
    results = []
    for route in routes:
        origin = route['origin']
        destination = route['destination']
        mode = route['mode']
        fuel =  route['fuel type']
        fuel_eff = route['fuel efficiency(km/L)']

        # Calculate the route distance and emissions using Openrouteservice API
        if mode == "driving":
            distance, emissions = get_route(origin,destination,fuel,fuel_eff,(weight/1000))
        elif mode == "plane":
            distance, emissions = air(origin,destination,weight,mode)

        # Build the result object
        result = {
            'origin': origin,
            'destination': destination,
            'mode': mode,
            'distance': distance,
            'emissions': emissions
        }

        results.append(result)



    tot = sum(result.get('emissions', 0) for result in results)
    response = {
            'results' : results,
            'Carbon Emission' : str(tot) + ' Kg CO2e'

    }
    return jsonify(response)

def calculate_emissions1():
    # Get the route data from the request body
    data = request.get_json()
    weight = (data['product weight'])
    # Retrieve the routes and additional parameters from the JSON payload
    routes = data.get('routes', [])
    # Iterate over each route in the data
    results = []
    for route in routes:
        origin = route['origin']
        destination = route['destination']
        mode = route['mode']
        fuel =  route['fuel type']
        fuel_eff = route['fuel efficiency(km/L)']

        # Calculate the route distance and emissions using Openrouteservice API
        if mode == "driving":
            distance, emissions = get_route(origin,destination,fuel,fuel_eff,(weight/1000))
        elif mode == "plane":
            distance, emissions = air(origin,destination,weight,mode)

        # Build the result object
        result = {
            'origin': origin,
            'destination': destination,
            'mode': mode,
            'distance': distance,
            'emissions': emissions
        }

        results.append(result)


    tot = sum(result.get('emissions', 0) for result in results)

    return tot


'''url = "https://www.carboninterface.com/api/v1/estimates"
headers = {
    "Authorization": "Bearer Eq8vmxlGJFDQJWlxXPb5A",
    "Content-Type": "application/json"
}
payload = {
    "type": "shipping",
    "weight_value": 200,
    "weight_unit": "g",
    "distance_value": 2000,
    "distance_unit": "km",
    "transport_method": "truck"
}

response = requests.post(url, headers=headers, data=json.dumps(payload))

print(response.json()["data"]["attributes"]["carbon_kg"])'''






