"""build_graph.py — builds campus_graph.pkl from buildings.json"""
import json, math, pickle, argparse
from pathlib import Path
import networkx as nx

def haversine(lat1,lng1,lat2,lng2):
    R=6_371_000
    phi1,phi2=math.radians(lat1),math.radians(lat2)
    dphi=math.radians(lat2-lat1); dlam=math.radians(lng2-lng1)
    a=math.sin(dphi/2)**2+math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return 2*R*math.asin(math.sqrt(a))

PROXIMITY_THRESHOLD=350
BARRIER_PAIRS={frozenset({"memorial_stadium","clark_kerr"}),frozenset({"memorial_stadium","international_house"}),
               frozenset({"clark_kerr","rsf"}),frozenset({"foothill_dining","campanile"})}
CURATED_EDGES=[
    ("soda_hall","cory_hall",80),("cory_hall","soda_hall",80),("cory_hall","hearst_mining",120),("hearst_mining","cory_hall",120),
    ("hearst_mining","etcheverry_hall",140),("etcheverry_hall","hearst_mining",140),("etcheverry_hall","davis_hall",90),("davis_hall","etcheverry_hall",90),
    ("davis_hall","mclaughlin_hall",100),("mclaughlin_hall","davis_hall",100),("soda_hall","hesse_hall",130),("hesse_hall","soda_hall",130),
    ("hesse_hall","bechtel_center",80),("bechtel_center","hesse_hall",80),("bechtel_center","etcheverry_hall",110),("etcheverry_hall","bechtel_center",110),
    ("soda_hall","foothill_dining",320),("foothill_dining","soda_hall",320),("tan_hall","hildebrand_hall",80),("hildebrand_hall","tan_hall",80),
    ("hildebrand_hall","latimer_hall",60),("latimer_hall","hildebrand_hall",60),("latimer_hall","pimentel_hall",110),("pimentel_hall","latimer_hall",110),
    ("pimentel_hall","lewis_hall",90),("lewis_hall","pimentel_hall",90),("tan_hall","cory_hall",160),("cory_hall","tan_hall",160),
    ("stanley_hall","li_ka_shing",80),("li_ka_shing","stanley_hall",80),("li_ka_shing","valley_life_sci",100),("valley_life_sci","li_ka_shing",100),
    ("valley_life_sci","wellman_hall",120),("wellman_hall","valley_life_sci",120),("wellman_hall","koshland_hall",80),("koshland_hall","wellman_hall",80),
    ("koshland_hall","morgan_hall",60),("morgan_hall","koshland_hall",60),("koshland_hall","hilgard_hall",80),("hilgard_hall","koshland_hall",80),
    ("hilgard_hall","giannini_hall",110),("giannini_hall","hilgard_hall",110),("giannini_hall","mulford_hall",90),("mulford_hall","giannini_hall",90),
    ("tolman_hall","valley_life_sci",150),("valley_life_sci","tolman_hall",150),("tolman_hall","stanley_hall",130),("stanley_hall","tolman_hall",130),
    ("hearst_gym","valley_life_sci",180),("valley_life_sci","hearst_gym",180),("stanley_hall","latimer_hall",200),("latimer_hall","stanley_hall",200),
    ("doe_library","bancroft_library",80),("bancroft_library","doe_library",80),("doe_library","moffitt_library",90),("moffitt_library","doe_library",90),
    ("moffitt_library","moses_hall",100),("moses_hall","moffitt_library",100),("doe_library","wheeler_hall",130),("wheeler_hall","doe_library",130),
    ("wheeler_hall","barrows_hall",110),("barrows_hall","wheeler_hall",110),("barrows_hall","campbell_hall",90),("campbell_hall","barrows_hall",90),
    ("campbell_hall","leconte_hall",80),("leconte_hall","campbell_hall",80),("leconte_hall","birge_hall",70),("birge_hall","leconte_hall",70),
    ("birge_hall","haviland_hall",150),("haviland_hall","birge_hall",150),("doe_library","dwinelle_hall",160),("dwinelle_hall","doe_library",160),
    ("dwinelle_hall","kroeber_hall",90),("kroeber_hall","dwinelle_hall",90),("kroeber_hall","moffitt_library",130),("moffitt_library","kroeber_hall",130),
    ("moses_hall","barrows_hall",120),("barrows_hall","moses_hall",120),("campanile","bancroft_library",150),("bancroft_library","campanile",150),
    ("campanile","evans_hall",200),("evans_hall","campanile",200),("campanile","blum_hall",110),("blum_hall","campanile",110),
    ("blum_hall","boalt_hall",110),("boalt_hall","blum_hall",110),("boalt_hall","social_sciences",120),("social_sciences","boalt_hall",120),
    ("social_sciences","wurster_hall",80),("wurster_hall","social_sciences",80),("wurster_hall","north_gate_hall",110),("north_gate_hall","wurster_hall",110),
    ("haviland_hall","north_gate_hall",130),("north_gate_hall","haviland_hall",130),("evans_hall","social_sciences",200),("social_sciences","evans_hall",200),
    ("sather_gate","doe_library",250),("doe_library","sather_gate",250),("sather_gate","sproul_hall",200),("sproul_hall","sather_gate",200),
    ("sather_gate","durant_hall",210),("durant_hall","sather_gate",210),("sproul_hall","mlk_student_union",100),("mlk_student_union","sproul_hall",100),
    ("mlk_student_union","eshleman_hall",60),("eshleman_hall","mlk_student_union",60),("sproul_hall","crossroads_dining",200),("crossroads_dining","sproul_hall",200),
    ("crossroads_dining","rsf",280),("rsf","crossroads_dining",280),("zellerbach_hall","dwinelle_hall",200),("dwinelle_hall","zellerbach_hall",200),
    ("zellerbach_hall","sproul_hall",190),("sproul_hall","zellerbach_hall",190),("durant_hall","stephens_hall",100),("stephens_hall","durant_hall",100),
    ("stephens_hall","wheeler_hall",170),("wheeler_hall","stephens_hall",170),("international_house","rsf",400),("rsf","international_house",400),
    ("memorial_stadium","evans_hall",600),("evans_hall","memorial_stadium",600),
]

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--buildings",default="buildings.json")
    parser.add_argument("--output",default="campus_graph.pkl")
    args=parser.parse_args()
    with open(args.buildings) as f: buildings=json.load(f)
    G=nx.DiGraph()
    for b in buildings:
        G.add_node(b["id"],name=b["name"],lat=b["lat"],lng=b["lng"],type=b["type"],area=b["area"],abbr=b["abbr"])
    curated_set=set()
    for u,v,w in CURATED_EDGES:
        if G.has_node(u) and G.has_node(v):
            G.add_edge(u,v,weight=w,source="curated"); curated_set.add((u,v))
    n=len(buildings)
    for i in range(n):
        for j in range(i+1,n):
            a,b=buildings[i],buildings[j]
            dist=haversine(a["lat"],a["lng"],b["lat"],b["lng"])
            if dist<=PROXIMITY_THRESHOLD:
                pair=frozenset({a["id"],b["id"]})
                if pair not in BARRIER_PAIRS:
                    if (a["id"],b["id"]) not in curated_set: G.add_edge(a["id"],b["id"],weight=round(dist,1),source="proximity")
                    if (b["id"],a["id"]) not in curated_set: G.add_edge(b["id"],a["id"],weight=round(dist,1),source="proximity")
    print(f"Nodes: {G.number_of_nodes()}  Edges: {G.number_of_edges()}")
    assert G.number_of_nodes()>=50 and G.number_of_edges()>=120
    with open(args.output,"wb") as f: pickle.dump(G,f)
    print(f"Saved to {args.output} ✓")
