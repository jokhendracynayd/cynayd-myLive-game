#PRODUCTION SERVER

from models.m_greedy_game import Greedy, Seat
from fastapi import APIRouter, HTTPException
from config.redis import client
from config.db import db
from bson import ObjectId
import secrets
import datetime
import random
import json as js
from pymongo import ReturnDocument
from pydantic import BaseModel,json
from fastapi.responses import JSONResponse
from utils.greedy_game import greedy_game_boat
json.ENCODERS_BY_TYPE[ObjectId]=str
router = APIRouter()
table_collection = db['greedies']
transaction_collection = db["transactions"]
user_login_table = db["user_logins"]
from controllers.credit_diamonds import credit_greedy_diamonds
class UpdateSeatAmountRequest(BaseModel):
    UID: str
    amount: float
    seat: str

async def check_active_game_and_end():
    try:
        docs = table_collection.find({"game_status": "active"})
        for doc in docs:
            isExist = client.get(f"{doc['_id']}")
            if isExist is None:
                try:
                    await winner_announcement(doc['_id'])
                except Exception as error:
                    print(error)
            elif isExist is not None and doc["game_last_count"] <= 0:
                try:
                    await winner_announcement(doc['_id'])
                except Exception as error:
                    print(error)

    except Exception as err:
        print(err)

@router.get("/create")
async def create():
    try:
        greedy_game =  client.get("greedy_game")
        if greedy_game is None:
            greedy=Greedy(seat=Seat())
            greedy_dict = greedy.dict()
            doc_id=table_collection.insert_one(greedy_dict).inserted_id
            doc=table_collection.find_one({"_id":ObjectId(doc_id)})
            client.setex(str(doc_id), 32, str(doc["_id"])),
            client.setex("greedy_game", 28, str(doc["_id"])),
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
            ttl =  client.ttl("greedy_game")
            if ttl >= 10:
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



def randomGenrate(result):
    portUpdate = client.get("greedy_portUpdate")
    portUpdate=js.loads(portUpdate)
    port = [100,1000,1000,10000]
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
            client.set("greedy_portUpdate",js.dumps(portUpdate))
            return portUpdate
        elif rndmn1 == 2:
            portUpdate['B_total_amount']+=port[portRndm2]
            portUpdate['B_total_amount']+=result['seat']['B_total_amount']
            client.set("greedy_portUpdate",js.dumps(portUpdate))
            return portUpdate
        else:
            portUpdate['C_total_amount']+=port[portRndm3]
            portUpdate['C_total_amount']+=result['seat']['C_total_amount']
            client.set("greedy_portUpdate",js.dumps(portUpdate))
            return portUpdate
    elif rndmn == 2:
        # add number on port two A and B or A and C or 
        rndmn2 = random.randint(1,3)
        if rndmn2 == 1:
            portUpdate['A_total_amount']+=port[portRndm1]
            portUpdate['A_total_amount']+=result['seat']['A_total_amount']
            portUpdate['B_total_amount']+=port[portRndm2]
            portUpdate['B_total_amount']+=result['seat']['B_total_amount']
            client.set("greedy_portUpdate",js.dumps(portUpdate))
            return portUpdate # add here in port A and B
        elif rndmn2 == 2:
            portUpdate['B_total_amount']+=port[portRndm2]
            portUpdate['B_total_amount']+=result['seat']['B_total_amount']
            portUpdate['C_total_amount']+=port[portRndm3]
            portUpdate['C_total_amount']+=result['seat']['C_total_amount']
            client.set("greedy_portUpdate",js.dumps(portUpdate))
            return portUpdate # add here in port B and C
        else:
            portUpdate['C_total_amount']+=port[portRndm3]
            portUpdate['C_total_amount']+=result['seat']['C_total_amount']
            portUpdate['A_total_amount']+=port[portRndm1]
            portUpdate['A_total_amount']+=result['seat']['A_total_amount']
            client.set("greedy_portUpdate",js.dumps(portUpdate))
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



# @router.get('/user-bid/{game_id}/{user_id}')
# async def user_bid(game_id: str, user_id: str):
#     portUpdate = client.get("fruit_portUpdate")
#     prev_gameId=client.get("fruit_prev_gameId")
#     if prev_gameId is None:
#         prev_gameId=None
#     else:
#         prev_gameId=js.loads(prev_gameId)
#     if portUpdate is None:
#         portUpdate={
#             "A_total_amount":0,
#             "B_total_amount":0,
#             "C_total_amount":0
#         }
#         client.set("fruit_portUpdate",js.dumps(portUpdate))
#     try:
#         pipeline = [
#             {"$match": {"_id": ObjectId(game_id)}},
#         ]
#         result = list(table_collection.aggregate(pipeline))
#         sum_A = sum(item['amount'] for item in result[0]['users'] if item['user_id'] == user_id and item['seat'] == 'A')
#         sum_B = sum(item['amount'] for item in result[0]['users'] if item['user_id'] == user_id and item['seat'] == 'B')
#         sum_C = sum(item['amount'] for item in result[0]['users'] if item['user_id'] == user_id and item['seat'] == 'C')
#         if game_id != prev_gameId:
#             # prev_gameId=game_id
#             client.set("fruit_prev_gameId",js.dumps(game_id))
#             portUpdate={
#             "A_total_amount":0,
#             "B_total_amount":0,
#             "C_total_amount":0
#             }
#             client.set("fruit_portUpdate",js.dumps(portUpdate))
#         finalResult = randomGenrate(result[0])
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
#         raise JSONResponse(status_code=500, detail=str(err))   



