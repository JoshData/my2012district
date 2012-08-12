import csv, json, urllib2, os.path

rep_map = { }
if not os.path.exists("static/olddistricts.json"):
	reps = json.load(urllib2.urlopen("http://www.govtrack.us/api/v1/person?roles__current=true&limit=1000"))
	for rep in reps["objects"]:
		rep_map[(rep["current_role"]["state"], rep["current_role"]["district"])] = rep
else:
	# Don't hit the API again.
	for distr, info in json.load(open("static/olddistricts.json")).items():
		if info["REP"]:
			rep_map[(distr[0:2], int(distr[2:]))] = info["REP"]
		
stateapportionment = {'AL': 7, 'AK': 1, 'AS': 'T', 'AZ': 8, 'AR': 4, 'CA': 53, 'CO': 7, 'CT': 5, 'DE': 1, 'DC': 'T', 'FL': 25, 'GA': 13, 'GU': 'T', 'HI': 2, 'ID': 2, 'IL': 19, 'IN': 9, 'IA': 5, 'KS': 4, 'KY': 6, 'LA': 7, 'ME': 2, 'MD': 8, 'MA': 10, 'MI': 15, 'MN': 8, 'MS': 4, 'MO': 9, 'MT': 1, 'NE': 3, 'NV': 3, 'NH': 2, 'NJ': 13, 'NM': 3, 'NY': 29, 'NC': 13, 'ND':  1, 'MP': 'T', 'OH': 18, 'OK': 5, 'OR': 5, 'PA': 19, 'PR': 'T', 'RI': 2, 'SC': 6, 'SD': 1, 'TN': 9, 'TX': 32, 'UT': 3, 'VT': 1, 'VI': 'T', 'VA': 11, 'WA': 9, 'WV': 3, 'WI': 8, 'WY': 1}

can_status = { }
for line in csv.reader(open("data/not_an_incumbent.txt"), delimiter="\t", quotechar=None):
	if line[1] not in ("GOVTRACK_ID", ""): # header, unknown value
		can_status[line[1]] = line[4]

districts = { }
for state in stateapportionment:
	for district in xrange(1, stateapportionment[state]+1 if stateapportionment[state] != "T" else 1+1):
		district = district if stateapportionment[state] not in ("T", 1) else 0
		
		districts[state + ("%02d" % district)] = {
			"REP": rep_map.get((state, district), None),
			"STATUS": can_status.get(rep_map.get((state, district), {}).get("id")),
		}
		
# Dump the master information pretty-printed.
json.dump(districts, open("static/olddistricts.json", "w"), sort_keys=True, indent=4)

# Dump each district to a separate file in compact form.
for district, data in districts.items():
	json.dump(data, open("static/districts/olddistrict_%s.json" % district.lower(), "w"), sort_keys=True, separators=(',',':'))

