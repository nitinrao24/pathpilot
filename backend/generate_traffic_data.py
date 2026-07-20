"""generate_traffic_data.py — synthetic foot-traffic generator"""
import json, math, random, csv, argparse
from pathlib import Path

RANDOM_SEED = 42
CLASS_SLOTS = [(8,1.0),(9,1.5),(10,1.0),(11,1.5),(12,1.0),(13,1.5),(14,1.0),(15,1.5),(16,1.0),(17,1.5),(18,1.5)]

def minutes_until_next_class(hour):
    for s,d in CLASS_SLOTS:
        if s<=hour<s+d: return 0.0
        if s>hour: return (s-hour)*60
    return 999.0

def minutes_since_last_class_ended(hour):
    e=999.0
    for s,d in CLASS_SLOTS:
        end=s+d
        if end<=hour: e=min(e,(hour-end)*60)
    return e

def is_in_class(hour):
    for s,d in CLASS_SLOTS:
        if s<=hour<s+d: return True
    return False

def class_starting_soon(hour,window=15.0): return int(0<minutes_until_next_class(hour)<=window)

def build_features(btype,hour,dow,area):
    hs=math.sin(2*math.pi*hour/24); hc=math.cos(2*math.pi*hour/24)
    types=["lecture","lab","library","cafe","gym","landmark"]
    areas=["engineering","chemistry","bioscience","central","south","northside","east"]
    return {"hour":round(hour,2),"hour_sin":round(hs,4),"hour_cos":round(hc,4),
            "dow":dow,"is_weekend":int(dow>=5),
            "mins_to_class":round(min(minutes_until_next_class(hour),120),1),
            "mins_since_class":round(min(minutes_since_last_class_ended(hour),120),1),
            "in_class_now":int(is_in_class(hour)),"class_soon":class_starting_soon(hour),
            **{f"type_{t}":int(btype==t) for t in types},
            **{f"area_{a}":int(area==a) for a in areas}}

def score_to_label(s):
    if s>=0.68: return "high"
    if s>=0.18: return "medium"
    return "low"

def label_to_int(l): return {"low":0,"medium":1,"high":2}[l]

def lecture_profile(h,dow):
    if dow>=5: return 0.05
    for s,d in CLASS_SLOTS:
        if s<=h<s+d: return random.uniform(0.75,1.0) if 9<=h<=16 else random.uniform(0.55,0.80)
    m=minutes_until_next_class(h)
    if m<=10: return random.uniform(0.40,0.65)
    if m<=20: return random.uniform(0.15,0.35)
    return random.uniform(0.02,0.10)

def lab_profile(h,dow):
    if dow>=5: return random.uniform(0.10,0.30)
    if 9<=h<=18: return min(1.0,0.45+0.25*math.sin(math.pi*(h-9)/9)+random.uniform(-0.10,0.10))
    return random.uniform(0.05,0.25)

def library_profile(h,dow):
    if dow>=5: return random.uniform(0.35,0.70) if 11<=h<=21 else random.uniform(0.05,0.20)
    if h<9: return random.uniform(0.02,0.08)
    if 9<=h<=12: return random.uniform(0.25,0.50)
    if 12<=h<=17: return random.uniform(0.45,0.70)
    if 17<=h<=21: return random.uniform(0.65,0.95)
    return random.uniform(0.10,0.30)

def cafe_profile(h,dow):
    if 7.5<=h<=9: return random.uniform(0.55,0.85)
    if 11.5<=h<=13.5: return random.uniform(0.75,1.0)
    if 14<=h<=17: return random.uniform(0.20,0.40)
    if 17.5<=h<=19.5: return random.uniform(0.65,0.90)
    if h<7.5 or h>21: return 0.0
    return random.uniform(0.10,0.25)

def gym_profile(h,dow):
    if 6<=h<=9: return random.uniform(0.55,0.85)
    if 10<=h<=14: return random.uniform(0.15,0.35)
    if 16<=h<=20: return random.uniform(0.60,0.90)
    return random.uniform(0.05,0.20)

def landmark_profile(h,dow):
    if 8<=h<=18: return random.uniform(0.55,0.80) if minutes_until_next_class(h)<=10 else random.uniform(0.25,0.55)
    return random.uniform(0.05,0.20)

PROFILE_FN={"lecture":lecture_profile,"lab":lab_profile,"library":library_profile,
            "cafe":cafe_profile,"gym":gym_profile,"landmark":landmark_profile}

def generate_records(buildings,n_records,seed=RANDOM_SEED):
    random.seed(seed); records=[]; slots=[h/2 for h in range(14,46)]
    for _ in range(n_records):
        b=random.choice(buildings)
        hour=max(7.0,min(23.0,random.choice(slots)+random.uniform(-0.2,0.2)))
        dow=random.randint(0,6)
        score=PROFILE_FN.get(b["type"],lecture_profile)(hour,dow)
        score=max(0.0,min(1.0,score+random.gauss(0,0.07)))
        label=score_to_label(score)
        feat=build_features(b["type"],hour,dow,b["area"])
        records.append({"building_id":b["id"],"building_name":b["name"],**feat,
                        "raw_score":round(score,4),"congestion":label,"congestion_id":label_to_int(label)})
    return records

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--records",type=int,default=5000)
    parser.add_argument("--output",default="traffic_data.csv")
    parser.add_argument("--buildings",default="buildings.json")
    parser.add_argument("--seed",type=int,default=RANDOM_SEED)
    args=parser.parse_args()
    with open(args.buildings) as f: buildings=json.load(f)
    records=generate_records(buildings,args.records,args.seed)
    fieldnames=list(records[0].keys())
    with open(args.output,"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fieldnames); w.writeheader(); w.writerows(records)
    print(f"Saved {len(records)} records to {args.output}")
