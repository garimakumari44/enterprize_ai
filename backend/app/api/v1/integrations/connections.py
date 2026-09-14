from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(
    prefix="/connections",
    tags=["Connections"]
)



class ConnectionCreate(BaseModel):

    name:str
    integration:str
    credentials:dict



connections=[]



@router.post("/")
async def create_connection(
    data:ConnectionCreate
):

    connection={

        "id":len(connections)+1,
        "name":data.name,
        "integration":data.integration,
        "credentials":data.credentials
    }


    connections.append(connection)


    return {
        "message":"Connection created",
        "connection":connection
    }



@router.get("/")
async def list_connections():

    return connections



@router.get("/{connection_id}")
async def get_connection(
    connection_id:int
):

    for c in connections:

        if c["id"]==connection_id:
            return c


    raise HTTPException(
        404,
        "Connection not found"
    )



@router.delete("/{connection_id}")
async def delete_connection(
    connection_id:int
):

    for c in connections:

        if c["id"]==connection_id:

            connections.remove(c)

            return {
                "message":"Deleted"
            }


    raise HTTPException(
        404,
        "Connection not found"
    )