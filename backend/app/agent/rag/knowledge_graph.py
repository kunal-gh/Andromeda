"""Knowledge Graph layer using NetworkX for entity-relationship reasoning."""
from typing import Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class Entity:
    id: str
    type: str
    properties: dict[str, Any]

@dataclass
class Relationship:
    source: str
    target: str
    type: str
    properties: dict[str, Any]

class AndromedaKnowledgeGraph:
    def __init__(self):
        try:
            import networkx as nx
            self.graph = nx.DiGraph()
            self._available = True
        except ImportError:
            self._available = False
            logger.warning("networkx not installed. Knowledge Graph disabled.")
    
    def add_entity(self, entity: Entity):
        if not self._available:
            return
        self.graph.add_node(entity.id, type=entity.type, **entity.properties)
    
    def add_relationship(self, rel: Relationship):
        if not self._available:
            return
        self.graph.add_edge(rel.source, rel.target, type=rel.type, **rel.properties)
    
    def get_related_entities(self, entity_id: str, relationship_type: str | None = None) -> list[dict]:
        if not self._available or entity_id not in self.graph:
            return []
        related = []
        for neighbor in self.graph.neighbors(entity_id):
            edge_data = self.graph.get_edge_data(entity_id, neighbor)
            if relationship_type is None or edge_data.get("type") == relationship_type:
                node_data = {k: v for k, v in self.graph.nodes[neighbor].items() if k != "type"}
                related.append({
                    "id": neighbor, 
                    "type": self.graph.nodes[neighbor].get("type"), 
                    "relationship": edge_data.get("type"), 
                    **node_data
                })
        return related
    
    def find_paths(self, source: str, target: str, max_length: int = 3) -> list[list[str]]:
        if not self._available:
            return []
        import networkx as nx
        try:
            return list(nx.all_simple_paths(self.graph, source, target, cutoff=max_length))
        except nx.NetworkXNoPath:
            return []
    
    def query_subgraph(self, entity_type: str | None = None, **property_filters) -> list[dict]:
        if not self._available:
            return []
        results = []
        for node_id, data in self.graph.nodes(data=True):
            if entity_type and data.get("type") != entity_type:
                continue
            if all(data.get(k) == v for k, v in property_filters.items()):
                results.append({"id": node_id, **data})
        return results

_knowledge_graph: AndromedaKnowledgeGraph | None = None

def get_knowledge_graph() -> AndromedaKnowledgeGraph:
    global _knowledge_graph
    if _knowledge_graph is None:
        _knowledge_graph = AndromedaKnowledgeGraph()
        _seed_knowledge_graph(_knowledge_graph)
    return _knowledge_graph

def _seed_knowledge_graph(kg: AndromedaKnowledgeGraph):
    if not kg._available:
        return
    try:
        from app.db.database import SessionLocal
        from app.db.models import Customer, Order
        db = SessionLocal()
        try:
            for customer in db.query(Customer).all():
                kg.add_entity(Entity(id=customer.id, type="customer", properties={
                    "name": customer.name, 
                    "email": customer.email, 
                    "tier": customer.loyalty_tier, 
                    "fraud_risk": customer.fraud_risk
                }))
            for order in db.query(Order).all():
                kg.add_entity(Entity(id=order.id, type="order", properties={
                    "item": order.item_name, 
                    "category": order.category, 
                    "price": order.price, 
                    "status": order.status, 
                    "final_sale": order.final_sale
                }))
                kg.add_relationship(Relationship(source=order.customer_id, target=order.id, type="purchased", properties={"date": str(order.purchase_date)}))
        finally:
            db.close()
    except ImportError:
        pass