@router.get('/wallet-balance/{UID}')
async def walletBalance(UID:str):
    if not UID or UID=="null":
        return JSONResponse(status_code=400, content={"success": False, "msg": "Invalid data"})
    table_balance = user_login_table.find_one({"UID": UID},{"Udiamonds":1})
    print(table_balance)
    return JSONResponse(status_code=200, content={
        "data":{
            "diamond":table_balance["Udiamonds"]
            },
        "success":True,
        "msg":"Wallet balance"
    })

@router.put("/updateSeatAmount/{id}")
async def update_seat_amount(id: str, request: UpdateSeatAmountRequest):
    try:
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
            return JSONResponse(status_code=404, content={"success": False, "msg": "No data found"})

        if table["game_status"] == "ended" or table["winnerAnnounced"] == "yes":
            return JSONResponse(status_code=400, content={"success": False, "msg": "This game has ended, please wait"})

        table_balance = user_login_table.find_one({"UID": UID},{"Udiamonds":1})

        if not table_balance:
            return JSONResponse(status_code=404, content={"success": False, "msg": "No data found"})
    
        user_diamond = table_balance["Udiamonds"]
        if user_diamond < amount:
            return JSONResponse(status_code=400, content={"success": False, "msg": "Insufficient balance"})
    
        update_obj = {"$push": {"users": {"UID": UID, "seat": seat, "amount": amount}}}
        seat_total_amount_field = {
            "A": "seat.A_total_amount",
            "B": "seat.B_total_amount",
            "C": "seat.C_total_amount",
            "D": "seat.D_total_amount",
            "E": "seat.E_total_amount",
            "F": "seat.F_total_amount",
            "G": "seat.G_total_amount",
            "H": "seat.H_total_amount",
        }
        if seat in seat_total_amount_field:
            update_obj["$inc"] = {seat_total_amount_field[seat]: amount}
        updated_balance = user_login_table.find_one_and_update(
            {"_id": table_balance["_id"]},
            {"$inc": {"Udiamonds": - amount}},
            return_document=ReturnDocument.AFTER
        )
        if not updated_balance or int(updated_balance["Udiamonds"]) + int(amount) != user_diamond:
            return JSONResponse(status_code=500, content={"success": False, "msg": "Something went wrong"})

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
                    "game_name": "greedy"
                }
            }
            transaction_collection.insert_one(transaction_data)
            seat_sums = {seat: 0 for seat in 'ABCDEFGH'}
            for item in updated_table['users']:
                if item['UID'] == UID and item['seat'] in seat_sums:
                    seat_sums[item['seat']] += item['amount']       
            return JSONResponse(status_code=200, content={"success": True, "msg": "Seat amount updated successfully", "data": {
                "sum_A": seat_sums["A"],
                "sum_B": seat_sums["B"],
                "sum_C": seat_sums["C"],
                "sum_D": seat_sums["D"],
                "sum_E": seat_sums["E"],
                "sum_F": seat_sums["F"],
                "sum_G": seat_sums["G"],
                "sum_H": seat_sums["H"],
                "A_total_amount": updated_table["seat"]["A_total_amount"],
                "B_total_amount": updated_table["seat"]["B_total_amount"],
                "C_total_amount": updated_table["seat"]["C_total_amount"],
                "D_total_amount": updated_table["seat"]["D_total_amount"],
                "E_total_amount": updated_table["seat"]["E_total_amount"],
                "F_total_amount": updated_table["seat"]["F_total_amount"],
                "G_total_amount": updated_table["seat"]["G_total_amount"],
                "H_total_amount": updated_table["seat"]["H_total_amount"],
            },
            "currentBalance":updated_balance["Udiamonds"]
            })
        else:
            credit_balance = user_login_table.find_one_and_update(
                {"_id": table_balance["_id"]},
                {"$inc": {"Udiamonds": amount}},
                return_document=ReturnDocument.AFTER
            )
            if not credit_balance or int(credit_balance["Udiamonds"]) - int(amount) != user_diamond:
                return JSONResponse(status_code=500, content={"success": False, "msg": "Something went wrong"})
            return JSONResponse(status_code=500, content={"success": False, "msg": "Something went wrong"})
    except Exception as err:
        import traceback # NOTE: Not for production
        tb_str = ''.join(traceback.format_exception(etype=type(err), value=err, tb=err.__traceback__)) # NOTE: Not for production
        
        # Send the JSONResponse with detailed traceback
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "msg": str(err),
                "traceback": tb_str # NOTE: Not for production
            }
        )


