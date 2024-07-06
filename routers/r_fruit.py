#PRODUCTION SERVER

from models.m_fruit import Fruit, Seat
from fastapi import APIRouter, HTTPException
from config.redis import client
from config.db import db
from bson import ObjectId
import secrets
import datetime
import random
import json as js
from pymongo import ReturnDocument
from fastapi.responses import JSONResponse
from pydantic import BaseModel,json
from utils.fruit_game_boat import fruit_game_boat
json.ENCODERS_BY_TYPE[ObjectId]=str
router = APIRouter()
table_collection = db['fruits']
table_balance_collection = db["user_wallet_balances"]
transaction_collection = db["transactions"]
user_login_table= db["user_logins"]

from controllers.credit_diamonds import credit_diamonds as new_credit_diamonds

class UpdateSeatAmountRequest(BaseModel):
    UID: str
    amount: float
    seat: str


class RechargeRequest(BaseModel):
    amount: float
    user_id: str

async def check_active_game_and_end():
    try:
        docs = table_collection.find({"game_status": "active"})
        for doc in docs:
            isExist = client.get(f"{doc['_id']}")
            if isExist is None:
                try:
                    await winner_announced(doc['_id'])
                except Exception as error:
                    print(error)
            elif isExist is not None and doc["game_last_count"] <= 0:
                try:
                    await winner_announced(doc['_id'])
                except Exception as error:
                    print(error)

    except Exception as err:
        print(err)


@router.get("/create")
async def create():
    try:
        fruit_game =  client.get("fruit_game")
        if fruit_game is None:
            game_id = secrets.token_hex(8)
            fruit=Fruit(game_id=game_id,seat=Seat())
            fruit_dict = fruit.dict()
            doc_id=table_collection.insert_one(fruit_dict).inserted_id
            doc=table_collection.find_one({"_id":ObjectId(doc_id)})
            client.setex(str(doc_id), 28, str(doc["_id"])),
            client.setex("fruit_game", 23, str(doc["_id"])),
            await check_active_game_and_end()
            return {
                "success": True,
                "msg": "Game created",
                "data": {
                    "_id": doc_id,
                    "game_last_count": doc["game_last_count"]
                }
            }
        else:
            ttl =  client.ttl("fruit_game")
            if ttl >= 13:
                await check_active_game_and_end()
                docs = table_collection.find_one({"game_status": "active"}, {"game_last_count": 1})
                return {
                    "success": True,
                    "msg": "Game already created",
                    "data": docs
                }
            else:
                await check_active_game_and_end()
                return {
                    "success": False,
                    "msg": "Game already created but time is less than 15 sec",
                    "wait_time": ttl
                }
    except Exception as err:
        return {
            "success": False,
            "msg": err
        }



@router.get('/wallet-balance/{UID}')
async def walletBalance(UID:str):
    table_balance = user_login_table.find_one({"UID": UID})
    return {
        "data":{
            "diamond":table_balance["Udiamonds"]
            },
        "success":True,
        "msg":"Wallet balance"
    }
    
    
# Temparary route to recharge the user wallet
@router.post('/recharge-wallet')
async def recharge_wallet(request: RechargeRequest):
    # just increment the user wallet balance
    try:
        user_id = request.user_id
        amount = request.amount
        if not user_id or not amount:
            return{
                "success":False,
                "msg":"Invalid data"
            }
        table_balance = table_balance_collection.find_one({"user_id": user_id})
        if not table_balance:
            return{
                "success":False,
                "msg":"No data found"
            }
        updated_balance = table_balance_collection.find_one_and_update(
            {"_id": table_balance["_id"]},
            {"$inc": {"user_diamond": amount}},
            return_document=ReturnDocument.AFTER
        )
        return JSONResponse(status_code=200, content={
            "success": True,
            "msg": "Amount added successfully",
            "data": "updated_balance"
        })
    except Exception as err:
        return{
            "success":False,
            "msg":str(err)
        }
        


