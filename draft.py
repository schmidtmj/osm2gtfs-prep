import overpy, json, sys, collections, os, csv


#Inherit classes from osm2gtfs - no need to build myself

#Swap this with a named tuple
class route_schedule:

    def __init__(self, fr, to, sched, freq, dur=120):
        self.route_from=str(fr).decode('utf-8')
        self.route_to=str(to).decode('utf-8')
        self.route_open=str(sched).decode('utf-8')
        self.route_dur=str(dur).decode('utf-8')
        self.route_freq=str(freq).decode('utf-8')

        self.route_via=None
        self.route_inter=None
        self.route_except=None
        self.route_inter_dur=None

def query_overpass(qry_str):
    return overpy.Overpass().query(qry_str)

def parse_fare(fare_str, currency_str='GHS'):
    fare, currency, null = fare_str.partition(currency_str)
    assert currency ==  currency_str
    assert len(null) == 0
    return [fare, currency]

#Can I get this from osm2gtfs get_routes() or similar?
def route_builder(relations):
    data_dict = collections.defaultdict(dict)
    for relation in relations:
        tag_dict = relation.tags
        route_id = tag_dict['ref']
        route_type = tag_dict['type']
        if route_type in data_dict[route_id].keys():
            data_dict[route_id][route_type] = [relation, data_dict[route_id][route_type]]
        else:
            data_dict[route_id][route_type] = relation
    return data_dict

def extract_fares(routes_dict):
    route_dict={}
    for route_id, route_data in routes_dict.iteritems():
        master_tags = route_data['route_master'].tags
        route_fare, route_currency = parse_fare(master_tags['charge'])
        route_dict[route_id] = [{'general_fare': route_fare}]
    return route_dict

def extract_schedules(routes_dict):
    columns = ['ref', 'from', 'to', 'via', 'intermediates', 'opening-hours', 'exceptions', 'duration', 'intermediate-durations', 'frequency']
    csv_data = [columns]
    for route_id, route_data in routes_dict.iteritems():
        csv_data.append(extract_schedule_fields(route_id, route_data))
    return csv_data

def extract_schedule_fields(route_id, route_data):
    print(route_id, route_data['route_master'].id)
    master_tags = route_data['route_master'].tags
    route1_tags = route_data['route'][0].tags
    route2_tags = route_data['route'][1].tags

    route_sched='Mo-Sat 05:00-22:00;Sun 10:00-18:00'
    return route_schedule(route1_tags['from'], route1_tags['to'], route_sched, master_tags['frequency'], dur=120)

def write_fares(routes_dict, base_dict, json_file):
    base_dict['lines'] = routes_dict
    with open(json_file, 'w') as outfile:
        json.dump(base_dict, outfile, indent=4)
    print('JSON file written to {}'.format(json_file))

def write_schedules(csv_data, csv_save):
    with open(csv_save, 'w') as outfile:
        csv_writer = csv.writer(outfile)
        csv_writer.writerows(csv_data)
        print("CSV File Written to {}".format(csv_save))

def main():

    working_dir = os.getcwd()
    csv_out = os.path.join(working_dir, 'test.csv')
    json_out = os.path.join(working_dir, 'test.json')
    qry_str = """[out:json];
                 area(3601991849)->.searchArea;
                 relation
                   ["type"="route"]
                   ["bus"="unofficial"]
                   (area.searchArea);
                 relation(br);
                 >>;
                 out;"""

    test_str = """[out:json];
                  area(3601991849)->.searchArea;
                  relation(7481388);
                  >>;
                  out;"""
#7481244
#7481388
    base_dict = {"start_date": "2018-01-01",
                   "end_date": "2018-12-31",
                   "updated": "2018-03-15",
                   "currency_type": "GHC",
                   "payment_method": "0",
                   "transfers": "0"}

    qry_result = query_overpass(qry_str)
    routes = route_builder(qry_result.relations)

    write_to_csv(extract_schedules(routes), csv_out)
    write_to_json(extract_fares(routes), base_dict, json_out)

    print('DONE')

if __name__ == '__main__':
  main()

#3601991849 - Accra
#3600192781 - Ghana


#Solve key error issue (why??), make this whle thing a class with default values and boom off we go

#Can make relation object class with ref, charge, frequency, and more attributes, maybe a fare_to_json method which can be extended later
