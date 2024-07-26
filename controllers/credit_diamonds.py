#PRODUCTION
from config.db import db
import datetime
import secrets
from bson import ObjectId
from pymongo import ReturnDocument
table_collection = db['fruits']
table_balance_collection = db["user_wallet_balances"]
transaction_collection = db["transactions"]
table_collection_teen_patti = db['teen_pattis']
table_collection_greedy_game = db['greedies']
user_login_table = db["user_logins"]
# from config.firebase_firestore import firestore_db
from google.cloud.firestore_v1.base_query import FieldFilter
from firebase_admin import firestore

greedy_wining_ratio = 3.0

def credit_greedy_diamonds(winner:str,winnerUsers:list,game_id:str,winnerRatio:dict = {"A": 10, "B": 15, "C": 25, "D": 45, "E": 5, "F": 5, "G": 5, "H": 5}):
    WinningAmount = {}
    for ele in winnerUsers:
      UID = str(ele['UID'])
      amount = float(ele['amount'])
      if UID in WinningAmount:
         WinningAmount[UID]['BetAmount'] += amount
         WinningAmount[UID]['WinAmount'] += amount * winnerRatio[winner]
      else:
          WinningAmount[UID] = {
            'BetAmount': amount,
            'WinAmount': amount * winnerRatio[winner]
          }
      user=user_login_table.find_one_and_update(
         {"UID":ele['UID']},
         {'$inc':{"Udiamonds":ele["amount"] * winnerRatio[winner]}},
          return_document=ReturnDocument.AFTER
         )
      if user:
         transaction_id = secrets.token_hex(8)
         transaction_data = {
            "transaction_id": transaction_id,
            "transaction_type": "credited",
            "transaction_amount": ele["amount"] * winnerRatio[winner],
            "transaction_status": "success",
            "transaction_date": datetime.datetime.now(),
            "sender_type": "user",
            "receiver_type": "game",
            "sender_UID": ele["UID"],
            "before_tran_balance": user["Udiamonds"] - ele["amount"] * winnerRatio[winner],
            "after_tran_balance": user["Udiamonds"],
            "receiver_UID": game_id,
            "user_wallet_type_from": "diamonds",
            "user_wallet_type_to": "diamonds",
            "entity_type": {
                "type": "game",
                "game_id": game_id,
                "game_name": "greedy"
            }
          }
         transaction_collection.insert_one(transaction_data)
      else:
          transaction_id = secrets.token_hex(8)
          transaction_data = {
            "transaction_id": transaction_id,
            "transaction_type": "credited",
            "transaction_amount": ele["amount"] * winnerRatio[winner],
            "transaction_status": "failed",
            "transaction_date": datetime.datetime.now(),
            "sender_type": "user",
            "receiver_type": "game",
            "sender_UID": ele["UID"],
            "before_tran_balance": user["Udiamonds"] - ele["amount"] * winnerRatio[winner],
            "after_tran_balance": user["Udiamonds"],
            "receiver_UID": game_id,
            "user_wallet_type_from": "diamonds",
            "user_wallet_type_to": "diamonds",
            "entity_type": {
                "type": "game",
                "game_id": game_id,
                "game_name": "greedy"
            }
            }
          transaction_collection.insert_one(transaction_data)
    TopUserWinner = []
    for UID, data in WinningAmount.items():
      temp = {UID: data['WinAmount']}
      TopUserWinner.append(temp)
    TopUserWinner.sort(key=lambda x: list(x.values())[0], reverse=True)
    TopUserWinner = TopUserWinner[:3]
    dataToUpdate={
      "game_status": "ended",
      "winnerAnnounced": "yes",
      "winnedSeat":winner,
      "TopUserWinner": TopUserWinner,
      "WiningAmount": WinningAmount,
    }
    result = table_collection_greedy_game.update_one({'_id': ObjectId(game_id)}, {"$set": dataToUpdate})
    if result.acknowledged:
        TopWinnerUserWithProfilePic = []
        for item in TopUserWinner:
          for UID in item.keys():
            user = user_login_table.find_one({"UID": UID},{"user_profile_pic":1,"user_nick_name":1,"_id":0})
            if user:
              user["UID"] = UID
              user["WinAmount"] = item[UID]
              if not user["user_profile_pic"].startswith("http"):
                user["user_profile_pic"] = "https://apimylive.cynayd.com/api/v2/users/get-profile-pic/"+UID
              TopWinnerUserWithProfilePic.append(user)
        # print("TopWinnerUserWithProfilePic",TopWinnerUserWithProfilePic)
        return {
            "success": True,
            "msg": "Winner declared",
            "winnerSeat":winner,
            "TopUserWinner":TopWinnerUserWithProfilePic,
            "WiningAmount":WinningAmount,
            "data":winner
          }
    else:
      return{
        "success": False,
        "msg": "Something went wrong"
        }