def randomGenrate(result):
    portUpdate = client.get("fruit_portUpdate")
    portUpdate=js.loads(portUpdate)
    port = [500,1000,500,1000]
    portRndm1 = random.randint(1,3)
    portRndm2 = random.randint(1,3)
    portRndm3 = random.randint(1,3)
    rndmn = random.randint(1, 3)
    if rndmn == 1:
        # add number on port any one
        rndmn1 = random.randint(1,3)
        if rndmn1 == 1:
            portUpdate['A_total_amount']+=port[portRndm1]
            portUpdate['A_total_amount']+=result['seat']['A_total_amount']
            client.set("fruit_portUpdate",js.dumps(portUpdate))
            return portUpdate
        elif rndmn1 == 2:
            portUpdate['B_total_amount']+=port[portRndm2]
            portUpdate['B_total_amount']+=result['seat']['B_total_amount']
            client.set("fruit_portUpdate",js.dumps(portUpdate))
            return portUpdate
        else:
            portUpdate['C_total_amount']+=port[portRndm3]
            portUpdate['C_total_amount']+=result['seat']['C_total_amount']
            client.set("fruit_portUpdate",js.dumps(portUpdate))
            return portUpdate
    elif rndmn == 2:
        # add number on port two A and B or A and C or 
        rndmn2 = random.randint(1,3)
        if rndmn2 == 1:
            portUpdate['A_total_amount']+=port[portRndm1]
            portUpdate['A_total_amount']+=result['seat']['A_total_amount']
            portUpdate['B_total_amount']+=port[portRndm2]
            portUpdate['B_total_amount']+=result['seat']['B_total_amount']
            client.set("fruit_portUpdate",js.dumps(portUpdate))
            return portUpdate # add here in port A and B
        elif rndmn2 == 2:
            portUpdate['B_total_amount']+=port[portRndm2]
            portUpdate['B_total_amount']+=result['seat']['B_total_amount']
            portUpdate['C_total_amount']+=port[portRndm3]
            portUpdate['C_total_amount']+=result['seat']['C_total_amount']
            client.set("fruit_portUpdate",js.dumps(portUpdate))
            return portUpdate # add here in port B and C
        else:
            portUpdate['C_total_amount']+=port[portRndm3]
            portUpdate['C_total_amount']+=result['seat']['C_total_amount']
            portUpdate['A_total_amount']+=port[portRndm1]
            portUpdate['A_total_amount']+=result['seat']['A_total_amount']
            client.set("fruit_portUpdate",js.dumps(portUpdate))
            return portUpdate # add here in port C and A
    else:
        # add here on every port
        portUpdate['C_total_amount']+=port[portRndm3]
        portUpdate['C_total_amount']+=result['seat']['C_total_amount']
        portUpdate['A_total_amount']+=port[portRndm1]
        portUpdate['A_total_amount']+=result['seat']['A_total_amount']
        portUpdate['B_total_amount']+=port[portRndm2]
        portUpdate['B_total_amount']+=result['seat']['B_total_amount']
        client.set("fruit_portUpdate",js.dumps(portUpdate))
        return portUpdate




@router.get('/user-bid/{game_id}/{UID}')
async def user_bid(game_id: str, UID: str):
    # print("this is game id and UID",game_id,UID)
    portUpdate = client.get("fruit_portUpdate")
    prev_gameId = client.get("fruit_prev_gameId")
    if prev_gameId is None:
        prev_gameId=None
    else:
        prev_gameId=js.loads(prev_gameId)
    if portUpdate is None:
        portUpdate={
            "A_total_amount":0,
            "B_total_amount":0,
            "C_total_amount":0
        }
        client.set("fruit_portUpdate",js.dumps(portUpdate))
    try:
        pipeline = [
            {"$match": {"_id": ObjectId(game_id)}},
        ]
        result = list(table_collection.aggregate(pipeline))
        sum_A = sum(item['amount'] for item in result[0]['users'] if item['UID'] == UID and item['seat'] == 'A')
        sum_B = sum(item['amount'] for item in result[0]['users'] if item['UID'] == UID and item['seat'] == 'B')
        sum_C = sum(item['amount'] for item in result[0]['users'] if item['UID'] == UID and item['seat'] == 'C')
        if game_id != prev_gameId:
            # prev_gameId=game_id
            client.set("fruit_prev_gameId",js.dumps(game_id))
            portUpdate={
            "A_total_amount":0,
            "B_total_amount":0,
            "C_total_amount":0
            }
            client.set("fruit_portUpdate",js.dumps(portUpdate))
        finalResult = randomGenrate(result[0])
        return {
            "success": True,
            "msg": "User bid found",
            "data": {
                "sum_A": sum_A,
                "sum_B": sum_B,
                "sum_C": sum_C,
                "A_total_amount": finalResult['A_total_amount'],
                "B_total_amount": finalResult['B_total_amount'],
                "C_total_amount": finalResult['C_total_amount']
            },
        } 
    except Exception as err:
        raise JSONResponse(status_code=500, detail=str(err))   


