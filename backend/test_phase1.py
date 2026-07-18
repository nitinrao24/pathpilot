"""Phase 1 tests — pytest test_phase1.py -v"""
import pickle, pytest
import networkx as nx
from graph_utils import G, shortest_path, get_alternate_path, path_to_geojson, list_buildings

class TestGraphStructure:
    def test_minimum_node_count(self): assert G.number_of_nodes()>=50
    def test_minimum_edge_count(self): assert G.number_of_edges()>=120
    def test_is_directed(self): assert isinstance(G,nx.DiGraph)
    def test_fully_connected(self): assert nx.is_connected(G.to_undirected())
    def test_no_isolated_nodes(self): assert [n for n in G.nodes() if G.degree(n)==0]==[]
    def test_all_edges_positive_weight(self): assert all(d["weight"]>0 for _,_,d in G.edges(data=True))
    def test_all_nodes_required_fields(self):
        for nid,d in G.nodes(data=True): assert {"name","lat","lng","type","area","abbr"}.issubset(d.keys())
    def test_coordinates_on_campus(self):
        for nid,d in G.nodes(data=True):
            assert 37.860<=d["lat"]<=37.882; assert -122.270<=d["lng"]<=-122.245
    def test_key_buildings_present(self):
        for b in ["soda_hall","cory_hall","doe_library","sproul_hall","evans_hall"]: assert b in G
    def test_pkl_roundtrip(self):
        G2=pickle.load(open("campus_graph.pkl","rb"))
        assert G2.number_of_nodes()==G.number_of_nodes()

class TestShortestPathStructure:
    def test_required_keys(self):
        r=shortest_path("soda_hall","doe_library")
        assert {"path","names","coordinates","distance_m","walk_min","hops","congestion_applied"}.issubset(r.keys())
    def test_starts_ends_correctly(self):
        r=shortest_path("soda_hall","doe_library")
        assert r["path"][0]=="soda_hall"; assert r["path"][-1]=="doe_library"
    def test_hops_correct(self): r=shortest_path("soda_hall","doe_library"); assert r["hops"]==len(r["path"])-1
    def test_distance_positive(self): assert shortest_path("soda_hall","doe_library")["distance_m"]>0
    def test_no_congestion_by_default(self): assert shortest_path("soda_hall","doe_library")["congestion_applied"] is False

class TestShortestPathCorrectness:
    def test_adjacent_one_hop(self): assert shortest_path("soda_hall","cory_hall")["hops"]==1
    def test_path_edges_exist(self):
        r=shortest_path("foothill_dining","sproul_hall")
        for u,v in zip(r["path"][:-1],r["path"][1:]): assert G.has_edge(u,v)
    def test_triangle_inequality(self):
        ac=shortest_path("soda_hall","doe_library")["distance_m"]
        ab=shortest_path("soda_hall","birge_hall")["distance_m"]
        bc=shortest_path("birge_hall","doe_library")["distance_m"]
        assert ac<=ab+bc

class TestCongestionPenalties:
    def test_flag_true_with_penalties(self):
        r=shortest_path("soda_hall","doe_library",congestion_weights={("soda_hall","birge_hall"):100})
        assert r["congestion_applied"] is True
    def test_heavy_penalty_reroutes(self):
        base=shortest_path("soda_hall","cory_hall"); assert base["hops"]==1
        r=shortest_path("soda_hall","cory_hall",congestion_weights={("soda_hall","cory_hall"):50000})
        assert r["hops"]>1
    def test_base_graph_not_mutated(self):
        w=G["soda_hall"]["birge_hall"]["weight"]
        shortest_path("soda_hall","doe_library",congestion_weights={("soda_hall","birge_hall"):500})
        assert G["soda_hall"]["birge_hall"]["weight"]==w

class TestErrorHandling:
    def test_unknown_source(self):
        with pytest.raises(ValueError): shortest_path("fake","doe_library")
    def test_unknown_target(self):
        with pytest.raises(ValueError): shortest_path("soda_hall","fake")
    def test_same_source_target(self):
        with pytest.raises(ValueError): shortest_path("soda_hall","soda_hall")
