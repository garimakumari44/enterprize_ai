from typing import List, Dict
from datetime import datetime
import uuid


class GraphBuilder:
    """
    Builds knowledge graph objects
    from entities and relationships.
    """


    def __init__(self):
        pass



    def create_node(
        self,
        entity: Dict
    ) -> Dict:
        """
        Create graph node.
        """

        return {
            "id": entity.get(
                "id",
                str(uuid.uuid4())
            ),

            "label": entity.get(
                "name"
            ),

            "type": entity.get(
                "type",
                "UNKNOWN"
            ),

            "properties": entity.get(
                "properties",
                {}
            ),

            "created_at": datetime.utcnow()
        }



    def create_edge(
        self,
        relation: Dict
    ) -> Dict:
        """
        Create graph relationship.
        """

        return {

            "id": str(uuid.uuid4()),

            "source":
                relation["source"],

            "target":
                relation["target"],

            "type":
                relation["type"],

            "properties":
                relation.get(
                    "properties",
                    {}
                ),

            "created_at":
                datetime.utcnow()
        }



    def build_graph(
        self,
        entities: List[Dict],
        relations: List[Dict]
    ) -> Dict:
        """
        Build complete graph.
        """


        nodes = [
            self.create_node(entity)
            for entity in entities
        ]


        edges = [
            self.create_edge(relation)
            for relation in relations
        ]


        return {

            "nodes": nodes,

            "edges": edges,

            "metadata": {

                "node_count":
                    len(nodes),

                "edge_count":
                    len(edges),

                "created_at":
                    datetime.utcnow()
            }
        }