@router.put("/updateSeatAmount/{id}")
async def update_seat_amount(id: str, request: UpdateSeatAmountRequest):
    portUpdate = client.get("fruit_portUpdate")
    if portUpdate is None:
        portUpdate={
            "A_total_amount":0,
            "B_total_amount":0,
            "C_total_amount":0
        }
        client.set("fruit_portUpdate",js.dumps(portUpdate))
    prev_gameId = client.get("fruit_prev_gameId")
    if prev_gameId is None:
        prev_gameId = None
    else:
        prev_gameId = js.loads(prev_gameId)
    UID = request.UID
    amount = request.amount
    seat = request.seat
    if not UID or not amount or not seat:
        return{
            "success":False,
            "msg":"Invalid data"
        }

    table = table_collection.find_one({"_id": ObjectId(id)})
    if not table:
        # raise HTTPException(status_code=404, detail="No data found")
        return{
            "success":False,
            "msg":"No data found"
        }

    if table["game_status"] == "ended" or table["winnerAnnounced"] == "yes":
        # raise HTTPException(status_code=400, detail="This game has ended, please wait")
        return{
            "success":False,
            "msg":"This game has ended, please wait"
        }

    table_balance = user_login_table.find_one({"UID": UID})

    if not table_balance:
        # raise HTTPException(status_code=404, detail="No data found")
        return{
            "success":False,
            "msg":"No data found"
        }

    user_diamond = table_balance["Udiamonds"]

    if user_diamond < amount:
        # raise HTTPException(status_code=400, detail="Insufficient balance")
        return{
            "success":False,
            "msg":"Insufficient balance"
        }

    update_obj = {"$push": {"users": {"UID": UID, "seat": seat, "amount": amount}}}

    if seat == "A":
        update_obj["$inc"] = {"seat.A_total_amount": amount}
    elif seat == "B":
        update_obj["$inc"] = {"seat.B_total_amount": amount}
    elif seat == "C":
        update_obj["$inc"] = {"seat.C_total_amount": amount}

    updated_balance = user_login_table.find_one_and_update(
        {"_id": table_balance["_id"]},
        {"$inc": {"Udiamonds": - amount}},
        return_document=ReturnDocument.AFTER
    )
    if not updated_balance or int(updated_balance["Udiamonds"]) + int(amount) != user_diamond:
        # raise HTTPException(status_code=500, detail="Something went wrong")
        return{
            "success":False,
            "msg":"Something went wrong"
        }

    updated_table = table_collection.find_one_and_update(
        {"_id": ObjectId(id)},
        update_obj,
        return_document=ReturnDocument.AFTER
    )
    if updated_table:
        transaction_id = secrets.token_hex(8)
        transaction_data = {
            "transaction_id": transaction_id,
            "transaction_type": "debited",
            "transaction_amount": amount,
            "transaction_status": "success",
            "transaction_date": datetime.datetime.now(),
            "sender_type": "user",
            "receiver_type": "game",
            "sender_UID": UID,
            "before_tran_balance": user_diamond,
            "after_tran_balance": updated_balance["Udiamonds"],
            "receiver_UID": id,
            "user_wallet_type_from": "diamonds",
            "user_wallet_type_to": "diamonds",
            "entity_type": {
                "type": "game",
                "game_id": id,
                "game_name": "fruit"
            }
        }
        transaction_collection.insert_one(transaction_data)
        seat_sums = {seat: 0 for seat in 'ABC'}
        for item in updated_table['users']:
            if item['UID'] == UID and item['seat'] in seat_sums:
                seat_sums[item['seat']] += item['amount']
        if id != prev_gameId:
            client.set("fruit_prev_gameId",js.dumps(id))
            # prev_gameId=updated_table["_id"]
            portUpdate={
            "A_total_amount":0,
            "B_total_amount":0,
            "C_total_amount":0
            }
            client.set("fruit_portUpdate",js.dumps(portUpdate))
        finalResult = randomGenrate(updated_table)
        return {
            "success": True,
            "msg": "Amount added successfully",
            "data":{
                "sum_A": seat_sums['A'],
                "sum_B": seat_sums['B'],
                "sum_C": seat_sums['C'],
                "A_total_amount": finalResult['A_total_amount'],
                "B_total_amount": finalResult['B_total_amount'],
                "C_total_amount": finalResult['C_total_amount']
            },
            "currentBalance":updated_balance["Udiamonds"]
        }
    else:
        credit_balance = user_login_table.find_one_and_update(
            {"_id": table_balance["_id"]},
            {"$inc": {"Udiamonds": amount}},
            return_document=ReturnDocument.AFTER
        )
        if not credit_balance or int(credit_balance["Udiamonds"]) - int(amount) != user_diamond:
            # raise HTTPException(status_code=500, detail="Something went wrong")
            return{
                "success":False,
                "msg":"Something went wrong"
            }
        # raise HTTPException(status_code=500, detail="Something went wrong")
        return{
            "success":False,
            "msg":"Something went wrong"
        }

# Check game is already Announced or not if yes then send the response
# Prepare data playing user of the game in 24 hours
# If len(doc['user']) == 0 then select the random winner



def helptofindwinner(data,flag=False):
    if flag:
        # Return the port with the highest value
        return max(data, key=data.get)
    if any(value > 0 for value in data.values()):
        return max(data, key = lambda k: (data[k] >= 0, -data[k]))
    # If all values are negative, return the one with the least negative value
    else:
        return max(data, key = data.get)