@router.get("/today-user-profit/{UID}")
async def today_user_profit(UID: str):
    try:
        import datetime
        # Get the current date and time
        now = datetime.datetime.now()
        midnight_today = datetime.datetime(now.year, now.month, now.day)
        pipeline = [
            {
                "$match": {
                    "transaction_date": {"$gte": midnight_today},
                    "sender_UID": UID,
                    "transaction_type": "credited"
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_transaction_amount": {"$sum": "$transaction_amount"}
                }
            }
        ]

        # Execute the aggregation pipeline
        result = list(transaction_collection.aggregate(pipeline))

        # Extract the total transaction amount
        total_transaction_amount = result[0]["total_transaction_amount"] if result else 0
        return JSONResponse(status_code=200,content={"success": True, "msg": "Today's user profit", "data": total_transaction_amount})
    except Exception as err:
        return JSONResponse(status_code=500, content={"success": False, "msg": str(err)})

@router.get("/today-total-profit")
async def today_total_profit():
    try:
        import datetime
        # Get the current date and time
        now = datetime.datetime.now()
        midnight_today = datetime.datetime(now.year, now.month, now.day)
        pipeline = [
            {
                "$match": {
                    "transaction_date": {"$gte": midnight_today},
                    "transaction_type": "credited"
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_transaction_amount": {"$sum": "$transaction_amount"}
                }
            }
        ]

        # Execute the aggregation pipeline
        result = list(transaction_collection.aggregate(pipeline))

        # Extract the total transaction amount
        total_transaction_amount = result[0]["total_transaction_amount"] if result else 0
        return JSONResponse(status_code=200,content={"success": True, "msg": "Today's Total profit", "data": total_transaction_amount})
    except Exception as err:
        return JSONResponse(status_code=500, content={"success": False, "msg": str(err)})


@router.get("/tody-total-round")
async def todayTotalRound():
    try:
        import datetime
        # Get the current date and time
        now = datetime.datetime.now()
        midnight_today = datetime.datetime(now.year, now.month, now.day)
        # Find all where time greate then
        total_round = table_collection.count_documents({"created_at": {"$gte": midnight_today}})
        return JSONResponse(status_code=200 ,content={"success":True , "msg":"Total round of today","data":total_round})
    except Exception as err:
        return JSONResponse(status_code=500, content={"success": False, "msg": str(err)})


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
        return JSONResponse(status_code=200, content=greedy_game_boat(winner,id))
    else:
        return JSONResponse(status_code=200, content=credit_greedy_diamonds(winner,winnerUsers,id))

#PROGRESS: Optimize the code

def checkPizzaSladWin(total_bidding,doc,exist_rc ,id):
    A_winning = total_bidding - int(doc['seat']['A_total_amount']) * 7.0
    B_winning = total_bidding - int(doc['seat']['B_total_amount']) * 7.0
    C_winning = total_bidding - int(doc['seat']['C_total_amount']) * 7.0
    D_winning = total_bidding - int(doc['seat']['D_total_amount']) * 7.0
    
    E_winning = total_bidding - int(doc['seat']['E_total_amount']) * 5.0
    F_winning = total_bidding - int(doc['seat']['F_total_amount']) * 5.0
    G_winning = total_bidding - int(doc['seat']['G_total_amount']) * 5.0
    H_winning = total_bidding - int(doc['seat']['H_total_amount']) * 5.0
    
    totalslad = E_winning + F_winning + G_winning + H_winning
    totalpizza = A_winning + B_winning + C_winning + D_winning
    
    rc_on_port_pizza = int(totalpizza) + int(exist_rc)
    rc_on_port_slad = int(totalslad) + int(exist_rc)
    candidate_winner_port = {"Pizza": rc_on_port_pizza, "Slad": rc_on_port_slad}
    winner = helptofindwinner(candidate_winner_port,True)
    winnerUsers = []
    if candidate_winner_port[winner] < 0:
        return False
    seat = []
    if winner == "Pizza":
        seat = ["A","B","C","D"]
    else:
        seat = ["E","F","G","H"]
    client.incrby("greedyGameRev", int(candidate_winner_port[winner]))
    for ele in doc["users"]:
        if ele["seat"] in seat:
            winnerUsers.append(ele)
    if len(winnerUsers)==0:
        return JSONResponse(status_code=200, content=greedy_game_boat(winner,id))
    else:
        return JSONResponse(status_code=200, content=credit_greedy_diamonds(winner,winnerUsers,id,{"Slad": 5.0,"Pizza": 7.0}))  
    
    
    

    
