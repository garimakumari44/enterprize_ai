class GraphQuery:


    def __init__(
        self,
        graph_store
    ):

        self.graph_store = graph_store



    async def find_entity(
        self,
        name:str
    ):

        return await self.graph_store.search(
            name
        )



    async def get_neighbors(
        self,
        node_id:str
    ):


        neighbors=[]


        for edge in self.graph_store.edges:


            if edge["source"] == node_id:

                node = await self.graph_store.get_node(
                    edge["target"]
                )

                neighbors.append(node)



            elif edge["target"] == node_id:

                node = await self.graph_store.get_node(
                    edge["source"]
                )

                neighbors.append(node)



        return neighbors



    async def relationship_path(
        self,
        source:str,
        target:str
    ):

        """
        Find direct relationship.
        """

        paths=[]


        for edge in self.graph_store.edges:


            if (
                edge["source"] == source
                and
                edge["target"] == target
            ):

                paths.append(edge)



        return paths