def helptosendresponse(doc,winner,id,winnerUsers=[]):
    for ele in doc["users"]:
        if ele["seat"]==winner:
            winnerUsers.append(ele)
    if len(winnerUsers)==0:
        return JSONResponse(status_code=200, content=fruit_game_boat(winner,id))
    else:
        return JSONResponse(status_code=200, content=new_credit_diamonds(winner,winnerUsers,id))

#PROGRESS: Optimize the code

# @router.get("/winner-announcement/{id}") 
# async def winner_announcement(id: str):
#     winningRatio = 3.0
#     try:
#         doc = table_collection.find_one({'_id': ObjectId(id)}) # Get the game data
#         if doc is None:
#             return JSONResponse(status_code=404, content={"success": False, "msg": "No data found"})
#         if doc["game_status"] == "ended" or doc["winnerAnnounced"] == "yes": # Check the game status
#             return JSONResponse(status_code=200, content={
#                 "success": True,
#                 "msg": "Winner already declared",
#                 "winnerSeat": doc["winnedSeat"],
#                 "data": doc["winnedSeat"],
#                 "WiningAmount": doc["WiningAmount"],
#                 "TopUserWinner": doc["TopUserWinner"]
#             })
#         if doc["game_status"] == "active": # Check the game status
#             if len(doc["users"]) == 0: # Here Goes the code When no user found in the game
#                 luck = ['A', 'B', 'C']
#                 winner = random.choice(luck)
#                 return JSONResponse(status_code=200, content=fruit_game_boat(winner, id))
#             else:
#                 if client.exists("fruitRC"): # Here Goes the code When fruitRC exist in redis
#                     winnerUsers = []
#                     exist_rc = int(client.get("fruitRC"))
#                     counter = int(client.get("fruitCounter"))
#                     total_bidding = int(doc['seat']['A_total_amount']) + int(doc['seat']['B_total_amount']) + int(doc['seat']['C_total_amount'])
#                     A_winning = total_bidding - int(doc['seat']['A_total_amount']) * winningRatio
#                     B_winning = total_bidding - int(doc['seat']['B_total_amount']) * winningRatio
#                     C_winning = total_bidding - int(doc['seat']['C_total_amount']) * winningRatio
#                     rc_on_port_a = int(A_winning) + int(exist_rc)
#                     rc_on_port_b = int(B_winning) + int(exist_rc)
#                     rc_on_port_c = int(C_winning) + int(exist_rc)
#                     candidate_winner_port = {"A": rc_on_port_a, "B": rc_on_port_b, "C": rc_on_port_c}
#                     #DONE: First check the counter value is greater than defined value e.g like 5 or 500
#                     if counter >= 5: # Here Goes the code When counter greater than 5 or exceed the defined value
#                         if exist_rc >= 0: # Here Goes the code When rc greater than 0
#                             #DONE: When counter exceed and rc greater than 0 then declare the winner to minium rc_port and update the rc and counter to 0
#                             winner = helptofindwinner(candidate_winner_port,True) 
#                             newRC = candidate_winner_port[winner]
#                             if newRC >= 0: #DONE: When newRC greater than 0
#                                 client.incrby("fruitGameRev", int(newRC))
#                                 client.set("fruitRC", 0)
#                                 client.set("fruitCounter", 0)
#                                 return helptosendresponse(doc,winner,id,winnerUsers)
#                             else: #DONE: When newRC less than 0
#                                 client.set("fruitRC", int(newRC))
#                                 client.incrby("fruitCounter", 1)
#                                 return helptosendresponse(doc,winner,id,winnerUsers)
#                         else: # Here Goes the code When rc less than 0
#                             #DONE: When counter exceed and rc less than 0 then declare the winner to maximum rc_port
#                             winner = helptofindwinner(candidate_winner_port,True) 
#                             newRC = candidate_winner_port[winner]
#                             client.set("fruitRC", int(newRC))
#                             client.incrby("fruitCounter", 1)
#                             return helptosendresponse(doc,winner,id,winnerUsers)
#                     else: # DONE: Here Goes the code When counter less than 5 or less than the defined value
#                         winner = helptofindwinner(candidate_winner_port)
#                         newRC = candidate_winner_port[winner]
#                         client.set("fruitRC", int(newRC))
#                         client.incrby("fruitCounter", 1)
#                         return helptosendresponse(doc,winner,id,winnerUsers)
#                 else: #DONE: Here Goes the code When fruitRC not exist in redis
#                     luck = ['A', 'B', 'C']
#                     winner = random.choice(luck)
#                     total_winning = 0
#                     total_bidding = int(doc['seat']['A_total_amount'] ) + int( doc['seat']['B_total_amount']) + int(doc['seat']['C_total_amount'])
#                     if winner == 'A':
#                         total_winning = int(doc['seat']['A_total_amount']) * winningRatio
#                     elif winner == 'B':
#                         total_winning = int(doc['seat']['B_total_amount']) * winningRatio
#                     else:
#                         total_winning = int(doc['seat']['C_total_amount'] ) * winningRatio
#                     newRC=total_bidding - total_winning
#                     client.set("fruitRC",int(newRC))
#                     client.set("fruitCounter", 1)
#                     return helptosendresponse(doc,winner,id)
#         else:
#             return JSONResponse(status_code=404, content={"success": False, "msg": "Something went wrong"})
#     except Exception as err:
#         import traceback # NOTE: Not for production
#         tb_str = ''.join(traceback.format_exception(etype=type(err), value=err, tb=err.__traceback__)) # NOTE: Not for production
        
