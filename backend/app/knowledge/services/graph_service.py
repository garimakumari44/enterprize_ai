from __future__ import annotations

from typing import Any

from app.knowledge.knowledge_graph.graph_builder import GraphBuilder
from app.knowledge.knowledge_graph.entity_extractor import EntityExtractor
from app.knowledge.knowledge_graph.relation_extractor import RelationExtractor


class GraphService:
    """
    Business service for Knowledge Graph operations.
    """

    def __init__(
        self,
        entity_extractor: EntityExtractor,
        relation_extractor: RelationExtractor,
        graph_builder: GraphBuilder,
    ) -> None:

        self.entity_extractor = entity_extractor
        self.relation_extractor = relation_extractor
        self.graph_builder = graph_builder

    async def build_graph(
        self,
        text: str,
    ) -> dict[str, Any]:
        """
        Build a knowledge graph from text.
        """

        entities = self.entity_extractor.extract(text)

        relations = self.relation_extractor.extract(
            text=text,
            entities=entities,
        )

        graph = self.graph_builder.build(
            entities=entities,
            relations=relations,
        )

        return {
            "entities": entities,
            "relations": relations,
            "graph": graph,
        }

    async def extract_entities(
        self,
        text: str,
    ) -> list[dict[str, Any]]:
        """
        Extract entities only.
        """

        return self.entity_extractor.extract(text)

    async def extract_relations(
        self,
        text: str,
    ) -> list[dict[str, Any]]:
        """
        Extract relations only.
        """

        entities = self.entity_extractor.extract(text)

        return self.relation_extractor.extract(
            text=text,
            entities=entities,
        )

    async def graph_statistics(
        self,
        graph: Any,
    ) -> dict[str, int]:
        """
        Return basic graph statistics.
        """

        return {
            "nodes": len(graph.nodes),
            "edges": len(graph.edges),
        }