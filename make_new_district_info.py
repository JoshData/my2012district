import csv, re, urllib2, json, os.path

candidate_info = { }

# Get nice and normalized information from OpenSecrets.org. Tie to GovTrack IDs
# where available.
can_id_map = { }
for line in csv.reader(open("data/cands12.txt"), delimiter=",", quotechar="|"):
	if line[5][2] == "S": continue # we only care about House candidates
	
	candidate_info[line[1]] = {
		"FEC_ID": line[1],
		"CRP_ID": line[2],
		"NAME": re.sub(r" \(.\)$", "", line[3]), # remove party symbol from name
		"PARTY": { "D": "Democratic Party", "R": "Republican Party", "L": "Libertarian Party", "I": "Independent", "U": "[Party Unknown]", "3": "Other Party"}[ line[4] ],
		}
		
	can_id_map[line[2]] = line[1]

if not os.path.exists("static/candidates.json"):
	# Look up GovTrack record.
	for can in candidate_info.values():
		info = json.load(urllib2.urlopen("http://www.govtrack.us/api/v1/person/?osid=" + can["CRP_ID"]))
		if len(info["objects"]) == 1:
			can["GOVTRACK_INFO"] = info["objects"][0]
else:
	# Don't hit the API again, grab from previous run of this script.
	old_data = json.load(open("static/candidates.json"))
	for district in old_data.values():
		for can in district:
			if "GOVTRACK_INFO" in can:
				candidate_info[can["FEC_ID"]]["GOVTRACK_INFO"] = can["GOVTRACK_INFO"]
				
# Check incumbents that we know are no longer running, since they may still appear
# in the FEC data.
not_running = set()
for line in csv.reader(open("data/not_an_incumbent.txt"), delimiter="\t", quotechar=None):
	if line[2] != "":
		not_running.add(line[2])
	
# Get the most up-to-date information from the FEC, adding in any candidates
# missing from OpenSecrets and creating the master list of the running candidates.
candidates = { }
for line in csv.reader(open("data/webl12.txt"), delimiter="|", quotechar=None):
	if line[0][0] != "H": continue # we only care about House candidates
	if line[19].strip() == "": continue # no district identified?
	if line[0] in not_running: continue
	if line[0] not in candidate_info:
		# If there was no OpenSecrets record for this candidate, add a new record.
		# Clean names: make first-last format and force to title case.
		name = re.sub("^(.*?), (.*)", lambda m : m.group(2) + " " + m.group(1), line[1])
		name = re.sub(r"((^|\s)\w)(\w+)", lambda m : m.group(1) + m.group(3).lower(), name)
		candidate_info[line[0]] = {
			"FEC_ID": line[0],
			"NAME": name,
			"PARTY": { "DEM": "Democratic Party", "DFL": "Democratic Party", "GRE": "Green Party", "GRN": "Green Party", "REP": "Republican Party", "LIB": "Libertarian Party", "IND": "Independent", "UNK": "[Party Unknown]", "3": "Other Party", "OTH": "Other Party", "NPA": "[No Party]", "NNE": "[No Party]", "NOP": "[No Party]", "WFP": "Working Families Party"}[ line[4] ],
		}
	candidate_info[line[0]]["NAME_SORT"] = line[1]
	d = line[18] + line[19] # state + district number
	candidates.setdefault(d, []).append(candidate_info[line[0]])
		
# Did the candidate run last cycle?
ran2010map = { }
for line in csv.reader(open("data/cands10.txt"), delimiter=",", quotechar="|"):
	if line[2] in can_id_map:
		candidate_info[can_id_map[line[2]]]["RAN2010"] = { "DISTRICT": line[5], "FEC_ID": line[1] }
		ran2010map[line[1]] = can_id_map[line[2]]
	if line[1] in candidate_info:
		candidate_info[line[1]]["RAN2010"] = { "DISTRICT": line[5], "FEC_ID": line[1] }
		ran2010map[line[1]] = line[1]

# Add 2010 election results by candidate.
# The first entry for a district is the winner.
results10_last_district = (None, None)
for line in csv.reader(open("data/results10.csv"), delimiter=",", quotechar="\""):
	is_winner = (results10_last_district != (line[2], line[3]))
	results10_last_district = (line[2], line[3])
	if line[4] not in ran2010map: continue
	can = candidate_info[ran2010map[line[4]]]
	
	# candidates are repeated if they ran in more than one party, which will confuse is_winner.
	# to do this correctly, only set WON if this is the first time we're seeing this candidate.
	if "WON" not in can["RAN2010"]: can["RAN2010"]["WON"] = is_winner 
	if line[16] == "": continue # ran in primary only?
	
	# candidates that run in more than one party should have their vote totals summed across parties(?)
	can["RAN2010"]["VOTESABS"] = can["RAN2010"].get("VOTESABS", 0) + int(line[15].replace(",", ""))
	can["RAN2010"]["VOTESPCT"] = can["RAN2010"].get("VOTESPCT", 0) + float(line[16].replace("%", ""))

# Sort the candidates in each district.
for district in candidates.values():
	district.sort(key = lambda c : (
		not "GOVTRACK_INFO" in c,
		not (c["RAN2010"].get("WON", False) if "RAN2010" in c else False),
		-(c["RAN2010"].get("VOTESPCT", 0) if "RAN2010" in c else -1),
		c["NAME_SORT"]
		))

# Dump the master information pretty-printed.
json.dump(candidates, open("static/candidates.json", "w"), sort_keys=True, indent=4)

# Dump each district to a separate file in compact form.
for district in candidates:
	json.dump(candidates[district], open("static/districts/candidates_%s.json" % district.lower(), "w"), sort_keys=True, separators=(',',':'))