#         # Send the JSONResponse with detailed traceback
#         return JSONResponse(
#             status_code=404,
#             content={
#                 "success": False,
#                 "msg": str(err),
#                 "traceback": tb_str # NOTE: Not for production
#             }
#         )




@router.get("/winner-announcement/{id}")
async def winner_announced(id: str):
    try:
        doc=table_collection.find_one({'_id': ObjectId(id)})
        if doc is None:
            raise HTTPException(status_code=404, detail="No data found")
        if doc["game_status"] == "ended" or doc["winnerAnnounced"] == "yes":
            return {
                "success": True,
                "msg": "Winner already declared",
                "winnerSeat":doc["winnedSeat"],
                "data":doc["winnedSeat"],
                "WiningAmount":doc["WiningAmount"],
                "TopUserWinner":doc["TopUserWinner"]
            }
        if doc["game_status"] == "active":
            if len(doc["users"]) == 0:
                luck = ['A', 'B', 'C']
                winner = random.choice(luck)
                return fruit_game_boat(winner,id)
            else:
                if client.exists("fruitRC"):
                    winnerUsers=[]
                    exist_rc= client.get("fruitRC")
                    counter=client.get("fruitCounter")
                    total_bidding = int(doc['seat']['A_total_amount']) + int(doc['seat']['B_total_amount']) + int(doc['seat']['C_total_amount'])
                    A_winning = total_bidding - int(doc['seat']['A_total_amount']) * 3
                    B_winning = total_bidding - int(doc['seat']['B_total_amount']) * 3
                    C_winning = total_bidding - int(doc['seat']['C_total_amount']) * 3
                    rc_on_port_a = int(A_winning) + int(exist_rc)
                    rc_on_port_b = int(B_winning) + int(exist_rc)
                    rc_on_port_c = int(C_winning) + int(exist_rc)
                    newRC = 0
                    counter = int(counter)
                    exist_rc = int(exist_rc)
                    winner = ""
                    if counter>=5000:
                        # when counter greater than 5
                        if exist_rc > 0:
                            # when rc greater than 0
                            if rc_on_port_a >= 0 and rc_on_port_b >= 0 and rc_on_port_c >= 0:
                                if rc_on_port_a <= rc_on_port_b and rc_on_port_a <= rc_on_port_c:
                                    newRC = rc_on_port_a
                                    winner = "A"
                                elif rc_on_port_b <= rc_on_port_a and rc_on_port_b <= rc_on_port_c:
                                    newRC = rc_on_port_b
                                    winner = "B"
                                else:
                                    newRC = rc_on_port_c
                                    winner = "C"
                            elif rc_on_port_a <= 0 and rc_on_port_b >= 0 and rc_on_port_c >= 0:
                                if rc_on_port_b <= rc_on_port_c:
                                    newRC = rc_on_port_b
                                    winner = "B"
                                else:
                                    newRC = rc_on_port_c
                                    winner = "C"
                            elif rc_on_port_b <= 0 and rc_on_port_a >= 0 and rc_on_port_c >= 0:
                                if rc_on_port_a <= rc_on_port_c:
                                    newRC = rc_on_port_a
                                    winner = "A"
                                else:
                                    newRC = rc_on_port_c
                                    winner = "C"
                            elif rc_on_port_c <= 0 and rc_on_port_a >= 0 and rc_on_port_b >= 0:
                                if rc_on_port_b <= rc_on_port_a:
                                    newRC = rc_on_port_b
                                    winner = "B"
                                else:
                                    newRC = rc_on_port_a
                                    winner = "A"
                            elif rc_on_port_a <= 0 and rc_on_port_b <= 0 and rc_on_port_c <= 0:
                                if rc_on_port_a >= rc_on_port_b and rc_on_port_a >= rc_on_port_c:
                                    newRC = rc_on_port_a
                                    winner = "A"
                                elif rc_on_port_b >= rc_on_port_c and rc_on_port_b >= rc_on_port_a:
                                    newRC = rc_on_port_b
                                    winner = "B"
                                else:
                                    newRC = rc_on_port_c
                                    winner = "C"
                            if winner =="":
                                winner = "A"
                                newRC = rc_on_port_a
                            client.incrby("fruitGameRev", int(newRC))
                            client.set("fruitRC", 0)
                            client.set("fruitCounter", 0)
                            for ele in doc["users"]:
                                if ele["seat"]==winner:
                                    winnerUsers.append(ele)
                            if len(winnerUsers)==0:
                                return fruit_game_boat(winner,id)
                            else:
                                return new_credit_diamonds(winner,winnerUsers,id)

                        else:
                            # when rc less than 0
                            if A_winning >= B_winning and A_winning >= C_winning:
                                winner = "A"
                                newRC = rc_on_port_a
                            elif B_winning >= C_winning and B_winning >= A_winning:
                                winner = "B"
                                newRC = rc_on_port_b
                            else:
                                winner = "C"
                                newRC = rc_on_port_c

                            if winner =="":
                                winner = "A"
                                newRC = rc_on_port_a
                            client.set("fruitRC", int(newRC))
                            client.incrby("fruitCounter", 1)
                            for ele in doc["users"]:
                                if ele["seat"]==winner:
                                    winnerUsers.append(ele)
                            if len(winnerUsers)==0:
                                return fruit_game_boat(winner,id)
                            else:
                                return new_credit_diamonds(winner,winnerUsers,id)
                    else:
                        # when counter less than 5
                        if exist_rc==0:
                            #when rc equal to 0
                            luck = ['A', 'B', 'C']
                            winner = random.choice(luck)
                            total_winning = 0
                            total_bidding =int( doc['seat']['A_total_amount']) + int(doc['seat']['B_total_amount']) + int(doc['seat']['C_total_amount'])
                            if winner == 'A':
                                total_winning = int(doc['seat']['A_total_amount']) * 3.0
                            elif winner == 'B':
                                total_winning = int(doc['seat']['B_total_amount']) * 3.0
                            else:
                                total_winning = int(doc['seat']['C_total_amount']) * 3.0
                            rc=total_bidding-total_winning
                            client.set("fruitRC",int(rc))
                            client.incrby("fruitCounter", 1)
                            winnerUsers=[]
                            for ele in doc["users"]:
                                if ele["seat"]==winner:
                                    winnerUsers.append(ele)
                            if len(winnerUsers)==0:
                                return fruit_game_boat(winner,id)
                            else:
                                return new_credit_diamonds(winner,winnerUsers,id)
                        elif exist_rc>0:
                            #when rc greater than 0
                            if rc_on_port_a >= 0 and rc_on_port_b >= 0 and rc_on_port_c >= 0:
                                if rc_on_port_a <= rc_on_port_b and rc_on_port_a <= rc_on_port_c:
                                    newRC = rc_on_port_a
                                    winner = "A"
                                elif rc_on_port_b <= rc_on_port_a and rc_on_port_b <= rc_on_port_c:
                                    newRC = rc_on_port_b
                                    winner = "B"
                                else:
                                    newRC = rc_on_port_c
                                    winner = "C"
                            elif rc_on_port_a <= 0 and rc_on_port_b >= 0 and rc_on_port_c >= 0:
                                if rc_on_port_b <= rc_on_port_c:
                                    newRC = rc_on_port_b
                                    winner = "B"
                                else:
                                    newRC = rc_on_port_c
                                    winner = "C"
                            elif rc_on_port_b <= 0 and rc_on_port_a >= 0 and rc_on_port_c >= 0:
                                if rc_on_port_a <= rc_on_port_c:
                                    newRC = rc_on_port_a
                                    winner = "A"
                                else:
                                    newRC = rc_on_port_c
                                    winner = "C"
                            elif rc_on_port_c <= 0 and rc_on_port_a >= 0 and rc_on_port_b >= 0:
                                if rc_on_port_b <= rc_on_port_a:
                                    newRC = rc_on_port_b
                                    winner = "B"
                                else:
                                    newRC = rc_on_port_a
                                    winner = "A"
                            elif rc_on_port_a <= 0 and rc_on_port_b <= 0 and rc_on_port_c <= 0:
                                if rc_on_port_a >= rc_on_port_b and rc_on_port_a >= rc_on_port_c:
                                    newRC = rc_on_port_a
                                    winner = "A"
                                elif rc_on_port_b >= rc_on_port_c and rc_on_port_b >= rc_on_port_a:
                                    newRC = rc_on_port_b
                                    winner = "B"
                                else:
                                    newRC = rc_on_port_c
                                    winner = "C"
                            elif rc_on_port_a <= 0 and rc_on_port_b <= 0 and rc_on_port_c >= 0:
                                newRC = rc_on_port_c
                                winner = "C"
                            elif rc_on_port_a <= 0 and rc_on_port_b >= 0 and rc_on_port_c <= 0:
                                newRC = rc_on_port_b
                                winner = "B"
                            elif rc_on_port_a >= 0 and rc_on_port_b <= 0 and rc_on_port_c <= 0:
                                newRC = rc_on_port_a
                                winner = "A"
                            if winner=="":
                                newRC = rc_on_port_a
                                winner = "A"
                            client.set("fruitRC", int(newRC))
                            client.incrby("fruitCounter", 1)
                            for ele in doc["users"]:
                                if ele["seat"]==winner:
                                    winnerUsers.append(ele)
                            if len(winnerUsers)==0:
                                return fruit_game_boat(winner,id)
                            else:
                                return new_credit_diamonds(winner,winnerUsers,id)
                        elif exist_rc<0:
                            #when rc less than 0
                            if rc_on_port_a <= 0 and rc_on_port_b <= 0 and rc_on_port_c <= 0:
                                if rc_on_port_a >= rc_on_port_b and rc_on_port_a >= rc_on_port_c:
                                    newRC = rc_on_port_a
                                    winner = "A"
                                elif rc_on_port_b >= rc_on_port_a and rc_on_port_b >= rc_on_port_c:
                                    newRC = rc_on_port_b
                                    winner = "B"
                                else:
                                    newRC = rc_on_port_c
                                    winner = "C"
                            elif rc_on_port_a >= 0 and rc_on_port_b >= 0 and rc_on_port_c >= 0:
                                if rc_on_port_a <= rc_on_port_b and rc_on_port_a <= rc_on_port_c:
                                    newRC = rc_on_port_a
                                    winner = "A"
                                elif rc_on_port_b <= rc_on_port_a and rc_on_port_b <= rc_on_port_c:
                                    newRC = rc_on_port_b
                                    winner = "B"
                                else:
                                    winner = "C"
                            elif rc_on_port_a >= 0 and rc_on_port_b <= 0 and rc_on_port_c <= 0:
                                newRC = rc_on_port_a
                                winner = "A"
                            elif rc_on_port_b >= 0 and rc_on_port_a <= 0 and rc_on_port_c <= 0:
                                newRC = rc_on_port_b
                                winner = "B"
                            elif rc_on_port_c >= 0 and rc_on_port_a <= 0 and rc_on_port_b <= 0:
                                newRC = rc_on_port_c
                                winner = "C"
                            elif rc_on_port_a <= 0 and rc_on_port_b >= 0 and rc_on_port_c >= 0:
                                if rc_on_port_b <= rc_on_port_c:
                                    newRC = rc_on_port_b
                                    winner = "B"
                                else:
                                    newRC = rc_on_port_c
                                    winner = "C"
                            elif rc_on_port_b <= 0 and rc_on_port_a >= 0 and rc_on_port_c >= 0:
                                if rc_on_port_a <= rc_on_port_c:
                                    newRC = rc_on_port_a
                                    winner = "A"
                                else:
                                    newRC = rc_on_port_c
                                    winner = "C"
                            elif rc_on_port_c <= 0 and rc_on_port_a >= 0 and rc_on_port_b >= 0:
                                if rc_on_port_a <= rc_on_port_b:
                                    newRC = rc_on_port_a
                                    winner = "A"
                                else:
                                    newRC = rc_on_port_b
                                    winner = "B"

                            if winner == "":
                                newRC = rc_on_port_a
                                winner = "A"
                            client.set("fruitRC", int(newRC))
                            client.incrby("fruitCounter", 1)
                            for ele in doc["users"]:
                                if ele["seat"]==winner:
                                    winnerUsers.append(ele)
                            if len(winnerUsers)==0:
                                return fruit_game_boat(winner,id)
                            else:
                                return new_credit_diamonds(winner,winnerUsers,id)

                else:
                    luck = ['A', 'B', 'C']
                    winner = random.choice(luck)
                    total_winning = 0
                    total_bidding = int(doc['seat']['A_total_amount'] ) + int( doc['seat']['B_total_amount']) + int(doc['seat']['C_total_amount'])
                    if winner == 'A':
                        total_winning = int(doc['seat']['A_total_amount']) * 3
                    elif winner == 'B':
                        total_winning = int(doc['seat']['B_total_amount']) * 3
                    else:
                        total_winning = int(doc['seat']['C_total_amount'] ) * 3
                    rc=total_bidding-total_winning
                    client.set("fruitRC",int(rc))
                    client.set("fruitCounter", 1)
                    winnerUsers=[]
                    for ele in doc["users"]:
                        if ele["seat"] == winner:
                            winnerUsers.append(ele)
                    if len(winnerUsers)==0:
                        return fruit_game_boat(winner,id)
                    else:
                        return new_credit_diamonds(winner, winnerUsers, id)
                        
              
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))