def credit_diamonds(winner:str,winnerUsers:list,game_id:str):
    WinningAmount = {}
    for ele in winnerUsers:
      user_id = str(ele['UID'])
      amount = float(ele['amount'])
      if user_id in WinningAmount:
         WinningAmount[user_id]['BetAmount'] += amount
         WinningAmount[user_id]['WinAmount'] += amount * 3.0
      else:
          WinningAmount[user_id] = {
            'BetAmount': amount,
            'WinAmount': amount * 3.0
          }
      user=user_login_table.find_one_and_update(
         {"UID":ele['UID']},
         {'$inc':{"Udiamonds":ele["amount"]*3.0}},
          return_document=ReturnDocument.AFTER
         )
      if user:
         transaction_id = secrets.token_hex(8)
         transaction_data = {
            "transaction_id": transaction_id,
            "transaction_type": "credited",
            "transaction_amount": ele["amount"]*3.0,
            "transaction_status": "success",
            "transaction_date": datetime.datetime.now(),
            "sender_type": "user",
            "receiver_type": "game",
            "sender_UID": ele["UID"],
            "before_tran_balance": user["Udiamonds"]-ele["amount"]*3.0,
            "after_tran_balance": user["Udiamonds"],
            "receiver_UID": game_id,
            "user_wallet_type_from": "diamonds",
            "user_wallet_type_to": "diamonds",
            "entity_type": {
                "type": "game",
                "game_id": game_id,
                "game_name": "fruit"
            }
          }
         transaction_collection.insert_one(transaction_data)
      else:
           
          transaction_id = secrets.token_hex(8)
          transaction_data = {
            "transaction_id": transaction_id,
            "transaction_type": "credited",
            "transaction_amount": ele["amount"]*3.0,
            "transaction_status": "failed",
            "transaction_date": datetime.datetime.now(),
            "sender_type": "user",
            "receiver_type": "game",
            "sender_UID": ele["UID"],
            "before_tran_balance": user["Udiamonds"] - ele["amount"]*3.0,
            "after_tran_balance": user["Udiamonds"],
            "receiver_UID": game_id,
            "user_wallet_type_from": "diamonds",
            "user_wallet_type_to": "diamonds",
            "entity_type": {
                "type": "game",
                "game_id": game_id,
                "game_name": "fruit"
            }
            }
          transaction_collection.insert_one(transaction_data)
    TopUserWinner = []
    for user_id, data in WinningAmount.items():
      temp = {user_id: data['WinAmount']}
      TopUserWinner.append(temp)
    TopUserWinner.sort(key=lambda x: list(x.values())[0], reverse=True)
    TopUserWinner = TopUserWinner[:3]
    dataToUpdate={
      "game_status": "ended",
      "winnerAnnounced": "yes",
      "winnedSeat":winner,
      "TopUserWinner": TopUserWinner, 
      "WiningAmount": WinningAmount,
      }
    result=table_collection.update_one({'_id': ObjectId(game_id)}, {"$set": dataToUpdate})
    if result.acknowledged:
        return {
            "success": True,
            "msg": "Winner declared",
            "winnerSeat":winner,
            "TopUserWinner":TopUserWinner,
            "WiningAmount":WinningAmount,
            "data":winner
          }
    else:
      return{
        "success": False,
        "msg": "Something went wrong"
        }
    
    
    
    
def credit_diamonds_teen_patti(winner:str,winnerUsers:list,game_id:str):
    WinningAmount = {}
    for ele in winnerUsers:
      user_id = str(ele['UID'])
      amount = float(ele['amount'])
      if user_id in WinningAmount:
         WinningAmount[user_id]['BetAmount'] += amount
         WinningAmount[user_id]['WinAmount'] += amount * 3.0
      else:
          WinningAmount[user_id] = {
            'BetAmount': amount,
            'WinAmount': amount * 3.0
          }
      user=user_login_table.find_one_and_update(
         {"UID":ele['UID']},
         {'$inc':{"Udiamonds":ele["amount"]*3.0}},
          return_document=ReturnDocument.AFTER
         )
      if user:
         transaction_id = secrets.token_hex(8)
         transaction_data = {
            "transaction_id": transaction_id,
            "transaction_type": "credited",
            "transaction_amount": ele["amount"]*3.0,
            "transaction_status": "success",
            "transaction_date": datetime.datetime.now(),
            "sender_type": "user",
            "receiver_type": "game",
            "sender_UID": ele["UID"],
            "before_tran_balance": user["Udiamonds"]-ele["amount"]*3.0,
            "after_tran_balance": user["Udiamonds"],
            "receiver_UID": game_id,
            "user_wallet_type_from": "diamonds",
            "user_wallet_type_to": "diamonds",
            "entity_type": {
                "type": "game",
                "game_id": game_id,
                "game_name": "teen-patti"
            }
          }
         transaction_collection.insert_one(transaction_data)
      else:
           
          transaction_id = secrets.token_hex(8)
          transaction_data = {
            "transaction_id": transaction_id,
            "transaction_type": "credited",
            "transaction_amount": ele["amount"]*3.0,
            "transaction_status": "failed",
            "transaction_date": datetime.datetime.now(),
            "sender_type": "user",
            "receiver_type": "game",
            "sender_UID": ele["UID"],
            "before_tran_balance": user["Udiamonds"] - ele["amount"]*3.0,
            "after_tran_balance": user["Udiamonds"],
            "receiver_UID": game_id,
            "user_wallet_type_from": "diamonds",
            "user_wallet_type_to": "diamonds",
            "entity_type": {
                "type": "game",
                "game_id": game_id,
                "game_name": "teen-patti"
            }
            }
          transaction_collection.insert_one(transaction_data)
    TopUserWinner = []
    for user_id, data in WinningAmount.items():
      temp = {user_id: data['WinAmount']}
      TopUserWinner.append(temp)
    TopUserWinner.sort(key=lambda x: list(x.values())[0], reverse=True)
    TopUserWinner = TopUserWinner[:3]
    dataToUpdate={
      "game_status": "ended",
      "winnerAnnounced": "yes",
      "winnedSeat":winner,
      "TopUserWinner": TopUserWinner, 
      "WiningAmount": WinningAmount,
      }
    result=table_collection_teen_patti.update_one({'_id': ObjectId(game_id)}, {"$set": dataToUpdate})
    if result.acknowledged:
        return {
            "success": True,
            "msg": "Winner declared",
            "winnerSeat":winner,
            "TopUserWinner":TopUserWinner,
            "WiningAmount":WinningAmount,
            "data":winner
          }
    else:
      return{
        "success": False,
        "msg": "Something went wrong"
        }