@router.get("/winner-announcement/{id}") 
async def winner_announcement(id: str):
    winnerRatio = { "Pizza": 7.0, "Slad": 5.0, "H": 5, "G": 5, "F": 5, "E": 5, "D": 45, "C": 25, "B": 15, "A": 10 }
    try:
        doc = table_collection.find_one({'_id': ObjectId(id)}) # Get the game data
        if doc is None:
            return JSONResponse(status_code=404, content={"success": False, "msg": "No data found"})
        if doc["game_status"] == "ended" or doc["winnerAnnounced"] == "yes": # Check the game status
            return JSONResponse(status_code=200, content={
                "success": True,
                "msg": "Winner already declared",
                "winnerSeat": doc["winnedSeat"],
                "data": doc["winnedSeat"],
                "WiningAmount": doc["WiningAmount"],
                "TopUserWinner": doc["TopUserWinner"]
            })
        if doc["game_status"] == "active": # Check the game status
            if len(doc["users"]) == 0: # Here Goes the code When no user found in the game
                luck = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
                winner = random.choice(luck)
                return JSONResponse(status_code=200, content=greedy_game_boat(winner, id))
            else:
                if client.exists("greedyRC"): # Here Goes the code When greedyRC exist in redis
                    winnerUsers = []
                    exist_rc = int(client.get("greedyRC"))
                    counter = int(client.get("greedyCounter"))
                    total_bidding = int(doc['seat']['A_total_amount']) + int(doc['seat']['B_total_amount']) + int(doc['seat']['C_total_amount']) + int(doc['seat']['D_total_amount']) + int(doc['seat']['E_total_amount']) + int(doc['seat']['F_total_amount']) + int(doc['seat']['G_total_amount']) + int(doc['seat']['H_total_amount'])
                    A_winning = total_bidding - int(doc['seat']['A_total_amount']) * winnerRatio["A"]
                    B_winning = total_bidding - int(doc['seat']['B_total_amount']) * winnerRatio["B"]
                    C_winning = total_bidding - int(doc['seat']['C_total_amount']) * winnerRatio["C"]
                    D_winning = total_bidding - int(doc['seat']['D_total_amount']) * winnerRatio["D"]
                    E_winning = total_bidding - int(doc['seat']['E_total_amount']) * winnerRatio["E"]
                    F_winning = total_bidding - int(doc['seat']['F_total_amount']) * winnerRatio["F"]
                    G_winning = total_bidding - int(doc['seat']['G_total_amount']) * winnerRatio["G"]
                    H_winning = total_bidding - int(doc['seat']['H_total_amount']) * winnerRatio["H"]
                    rc_on_port_a = int(A_winning) + int(exist_rc)
                    rc_on_port_b = int(B_winning) + int(exist_rc)
                    rc_on_port_c = int(C_winning) + int(exist_rc)
                    rc_on_port_d = int(D_winning) + int(exist_rc)
                    rc_on_port_e = int(E_winning) + int(exist_rc)
                    rc_on_port_f = int(F_winning) + int(exist_rc)
                    rc_on_port_g = int(G_winning) + int(exist_rc)
                    rc_on_port_h = int(H_winning) + int(exist_rc)
                    candidate_winner_port = {"A": rc_on_port_a, "B": rc_on_port_b, "C": rc_on_port_c, "D": rc_on_port_d, "E": rc_on_port_e, "F": rc_on_port_f, "G": rc_on_port_g, "H": rc_on_port_h}
                    #DONE: First check the counter value is greater than defined value e.g like 5 or 500
                    if counter >= 500: # Here Goes the code When counter greater than 5 or exceed the defined value
                        if exist_rc >= 0: # Here Goes the code When rc greater than 0
                            #DONE: When counter exceed and rc greater than 0 then declare the winner to minium rc_port and update the rc and counter to 0
                            #TODO: Here Check checkPizzaSladWin() function
                            
                            # isDone = checkPizzaSladWin(total_bidding,doc,exist_rc,id)
                            # # print("This is done",isDone)
                            # if isDone:
                            #     # print("👻👻👻👻👻👻👻",isDone)
                            #     client.set("greedyRC", 0)
                            #     client.set("greedyCounter", 0)
                            #     return isDone
                            
                            winner = helptofindwinner(candidate_winner_port,True) 
                            newRC = candidate_winner_port[winner]
                            if newRC >= 0: #DONE: When newRC greater than 0
                                client.incrby("greedyGameRev", int(newRC))
                                client.set("greedyRC", 0)
                                client.set("greedyCounter", 0)
                                return helptosendresponse(doc,winner,id,winnerUsers)
                            else: #DONE: When newRC less than 0
                                client.set("greedyRC", int(newRC))
                                client.incrby("greedyCounter", 1)
                                return helptosendresponse(doc,winner,id,winnerUsers)
                        else: # Here Goes the code When rc less than 0
                            #DONE: When counter exceed and rc less than 0 then declare the winner to maximum rc_port
                            winner = helptofindwinner(candidate_winner_port,True) 
                            newRC = candidate_winner_port[winner]
                            client.set("greedyRC", int(newRC))
                            client.incrby("greedyCounter", 1)
                            return helptosendresponse(doc,winner,id,winnerUsers)
                    else: # DONE: Here Goes the code When counter less than 5 or less than the defined value
                        winner = helptofindwinner(candidate_winner_port)
                        newRC = candidate_winner_port[winner]
                        client.set("greedyRC", int(newRC))
                        client.incrby("greedyCounter", 1)
                        return helptosendresponse(doc,winner,id,winnerUsers)
                else: #DONE: Here Goes the code When greedyRC not exist in redis
                    luck = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
                    winner = random.choice(luck)
                    total_winning = 0
                    total_bidding = int(doc['seat']['A_total_amount'] ) + int( doc['seat']['B_total_amount']) + int(doc['seat']['C_total_amount']) + int(doc['seat']['D_total_amount']) + int(doc['seat']['E_total_amount']) + int(doc['seat']['F_total_amount']) + int(doc['seat']['G_total_amount']) + int(doc['seat']['H_total_amount'])
                    if winner == 'A':
                        total_winning = int(doc['seat']['A_total_amount']) * winnerRatio["A"]
                    elif winner == 'B':
                        total_winning = int(doc['seat']['B_total_amount']) * winnerRatio["B"]
                    elif winner == 'C':
                        total_winning = int(doc['seat']['C_total_amount'] ) * winnerRatio["C"]
                    elif winner == 'D':
                        total_winning = int(doc['seat']['D_total_amount'] ) * winnerRatio["D"]
                    elif winner == 'E':
                        total_winning = int(doc['seat']['E_total_amount'] ) * winnerRatio["E"]
                    elif winner == 'F':
                        total_winning = int(doc['seat']['F_total_amount'] ) * winnerRatio["F"]
                    elif winner == 'G':
                        total_winning = int(doc['seat']['G_total_amount'] ) * winnerRatio["G"]
                    else:
                        total_winning = int(doc['seat']['H_total_amount'] ) * winnerRatio["H"]
                    newRC=total_bidding - total_winning
                    client.set("greedyRC",int(newRC))
                    client.set("greedyCounter", 1)
                    return helptosendresponse(doc,winner,id)
        else:
            return JSONResponse(status_code=404, content={"success": False, "msg": "Something went wrong"})
    except Exception as err:
        import traceback # NOTE: Not for production
        tb_str = ''.join(traceback.format_exception(etype=type(err), value=err, tb=err.__traceback__)) # NOTE: Not for production
        
        # Send the JSONResponse with detailed traceback
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "msg": str(err),
                "traceback": tb_str # NOTE: Not for production
            }
        )






