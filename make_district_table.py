import json, csv, sys

distrs = json.load(open("static/candidates.json"))

w = csv.writer(sys.stdout)
w.writerow(["2010 matches", "2012", "notes"])
for d, cands in distrs.items():
	# at-large districts don't change
	if d.endswith("00"): continue
	
	# get incumbents running in this district
	incumbs = [c for c in cands if c.get("RAN2010", { }).get("WON", False)]
	
	if len(incumbs) == 0:
		# No incumbent is running in this district, so we don't
		# have a way to match it up perfectly to a previous district.
		# But we can look at where the candidates ran last time.
		old_distrs = set(c["RAN2010"]["DISTRICT"] for c in cands if "RAN2010" in c)
		if len(old_distrs) == 0:
			# No district info!
			w.writerow(["", d, "no idea where this district came from"])
		elif len(old_distrs) == 1 and old_distrs == set([d]):
			# The only candidates that ran previously ran in this district.
			w.writerow([" ".join(old_distrs), d, "closest match was a losing candidate from 2010"])
		else:
			# Multiple districts...
			w.writerow([" ".join(old_distrs), d, "closest matches from 2010's losing candidates"])
		
	elif len(incumbs) == 1:
		# There is a single incumbent, so we can reliably say that
		# this district is the "same" as the district the incumbent
		# ran in the previous election.
		w.writerow([incumbs[0]["RAN2010"]["DISTRICT"], d, "exact match following the incumbent"])
		
	else:
		# There are multiple incumbents running in this district, which
		# indicates districts were merged.
		w.writerow([" ".join(i["RAN2010"]["DISTRICT"] for i in incumbs), d, "multiple incumbents running in " + d + " (merged district?)"])
		