@router.get("/resulthistory")
async def result_history(): 
    try:
        result = table_collection.find(
        {"game_status": "ended"},
        {"winnedSeat": 1, "_id": 0}
        ).sort([("_id", -1)]).limit(7)
        if result is None:
            return {
                "success":False,
                "msg": "No result found"
                }
        else:
            return {
                "success":True,
                "msg": "Result found",
                "data": list(result)
            }
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))
 


@router.get('/newUser-bid/{game_id}/{user_id}')
async def userBid(game_id:str,user_id:str):
    return {
        "success":True,
        "msg":"Data found"
    }



# portUpdate={
#     "A_total_amount":0,
#     "B_total_amount":0,
#     "C_total_amount":0
# }
# def randomGenrate(result):
#     global portUpdate
#     port = [1000,5000,10000,50000]
#     portRndm1 = random.randint(1,3)
#     portRndm2 = random.randint(1,3)
#     portRndm3 = random.randint(1,3)
#     rndmn = random.randint(1, 3)
#     if rndmn == 1:
#         # add number on port any one
#         rndmn1 = random.randint(1,3)
#         if rndmn1 == 1:
#             portUpdate['A_total_amount']+=port[portRndm1]
#             portUpdate['A_total_amount']+=result[0]['seat']['A_total_amount']
#             return portUpdate
#         elif rndmn1 == 2:
#             portUpdate['B_total_amount']+=port[portRndm2]
#             portUpdate['B_total_amount']+=result[0]['seat']['B_total_amount']
#             return portUpdate
#         else:
#             portUpdate['C_total_amount']+=port[portRndm3]
#             portUpdate['C_total_amount']+=result[0]['seat']['C_total_amount']
#             return portUpdate
#     elif rndmn == 2:
#         # add number on port two A and B or A and C or 
#         rndmn2 = random.randint(1,3)
#         if rndmn2 == 1:
#             portUpdate['A_total_amount']+=port[portRndm1]
#             portUpdate['A_total_amount']+=result[0]['seat']['A_total_amount']
#             portUpdate['B_total_amount']+=port[portRndm2]
#             portUpdate['B_total_amount']+=result[0]['seat']['B_total_amount']
#             return portUpdate # add here in port A and B
#         elif rndmn2 == 2:
#             portUpdate['B_total_amount']+=port[portRndm2]
#             portUpdate['B_total_amount']+=result[0]['seat']['B_total_amount']
#             portUpdate['C_total_amount']+=port[portRndm3]
#             portUpdate['C_total_amount']+=result[0]['seat']['C_total_amount']
#             return portUpdate # add here in port B and C
#         else:
#             portUpdate['C_total_amount']+=port[portRndm3]
#             portUpdate['C_total_amount']+=result[0]['seat']['C_total_amount']
#             portUpdate['A_total_amount']+=port[portRndm1]
#             portUpdate['A_total_amount']+=result[0]['seat']['A_total_amount']
#             return portUpdate # add here in port C and A
#     else:
#         # add here on every port
#         portUpdate['C_total_amount']+=port[portRndm3]
#         portUpdate['C_total_amount']+=result[0]['seat']['C_total_amount']
#         portUpdate['A_total_amount']+=port[portRndm1]
#         portUpdate['A_total_amount']+=result[0]['seat']['A_total_amount']
#         portUpdate['B_total_amount']+=port[portRndm2]
#         portUpdate['B_total_amount']+=result[0]['seat']['B_total_amount']
#         return portUpdate

    