# @router.get("/winner-announcement/{id}")
# async def winner_announced(id: str):
#     try:
#         global greedy_game_ratio
#         doc=table_collection.find_one({'_id': ObjectId(id)})
#         if doc is None:
#             raise HTTPException(status_code=404, detail="No data found")
#         if doc["game_status"] == "ended" or doc["winnerAnnounced"] == "yes":
#             return {
#                 "success": True,
#                 "msg": "Winner already declared",
#                 "winnerSeat":doc["winnedSeat"],
#                 "data":doc["winnedSeat"],
#                 "WiningAmount":doc["WiningAmount"],
#                 "TopUserWinner":doc["TopUserWinner"]
#             }
#         if doc["game_status"] == "active":
#             if len(doc["users"]) == 0:
#                 luck = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H','I','J']
#                 winner = random.choice(luck)
#                 return greedy_game_boat(winner,id)
#             else:
#                 if client.exists("greedyRC"):
#                     winnerUsers=[]
#                     exist_rc= client.get("greedyRC")
#                     counter=client.get("greedyCounter")
#                     total_bidding = int(doc['seat']['A_total_amount'] ) 
#                     + int(doc['seat']['B_total_amount']) 
#                     + int(doc['seat']['C_total_amount'])
#                     + int(doc['seat']['D_total_amount'])
#                     + int(doc['seat']['E_total_amount'])
#                     + int(doc['seat']['F_total_amount'])
#                     + int(doc['seat']['G_total_amount'])
#                     + int(doc['seat']['H_total_amount'])
#                     + int(doc['seat']['I_total_amount'])
#                     + int(doc['seat']['J_total_amount'])
#                     A_winning = total_bidding - int(doc['seat']['A_total_amount']) * 15
#                     B_winning = total_bidding - int(doc['seat']['B_total_amount']) * 5
#                     C_winning = total_bidding - int(doc['seat']['C_total_amount']) * 25
#                     D_winning = total_bidding - int(doc['seat']['D_total_amount']) * 45
#                     E_winning = total_bidding - int(doc['seat']['E_total_amount']) * 5
#                     F_winning = total_bidding - int(doc['seat']['F_total_amount']) * 5
#                     G_winning = total_bidding - int(doc['seat']['G_total_amount']) * 15
#                     H_winning = total_bidding - int(doc['seat']['H_total_amount']) * 5
#                     I_winning = total_bidding - int(doc['seat']['I_total_amount']) * 1.25
#                     J_winning = total_bidding - int(doc['seat']['J_total_amount']) * 4.37
#                     rc_on_port_a = int(A_winning) + int(exist_rc)
#                     rc_on_port_b = int(B_winning) + int(exist_rc)
#                     rc_on_port_c = int(C_winning) + int(exist_rc)
#                     rc_on_port_d = int(D_winning) + int(exist_rc)
#                     rc_on_port_e = int(E_winning) + int(exist_rc)
#                     rc_on_port_f = int(F_winning) + int(exist_rc)
#                     rc_on_port_g = int(G_winning) + int(exist_rc)
#                     rc_on_port_h = int(H_winning) + int(exist_rc)
#                     rc_on_port_i = int(I_winning) + int(exist_rc)
#                     rc_on_port_j = int(J_winning) + int(exist_rc)
#                     newRC=0
#                     counter=int(counter)
#                     exist_rc=int(exist_rc)
#                     winner=""
#                     if counter>=greedy_game_ratio:
#                         # when counter greater than 5
#                         if exist_rc>0:

#                             # when rc greater than 0
#                             # Assuming rc_on_port_a through rc_on_port_h exist
#                             # Assuming you have rc_on_port values for ports A to J in a list or dictionary
#                             rc_on_ports = {
#                                 'A': rc_on_port_a,
#                                 'B': rc_on_port_b,
#                                 'C': rc_on_port_c,
#                                 'D': rc_on_port_d,
#                                 'E': rc_on_port_e,
#                                 'F': rc_on_port_f,
#                                 'G': rc_on_port_g,
#                                 'H': rc_on_port_h,
#                                 'I': rc_on_port_i,
#                                 'J': rc_on_port_j,
#                             }
#                             # Initialize variables
#                             min_rc = None  # Initialize to None
#                             winner = None

#                             # Iterate over ports and find the minimum rc value
#                             for port, rc_value in rc_on_ports.items():
#                                 if min_rc is None or (rc_value >= 0 and rc_value < min_rc):
#                                     min_rc = rc_value
#                                     winner = port
#                             # print(f"The winner is: {winner} with rc_on_port value: {newRC}")

#                             if winner =="" or winner is None:
#                                 winner = "A"
#                                 newRC = rc_on_port_a
#                             client.incrby("greedyGameRev", int(newRC))
#                             client.set("greedyRC", 0)
#                             client.set("greedyCounter", 0)
#                             for ele in doc["users"]:
#                                 if ele["seat"]==winner:
#                                     winnerUsers.append(ele)
#                             if len(winnerUsers)==0:
#                                 return greedy_game_boat(winner,id)
#                             else:
#                                 return credit_greedy_diamonds(winner,winnerUsers,id)
#                         else:
#                             # when rc less than 0
#                             # Assuming A_winning, B_winning, C_winning, rc_on_port_a through rc_on_port_h exist
#                             print("counter greater than 5 and rc less than 0")
#                             # Assuming you have A_winning, B_winning, etc. defined as variables
#                             winning_variables = {
#                                 'A': A_winning,
#                                 'B': B_winning,
#                                 'C': C_winning,
#                                 'D': D_winning,
#                                 'E': E_winning,
#                                 'F': F_winning,
#                                 'G': G_winning,
#                                 'H': H_winning,
#                             }
#                             # Initialize variables
#                             max_winning = float('-inf')  # Initialize to negative infinity
#                             winner = None
#                             # Iterate over winning variables and find the maximum value
#                             for port, winning_value in winning_variables.items():
#                                 if winning_value >= max_winning:
#                                     max_winning = winning_value
#                                     winner = port

#                             # 'winner' will now contain the port letter with the maximum winning value
#                             newRC = max_winning
#                             # print(f"The winner is: {winner} with winning value: {newRC}")
#                             if winner =="":
#                                 winner = "A"
#                                 newRC = rc_on_port_a
#                             # print("winner",winner,"newRC",newRC)
#                             client.set("greedyRC", int(newRC))
#                             client.incrby("greedyCounter", 1)
#                             for ele in doc["users"]:
#                                 if ele["seat"]==winner:
#                                     winnerUsers.append(ele)
#                             if len(winnerUsers)==0:
#                                 return greedy_game_boat(winner,id)
#                             else:
#                                 return credit_greedy_diamonds(winner,winnerUsers,id)
#                     else:
#                         # when counter less than 5
#                         if exist_rc==0:
#                             #when rc equal to 0
#                             luck = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H','I','J']
#                             winner = random.choice(luck)
#                             total_winning = 0
#                             total_bidding = int(doc['seat']['A_total_amount'] ) 
#                             + int(doc['seat']['B_total_amount']) 
#                             + int(doc['seat']['C_total_amount'])
#                             + int(doc['seat']['D_total_amount'])
#                             + int(doc['seat']['E_total_amount'])
#                             + int(doc['seat']['F_total_amount'])
#                             + int(doc['seat']['G_total_amount'])
#                             + int(doc['seat']['H_total_amount'])
#                             + int(doc['seat']['I_total_amount'])
#                             + int(doc['seat']['J_total_amount'])
#                             if winner == 'A':
#                                 total_winning = int(doc['seat']['A_total_amount']) * 15
#                             elif winner == 'B':
#                                 total_winning = int(doc['seat']['B_total_amount']) * 5
#                             elif winner == 'C':
#                                 total_winning = int(doc['seat']['C_total_amount']) * 25
#                             elif winner == 'D':
#                                 total_winning = int(doc['seat']['D_total_amount']) * 45
#                             elif winner == 'E':
#                                 total_winning = int(doc['seat']['E_total_amount']) * 5
#                             elif winner == 'F':
#                                 total_winning = int(doc['seat']['F_total_amount']) * 5
#                             elif winner == 'G':
#                                 total_winning = int(doc['seat']['G_total_amount']) * 10
#                             elif winner == 'H':
#                                 total_winning = int(doc['seat']['H_total_amount']) * 5
#                             elif winner == 'I':
#                                 total_winning = int(doc['seat']['I_total_amount']) * 1.25
#                             else:
#                                 total_winning = int(doc['seat']['J_total_amount']) * 4.37
#                             rc=total_bidding-total_winning
#                             client.set("greedyRC",int(rc))
#                             client.incrby("greedyCounter", 1)
#                             winnerUsers=[]
#                             for ele in doc["users"]:
#                                 if ele["seat"]==winner:
#                                     winnerUsers.append(ele)
#                             if len(winnerUsers)==0:
#                                 return greedy_game_boat(winner,id)
#                             else:
#                                 return credit_greedy_diamonds(winner,winnerUsers,id)
#                         elif exist_rc>0:
#                             #when rc greater than 0
#                             # Assuming rc_on_port_a through rc_on_port_h exist
                            
