#!/usr/bin/env python
# coding=utf-8

import os, sys, csv, json, re, datetime, getopt

working_dir = os.getcwd()
frequency_file = os.path.join(working_dir, 'test.csv')
header_file = os.path.join(working_dir, 'header.json')
timetable_file = os.path.join(working_dir, 'test.json')

def load_csv(csv_in):
    with open(csv_in, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def load_json(json_in):
    with open(json_in, newline='', encoding='utf-8') as f:
        return json.load(f)

def write_json(json_obj, json_out):
    with open(json_out, 'w', encoding='utf8') as outfile:
        json.dump(json_obj, outfile, sort_keys=True, indent=4, ensure_ascii=False)

def split_data(data_in):
    intermediates = data_in.split(";")
    if len(intermediates) == 1 and intermediates[0] == '':
        return []
    else:
        return intermediates

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

    output = {}

    # Add header data to output
    header_keys = ['start_date','end_date','excluded_lines','included_lines']
    for key in header_keys:
        if key in header_data:
            output[key] = header_data[key]
        else:
            sys.stderr.write("Warning: The header json file lacks the key '%s'.\nYou HAVE TO add it later manually.\n" % key)

	# Add basic json structure
    output['updated'] = datetime.date.today().isoformat()
    output['lines'] = {}

    # Loop through bus lines
    for data in input_data:

        ref = data['ref']
        if ref not in output["lines"]:
            output["lines"][ref] = []
        fr = data['fr']
        to = data['to']
        via = data['via']

        intermediates = split_data(data[''])
        intermediate_durations = split_data(data['intermediate-durations'])
        exceptions = split_data(data['exceptions'])

        if len(intermediates) != len(intermediate_durations):
            sys.stderr.write("Error: For ref=%s, from='%s', to='%s', via='%s', there weren't the same number of intermediate stops and intermediate times.\nSkipping this line, please check your frequencies.csv.\n" % (ref,fr,to,via))
            continue

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

            if len(via) > 0:
                service["via"] = via

            station_list = [fr, to]
            if len(intermediates) > 0:
                for station in intermediates:
                    if station not in station_list:
                        station_list.insert(-1, station)
            service["stations"] = station_list
            service["stations"] = [fr, to]

            for opening_hour in opening_services[opening_service]:
                pass
                service["times"] += generate_times(opening_hour, float(data['frequency']), data['duration'])
                #service["times"] = None

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

def generate_times(service_time, frequency, duration, inter_durations=None):
    times=[]
    start_time, end_time = extract_service_times(service_time)

    # get number of minutes between public transport service
    if frequency == 0:
        sys.stderr.write("Error: You can not use the value '0' for frequency. Please check your frequencies.csv.\n")
        sys.exit(0)
    else:
        frequency = datetime.timedelta(minutes=frequency)

    current_time = start_time
    if inter_durations:
        duration = datetime.timedelta(minutes=max([float(dur) for dur in inter_durations]))
    else:
        inter_durations = [0, duration]
        duration = datetime.timedelta(minutes=float(duration))

    while current_time + duration <= end_time:
        #stop_times = [current_time.strftime('%H:%M')]
        stop_times=[]
        for inter_dur in inter_durations:
            stop_time = current_time + datetime.timedelta(minutes=float(inter_dur))
            stop_times.append(stop_time.strftime('%H:%M'))

        current_time += frequency
        times.append(stop_times)
    return times

def main():

    input_data = load_csv(frequency_file)
    print(input_data[:5])
    header_data = load_json(header_file)
    output = generate_json(input_data, header_data)
    #print(output)

    write_json(output, timetable_file)


if __name__ == "__main__":
    main()
