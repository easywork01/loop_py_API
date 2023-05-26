import csv
import os
import fastcsv
from flask import Flask, request, jsonify

import moment
from moment import tz

app = Flask(__name__)

arr1 = []
arr2 = []
arr3 = []
matchedData = []

@app.route("/storestatus", methods=["GET"])
def get_store_status():
    with open("store_status.csv", "r") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            arr1.append(row)
    return jsonify(arr1)

@app.route("/businesshours", methods=["GET"])
def get_business_hours():
    with open("business_hours.csv", "r") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            arr2.append(row)
    return jsonify(arr2)

@app.route("/timezones", methods=["GET"])
def get_timezones():
    with open("time_zone.csv", "r") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            arr3.append(row)
    return jsonify(arr3)

@app.route("/trigger_report", methods=["GET"])
def trigger_report():
    matchedData = []

    for i in range(len(arr1)):
        storeId = arr1[i]["store_id"]
        timestampUTC = arr1[i]["timestamp_utc"]
        storeStatus = arr1[i]["status"]

        timezoneRecord = next((record for record in arr3 if record["store_id"] == storeId), None)
        storeTimezone = timezoneRecord["timezone_str"] if timezoneRecord else "America/Chicago"

        timestampLocal = moment.utc(timestampUTC).tz(storeTimezone)

        dayOfWeek = timestampLocal.day()
        businessHoursRecord = next((record for record in arr2 if record["store_id"] == storeId and record["dayOfWeek"] == dayOfWeek), None)

        isOpen = True
        if businessHoursRecord:
            startTime = moment.tz(businessHoursRecord["start_time_local"], storeTimezone)
            endTime = moment.tz(businessHoursRecord["end_time_local"], storeTimezone)
            isOpen = timestampLocal.isBetween(startTime, endTime, None, "[]")

        downtimeMinutes = 0
        uptimeMinutes = 0
        if storeStatus == "inactive":
            downtimeMinutes = 60
        elif not isOpen:
            uptimeMinutes = 60
        else:
            uptimeMinutes = 60

        matchedData.append({
            "store_id": storeId,
            "uptime_last_hour": uptimeMinutes,
            "uptime_last_day": 0,
            "downtime_last_hour": downtimeMinutes,
            "downtime_last_day": 0,
            "update_last_week": 0,
            "downtime_last_week": 0
        })

    return jsonify({"success": True})

@app.route("/get-report", methods=["GET"])
def get_report():
    csvData = convert_to_csv(matchedData)

    response = make_response(csvData)
    response.headers["Content-Disposition"] = "attachment; filename=matched-data.csv"
    response.headers["Content-Type"] = "text/csv"

    return response

def convert_to_csv(data):
    output = StringIO()
    csv_writer = csv.DictWriter(output, fieldnames=data[0].keys())
    csv_writer.writeheader()
    csv_writer.writerows(data)
    return output.getvalue()

if __name__ == "__main__":
    app.run(port=3000)