#                             if counter//2<=greedy_game_ratio:
#                                 luck = ['slad','pizza']
#                                 total_bidding_on_slad = int(doc['seat']['B_total_amount'])
#                                 + int(doc['seat']['E_total_amount'])
#                                 + int(doc['seat']['F_total_amount'])
#                                 + int(doc['seat']['H_total_amount'])
#                                 + int(doc['seat']['I_total_amount'])
#                                 total_bidding_on_pizza = int(doc['seat']['A_total_amount'])
#                                 + int(doc['seat']['C_total_amount'])
#                                 + int(doc['seat']['D_total_amount'])
#                                 + int(doc['seat']['G_total_amount'])
#                                 + int(doc['seat']['J_total_amount'])
#                                 winner = random.choice(luck)
#                                 if winner == "slad":
#                                     # slad winn ['B','E','F','H'] these seat win

#                                     client.set("greedyRC", int(newRC+total_bidding_on_slad-total_bidding_on_pizza))
#                                     client.incrby("greedyCounter", 1)
#                                     for ele in doc["users"]:
#                                         if ele["seat"] in ['B','E','F','H']:
#                                             winnerUsers.append(ele)
#                                     if len(winnerUsers)==0:
#                                         return greedy_game_boat("A",id)
#                                     else:
#                                         return credit_greedy_diamonds("S",winnerUsers,id)
#                                 else:
#                                     # slad winn ['A','C','D','G'] these seat win
#                                     client.set("greedyRC", int(newRC+total_bidding_on_pizza-total_bidding_on_slad))
#                                     client.incrby("greedyCounter", 1)
#                                     for ele in doc["users"]:
#                                         if ele["seat"] in ['A','C','D','G']:
#                                             winnerUsers.append(ele)
#                                     if len(winnerUsers)==0:
#                                         return greedy_game_boat("E",id)
#                                     else:
#                                         return credit_greedy_diamonds("P",winnerUsers,id)

#                             # Assume rc_on_ports is a list containing the values for A to J ports
#                             rc_on_ports = [rc_on_port_a, rc_on_port_b, rc_on_port_c, rc_on_port_d, rc_on_port_e, rc_on_port_f, rc_on_port_g, rc_on_port_h, rc_on_port_i, rc_on_port_j]

#                             # Check if all values are greater than or equal to 0
#                             if all(rc >= 0 for rc in rc_on_ports):
#                                 min_rc, winner = min((rc, port) for port, rc in zip("ABCDEFGHIJ", rc_on_ports))
#                             else:
#                                 # Check if all values are less than or equal to 0
#                                 if all(rc <= 0 for rc in rc_on_ports):
#                                     max_rc, winner = max((rc, port) for port, rc in zip("ABCDEFGHIJ", rc_on_ports))
#                                 else:
#                                     # Check values for A to H when they are greater than or equal to 0
#                                     if all(rc >= 0 for rc in rc_on_ports[:8]):
#                                         min_rc, winner = min((rc, port) for port, rc in zip("ABCDEFGH", rc_on_ports[:8]))
#                                     else:
#                                         # Check values for A to H when they are less than or equal to 0
#                                         if all(rc <= 0 for rc in rc_on_ports[:8]):
#                                             max_rc, winner = max((rc, port) for port, rc in zip("ABCDEFGH", rc_on_ports[:8]))
#                                         else:
#                                             # Check values for A and B when they are greater than or equal to 0
#                                             if rc_on_port_a >= 0 and rc_on_port_b >= 0:
#                                                 min_rc, winner = min((rc, port) for port, rc in zip("AB", rc_on_ports[:2]))
#                                             else:
#                                                 # Check values for A and B when they are less than or equal to 0
#                                                 if rc_on_port_a <= 0 and rc_on_port_b <= 0:
#                                                     max_rc, winner = max((rc, port) for port, rc in zip("AB", rc_on_ports[:2]))
#                                                 else:
#                                                     # Check values for A and C when they are greater than or equal to 0
#                                                     if rc_on_port_a >= 0 and rc_on_port_c >= 0:
#                                                         min_rc, winner = min((rc, port) for port, rc in zip("AC", rc_on_ports[:3]))
#                                                     else:
#                                                         # Check values for A and C when they are less than or equal to 0
#                                                         if rc_on_port_a <= 0 and rc_on_port_c <= 0:
#                                                             max_rc, winner = max((rc, port) for port, rc in zip("AC", rc_on_ports[:3]))

