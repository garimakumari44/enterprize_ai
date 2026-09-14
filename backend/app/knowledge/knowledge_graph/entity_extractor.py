from abc import ABC, abstractmethod
from typing import List, Dict
import uuid
from datetime import datetime



class BaseEntityExtractor(ABC):
    """
    Abstract entity extraction interface.
    """


    @abstractmethod
    async def extract(
        self,
        text: str
    ) -> List[Dict]:
        pass



class EntityExtractor(
    BaseEntityExtractor
):
    """
    Default entity extractor.

    Production version can call:
    - LLM
    - NER model
    - Hybrid pipeline
    """


    def __init__(
        self,
        model=None
    ):

        self.model = model



    async def extract(
        self,
        text: str
    ) -> List[Dict]:


        """
        Extract entities.

        Example output:

        [
            {
                id:"123",
                name:"OpenAI",
                type:"ORGANIZATION"
            }
        ]

        """


        entities = []


        # Placeholder extraction logic
        # Replace with LLM / NLP model


        words = text.split()


        for word in words:


            if word.istitle():

                entities.append(

                    self._create_entity(
                        name=word,
                        entity_type="UNKNOWN"
                    )

                )


        return entities



    def _create_entity(
        self,
        name:str,
        entity_type:str
    ) -> Dict:


        return {

            "id":
                str(uuid.uuid4()),


            "name":
                name,


            "type":
                entity_type,


            "properties":
            {

                "source":
                    "entity_extractor"

            },


            "created_at":
                datetime.utcnow()

        }