# prev_gameId=None
# @router.get('/user-bid/{game_id}/{user_id}')
# async def user_bid(game_id: str, user_id: str):
#     global portUpdate
#     global prev_gameId
#     try:
#         pipeline = [
#             {"$match": {"_id": ObjectId(game_id)}},
#         ]
#         result = list(table_collection.aggregate(pipeline))
#         sum_A = sum(item['amount'] for item in result[0]['users'] if item['user_id'] == user_id and item['seat'] == 'A')
#         sum_B = sum(item['amount'] for item in result[0]['users'] if item['user_id'] == user_id and item['seat'] == 'B')
#         sum_C = sum(item['amount'] for item in result[0]['users'] if item['user_id'] == user_id and item['seat'] == 'C')
#         if game_id != prev_gameId:
#             prev_gameId=game_id
#             portUpdate['A_total_amount']=0
#             portUpdate['B_total_amount']=0
#             portUpdate['C_total_amount']=0
#         finalResult = randomGenrate(result)
#         return {
#             "success": True,
#             "msg": "User bid found",
#             "data": {
#                 "sum_A": sum_A,
#                 "sum_B": sum_B,
#                 "sum_C": sum_C,
#                 "A_total_amount": finalResult['A_total_amount'],
#                 "B_total_amount": finalResult['B_total_amount'],
#                 "C_total_amount": finalResult['C_total_amount']
#             },
#         } 
#     except Exception as err:
#         raise HTTPException(status_code=500, detail=str(err))   



@router.get("/delete-empty-documents")
async def delete_empty_documents():
    try:
        table_collection.delete_many({"users": []})
        return {
            "success": True,
            "msg": "Deleted successfully"
        }
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))