#                             # Print the result
#                             # print(f"The winner is: {winner} with rc_on_port value: {min_rc}")
#                             newRC = min_rc or max_rc

#                             if winner=="":
#                                 newRC = rc_on_port_a
#                                 winner = "A"
#                             client.set("greedyRC", int(newRC))
#                             client.incrby("greedyCounter", 1)
#                             for ele in doc["users"]:
#                                 if ele["seat"]==winner:
#                                     winnerUsers.append(ele)
#                             if len(winnerUsers)==0:
#                                 return greedy_game_boat(winner,id)
#                             else:
#                                 return credit_greedy_diamonds(winner,winnerUsers,id)
#                         elif exist_rc<0:
#                             #when rc less than 0
#                             # Assuming rc_on_port_a through rc_on_port_h exist

#                             # Assume rc_on_ports is a list containing the values for A to J ports
#                             rc_on_ports = [rc_on_port_a, rc_on_port_b, rc_on_port_c, rc_on_port_d, rc_on_port_e, rc_on_port_f, rc_on_port_g, rc_on_port_h, rc_on_port_i, rc_on_port_j]

#                             # Check if all values are less than or equal to 0
#                             if all(rc <= 0 for rc in rc_on_ports):
#                                 max_rc, winner = max((rc, port) for port, rc in zip("ABCDEFGHIJ", rc_on_ports))
#                             elif all(rc >= 0 for rc in rc_on_ports):
#                                 min_rc, winner = min((rc, port) for port, rc in zip("ABCDEFGHIJ", rc_on_ports))
#                             else:
#                                 positive_ports = [port for port, rc in zip("ABCDEFGHIJ", rc_on_ports) if rc >= 0]
#                                 negative_ports = [port for port, rc in zip("ABCDEFGHIJ", rc_on_ports) if rc <= 0]

#                                 if not positive_ports:
#                                     min_rc, winner = max((rc, port) for port, rc in zip(negative_ports, rc_on_ports))
#                                 elif not negative_ports:
#                                     min_rc, winner = min((rc, port) for port, rc in zip(positive_ports, rc_on_ports))
#                                 else:
#                                     newRC, winner = min((rc, port) for port, rc in zip(positive_ports, rc_on_ports))

#                             # Print the result
#                             # print(f"The winner is: {winner} with rc_on_port value: {min_rc if 'min_rc' in locals() else max_rc}")


#                             if winner == "":
#                                 newRC = rc_on_port_a
#                                 winner = "A"
#                             client.set("greedyRC", int(newRC))
#                             client.incrby("greedyCounter", 1)
#                             for ele in doc["users"]:
#                                 if ele["seat"]==winner:
#                                     winnerUsers.append(ele)
#                             if len(winnerUsers)==0:
#                                 return greedy_game_boat(winner,id)
#                             else:
#                                 return credit_greedy_diamonds(winner,winnerUsers,id)
#                 else:
#                     luck = ['A', 'B', 'C']
#                     winner = random.choice(luck)
#                     total_winning = 0
#                     total_bidding = int(doc['seat']['A_total_amount'] ) 
#                     + int(doc['seat']['B_total_amount']) 
#                     + int(doc['seat']['C_total_amount'])
#                     + int(doc['seat']['D_total_amount'])
#                     + int(doc['seat']['E_total_amount'])
#                     + int(doc['seat']['F_total_amount'])
#                     + int(doc['seat']['G_total_amount'])
#                     + int(doc['seat']['H_total_amount'])
#                     + int(doc['seat']['I_total_amount'])
#                     if winner == 'A':
#                         total_winning = int(doc['seat']['A_total_amount']) * 15
#                     elif winner == 'B':
#                         total_winning = int(doc['seat']['B_total_amount']) * 5
#                     elif winner == 'C':
#                         total_winning = int(doc['seat']['C_total_amount']) * 25
#                     elif winner == 'D':
#                         total_winning = int(doc['seat']['D_total_amount']) * 45
#                     elif winner == 'E':
#                         total_winning = int(doc['seat']['E_total_amount']) * 5
#                     elif winner == 'F':
#                         total_winning = int(doc['seat']['F_total_amount']) * 5
#                     elif winner == 'G':
#                         total_winning = int(doc['seat']['G_total_amount']) * 10
#                     elif winner == 'H':
#                         total_winning = int(doc['seat']['H_total_amount'] ) * 5
#                     elif winner == 'I':
#                         total_winning = int(doc['seat']['I_total_amount'] ) * 1.25
#                     else:
#                         total_winning = int(doc['seat']['J_total_amount'] ) * 4.37
#                     rc=total_bidding-total_winning
#                     client.set("greedyRC",int(rc))
#                     client.set("greedyCounter", 1)
#                     winnerUsers=[]
#                     for ele in doc["users"]:
#                         if ele["seat"] == winner:
#                             winnerUsers.append(ele)
#                     if len(winnerUsers)==0:
#                         return greedy_game_boat(winner,id)
#                     else:
#                         return credit_greedy_diamonds(winner, winnerUsers, id)
#     except Exception as err:
#         raise HTTPException(status_code=500, detail=str(err))


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