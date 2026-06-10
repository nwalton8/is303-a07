import pandas as pd
import time
import matplotlib.pyplot as plt
import requests
from peewee import SqliteDatabase, Model, CharField, FloatField, BooleanField, IntegerField
from bs4 import BeautifulSoup
import os

if os.path.exists('vehicles.db'):
    os.remove('vehicles.db')

db = SqliteDatabase('vehicles.db')

class Vehicle(Model):
    year = IntegerField()
    make = CharField()
    model = CharField()
    extra_text = CharField()
    mpg = IntegerField()
    category = CharField()
    tco_10_years = FloatField()

    class Meta:
        database = db
        
db.connect()
db.create_tables([Vehicle])

list_of_vehicles = [
    {'year': 2020, 'make': "Toyota", 'model': "Camry", 'extra_text': "", 'mpg': 29, 'category': "Midsize Car", 'tco_10_years': 35000},
    {'year': 2020, 'make': "Honda", 'model': "Civic", 'extra_text': " 4Dr", 'mpg': 32, 'category': "Compact Car", 'tco_10_years': 30000},
    {'year': 2026, 'make': "Toyota", 'model': "Prius", 'extra_text': "", 'mpg': 58, 'category': "Hybrid Car", 'tco_10_years': 25000}
]

for vehicle in list_of_vehicles:
    Vehicle.get_or_create(**vehicle)

for vehicle in Vehicle.select():
    print(f"{vehicle.year} {vehicle.make} {vehicle.model} - MPG: {vehicle.mpg}, TCO 10 Years: ${vehicle.tco_10_years:.2f}")
    



def get_fuel_data(year, make, model):
    base_url = "https://www.fueleconomy.gov/ws/rest/"
    baseheaders = {"Accept": "application/json"}
    url = base_url + f"vehicle/menu/options?year={year}&make={make}&model={model}"
    response = requests.get(url, headers=baseheaders)
    #print(response.text)
    data = response.json()
    if type(data['menuItem']) == list:
        vehicle_id = data['menuItem'][0]['value']
    else:
        vehicle_id = data['menuItem']['value']
    #print(vehicle_id)
    
    url = base_url + f"vehicle/{vehicle_id}"
    response = requests.get(url, headers=baseheaders)
    data = response.json()
    #print(data['comb08'])
    
    return data['comb08']
    
    
def get_maintenance_cost(make, model):
    total_maintenance = 0
    base_url = "https://caredge.com/"
    base_headers = {"User-Agent": "Mozilla/5.0"}
    url = f"{base_url}{make.lower()}/{model.lower()}/maintenance"
    response = requests.get(url, headers=base_headers)
    #print(response.text)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find_all("table")[0]
    if not table:
        print(f"No maintenance data found for {make} {model}")
        return 0
    for row in table.find_all("tr")[1:]:
        cells = [td.get_text(strip=True) for td in row.find_all("td")]
        dollar_amount = cells[2]
        int_amount = int(dollar_amount.replace("$", "").replace(",", ""))
        total_maintenance += int_amount
    #print(f"${total_maintenance:,}")
    return total_maintenance


for vehicle in list_of_vehicles:
    mpg = get_fuel_data(vehicle["year"], vehicle["make"], vehicle["model"]+vehicle["extra_text"])
    ten_year_maintenance_cost = get_maintenance_cost(vehicle["make"], vehicle["model"])
    tco = 11000*10/int(mpg)*4.50 + ten_year_maintenance_cost
    print(f"{vehicle['year']} {vehicle['make']} {vehicle['model']} - Total Cost: ${tco:.2f}")
    time.sleep(1)  # Sleep for 1 second to avoid overwhelming the servers
    
