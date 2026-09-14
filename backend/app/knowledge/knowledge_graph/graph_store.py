from abc import ABC, abstractmethod



class GraphStore(ABC):
    """
    Abstract graph database interface.
    """



    @abstractmethod
    async def add_node(
        self,
        node: dict
    ):
        pass



    @abstractmethod
    async def add_edge(
        self,
        edge: dict
    ):
        pass



    @abstractmethod
    async def get_node(
        self,
        node_id: str
    ):
        pass



    @abstractmethod
    async def delete_node(
        self,
        node_id: str
    ):
        pass



    @abstractmethod
    async def search(
        self,
        query: str
    ):
        pass