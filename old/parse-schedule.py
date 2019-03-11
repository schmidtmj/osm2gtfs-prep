import overpy, json, sys, collections, os, csv

class stop:
    'TBD'

class route_schedule:

    alias_dict = {'route_id': 'ref',
                       'route_from': 'from',
                       'route_to': 'to',
                       'route_via': 'via',
                       'route_inter': 'intermediates',
                       'route_open': 'opening-hours',
                       'route_except': 'exceptions',
                       'route_dur': 'duration',
                       'route_inter_dur': 'intermediate-durations',
                       'route_freq': 'frequency'}

    def __init__(self, route_id, route_tags, master_tags):

        self.route_id=route_id
        self.route_from=route_tags['from']
        self.route_to=route_tags['to']
        self.route_open='Mo-Sa 05:00-10:00'

        self.route_via=None
        self.route_inter=';'.join(route_tags['intermediates'])
        #self.route_inter=None
        self.route_except=None

        self.set_dur(route_tags)
        self.set_freq(master_tags['frequency'])
        #self.route_inter_dur=None
        self.set_inter_dur()

    def set_inter_dur(self):
        inter_num = len(self.route_inter.split(';'))
        inter_dur = round(float(self.route_dur)/inter_num,0)
        inter_dur_str = ';'.join([str(i*inter_dur) for i in range(inter_num)])
        self.route_inter_dur= inter_dur_str

    def set_freq(self, freq, max_wait=10):
        if freq == 'irregular' or freq == '0' or float(freq) > max_wait:
            freq = max_wait
        else:
            freq = float(freq)
        self.route_freq=freq

    def set_dur(self, dict, default_dur=120, min_per_stop=1):
        min_dur = len(self.route_inter.split(';')) * min_per_stop if self.route_inter else default_dur
        try:
            dur=dict['travel_time']
        except:
            dur=default_dur
        self.route_dur=str(max(min_dur, float(dur)))

    def to_dict(self, alias_dict=alias_dict, alias=True):

        if alias:
            return dict((alias_dict[key], value) for (key, value) in self.__dict__.items())
        else:
            return self.__dict__

def query_overpass(qry_str):
    return overpy.Overpass().query(qry_str)

def get_stops(relation, qry_result):
    member_list = []
    member_names = {}
    for member in relation.members:
        try:
            member_info = qry_result.get_node(member.ref, resolve_missing=False)
            member_list.append([member_info.id, float(member_info.lat), float(member_info.lon), member_info.tags])
            member_names[member_info.id]=member_info.tags['name']
        except:
            pass
    return member_names

def route_builder(qry_result):
    relations = qry_result.relations
    nodes = qry_result.nodes
    data_dict = collections.defaultdict(dict)
    for relation in relations:
        stops = get_stops(relation, qry_result)
        relation.tags['intermediates'] = list(stops.values())
        print(stops)
        tag_dict = relation.tags
        route_id = tag_dict['ref']
        route_type = tag_dict['type']
        if route_type in data_dict[route_id].keys():
            data_dict[route_id][route_type] = [relation, data_dict[route_id][route_type]]
        else:
            data_dict[route_id][route_type] = relation
    return data_dict

def extract_schedules(routes_dict):
    schedule_list=[]
    for route_id, route_dict in routes_dict.items():
        print(route_id, route_dict)
        for route in route_dict['route']:
            print(len(route.tags['intermediates']))
            schedule_list.append(route_schedule(route_id, route.tags, route_dict['route_master'].tags).to_dict())
    return schedule_list

def write_dict_to_csv(csv_data, csv_save):
    with open(csv_save, 'w') as outfile:
        csv_writer = csv.DictWriter(outfile, fieldnames=csv_data[0].keys())
        csv_writer.writeheader()
        csv_writer.writerows(csv_data)

def main():

    working_dir = os.getcwd()
    csv_out = os.path.join(working_dir, 'frequencies.csv')
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
                  relation(7584600);
                  >>;
                  out;"""

    print('Querying overpass...')
    qry_result = query_overpass(qry_str)
    print('Extracting schedule information....')
    routes = route_builder(qry_result)
    write_dict_to_csv(extract_schedules(routes), csv_out)
    print("Schedules written to {}".format(csv_out))

if __name__ == '__main__':
  main()

#3601991849 - Accra
#3600192781 - Ghana

#How add individualized opening hours, ??
