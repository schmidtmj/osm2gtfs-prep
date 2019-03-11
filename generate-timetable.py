#!/usr/bin/env python
# coding=utf-8

import os, sys, csv, json, re, datetime

working_dir = os.getcwd()
frequency_file = os.path.join(working_dir, 'frequency.csv')
timetable_file = os.path.join(working_dir, 'timetable.json')
header_data = {"start_date": "2019-01-01",
               "end_date": "2022-01-01",
               "included_lines": [],
               "excluded_lines": []}

def load_csv(csv_in):
    with open(csv_in) as f:
        return list(csv.DictReader(f))

def write_json(json_obj, json_out):
    with open(json_out, 'w') as outfile:
        json.dump(json_obj, outfile, sort_keys=True, indent=4, ensure_ascii=False)

def convert_opening_hrs(opening_hours):
    opening_services = {}
    for i, d in enumerate(opening_hours):
        (opening_service, opening_hour) = opening_hours[i].strip().split(' ')
        if opening_service in opening_services:
            opening_services[opening_service].append(opening_hour)
        else:
            opening_services[opening_service] = [opening_hour]
    return opening_services

def generate_json(input_data, header_data):

    #Copy header data in
    output = header_data.copy()

	# Add basic json structure
    output['updated'] = datetime.date.today().isoformat()
    output['lines'] = {}

    # Loop through bus lines
    for data in input_data:

        ref = data['ref']
        if len(output['included_lines']) > 0 :
            if ref not in output['included_lines']:
                continue
        elif ref in output['excluded_lines']:
            continue
        else:
            if ref not in output['lines']:
                output["lines"][ref] = []
            fr = data['fr']
            to = data['to']

            exceptions = []
            if 'opening-hours' not in data.keys():
                data['opening-hours'] = 'Mo-Sa 10:00-17:00'

            if data['dur'] is None or data['dur'] == '':
                data['dur'] = 120
            else:
                data['dur'] = float(data['dur'])

            if data['freq'] is None or data['freq'] == '' or data['freq'] == 'irregular':
                data['freq'] = 10
            elif int(data['freq']) == 0 or int(data['freq']) > 10:
                data['freq'] = 10
            else:
                data['freq'] = float(data['freq'])


            # Prepare schedule
            opening_services = convert_opening_hrs(data['opening-hours'].split(";"))
            for opening_service in opening_services.keys():
                # output timetable information
                service = {
                    "from": fr,
                    "to": to,
                    "services": [opening_service],
                    "exeptions": exceptions,
                    "times": []
                }
                service['stations'] = [fr, to]
                stop_weights = [0,1]
                assert len(service['stations']) == len(stop_weights)

                for opening_hour in opening_services[opening_service]:
                    service["times"] += generate_times(opening_hour, stop_weights, float(data['freq']), data['dur'])

                output["lines"][ref].append(service)

    return output

def extract_service_times(opening_times):

    regex = re.search(r"([0-9]+):([0-9]+)-([0-9]+):([0-9]+)" , opening_times)
    if regex is not None:
        (start_hour, start_min, end_hour, end_min) = regex.groups()
    else:
        regex = re.search(r"([0-9]+):([0-9]+)" , opening_times)
        if regex is None:
            sys.stderr.write("Error: Some format error in the opening_hours. Please check your frequencies.csv.\n")
            sys.exit(0)
        (start_hour, start_min) = regex.groups()
        (end_hour, end_min) = (start_hour, start_min)

    return (datetime.datetime.combine(datetime.datetime.today(), datetime.time(int(start_hour), int(start_min))),
            datetime.datetime.combine(datetime.datetime.today(), datetime.time(int(end_hour), int(end_min))))

def generate_times(service_time, stop_weights, frequency, duration):
    times=[]
    start_time, end_time = extract_service_times(service_time)
    # get number of minutes between public transport service
    if frequency == 0:
        sys.stderr.write("Error: You can not use the value '0' for frequency. Please check your frequencies.csv.\n")
        sys.exit(0)
    else:
        frequency = datetime.timedelta(minutes=frequency)

    current_time = start_time

    while current_time + datetime.timedelta(minutes=duration) <= end_time:
        #stop_times = [current_time.strftime('%H:%M')]
        stop_times=[]
        for stop_w in stop_weights:
            stop_dur = datetime.timedelta(minutes=float(stop_w) * duration)
            stop_time = current_time + stop_dur
            stop_times.append(stop_time.strftime('%H:%M'))

        current_time += frequency
        assert len(stop_times) == len(stop_weights)
        times.append(stop_times)
    return times

def main():

    write_json(generate_json(load_csv(frequency_file), header_data), timetable_file)

if __name__ == "__main__":
    main()
