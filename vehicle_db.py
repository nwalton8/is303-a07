from peewee import *

db = SqliteDatabase("vehicles.db")

class Vehicle(Model):
    make = CharField()
    model = CharField()
    year = IntegerField()
    mpg = IntegerField()
    category = CharField()
    tco_10yr = IntegerField()

    class Meta:
        database = db

db.connect()
db.create_tables([Vehicle])


def store_vehicle(data):
    existing = Vehicle.get_or_none(
        (Vehicle.make == data["make"]) &
        (Vehicle.model == data["model"]) &
        (Vehicle.year == data["year"])
    )
    if existing:
        print(f"Skipping {data['make']} {data['model']}")
        return

    Vehicle.create(**data)
    print(f"Stored {data['make']} {data['model']}")


v1_data = {"make":"Toyota", "model":"Corolla",
            "year":2020, "mpg":34,
            "category":"Sedan", "tco_10yr":51200}

store_vehicle(v1_data)

v2_data = {"make":"Toyota", "model":"Prius",
            "year":2026, "mpg":50,
            "category":"Sedan", "tco_10yr":13000}

store_vehicle(v2_data)

v3_data = {"make":"Toyta", "model":"Tacoma",
            "year":2026, "mpg":15,
            "category":"Truck", "tco_10yr":25000}

store_vehicle(v3_data)


incorrect_row = Vehicle.get(Vehicle.make == "Toyta")
incorrect_row.make = "Toyota"
incorrect_row.save()

for v in Vehicle.select():
    print(v.make, v.model, v.mpg)