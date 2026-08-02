import psycopg as sql
from enum import Enum
import secrets,string,uuid,os,pickle,numpy as np,pandas as pd,warnings
from argon2 import PasswordHasher
from cryptography.fernet import Fernet
from datetime import datetime
from dotenv import load_dotenv
warnings.filterwarnings("ignore", message="X does not have valid feature names")
load_dotenv()
encrypt=Fernet(os.getenv("encrypt_key"))

try:
    with open('loan_model.pkl', 'rb') as f:#loading the model 
        model = pickle.load(f) 
except FileNotFoundError:
    raise FileNotFoundError("The loan_model.pkl file was not found. Please run the training script ai for loan.py.")

class TransactionMethod(str, Enum):
    internal_transfer = 'internal_transfer'
    upi = "upi"
    neft = "neft"
    rtgs = "rtgs"
    debit_card="debit_card"
    credit_card="credit_card"
    branch_cash="branch_cash"

class Bank:
    def __init__(self, userid:str):
        self.userid = userid

    @staticmethod
    def transactionid() ->str: #this function is for transactionid generation
        return str(uuid.uuid4())
    @staticmethod
    def encrypt_str(note:str) ->str:
        if note is None:
            raise TypeError(" the note should not be NoneType")
        return encrypt.encrypt(note.encode()).decode()
    @staticmethod
    def decrypt_str(byte:str) ->str:
        if byte is None:
            raise TypeError(" the note should not be NoneType")
        return encrypt.decrypt(byte.encode()).decode()


    @staticmethod
    def transaction_history(account_number,date=None,amount=None,transaction_type=None,status=None):
        with sql.connect(dbname=os.getenv("db_name"),user=os.getenv("db_user"),host=os.getenv("db_host"),port=os.getenv("db_port")) as con:
            with con.cursor() as cursor:
                cursor.execute("select * from transactions WHERE sender_acc= %s OR receiver_acc= %s order by date desc limit 100",(account_number,account_number))
                transactions=cursor.fetchall()
                
                formatted_transactions = []
                for row in transactions:
                    if row[3] == account_number:
                        tx_type = "Sent" 
                        counterparty = f"To: {row[5]}"
                        sign = "-"
                    else:
                        tx_type = "Received"
                        counterparty = f"From: {row[2]}"
                        sign = "+"
                    formatted_transactions.append({
                        "transactionid": row[1],
                        "type": tx_type,
                        "counterparty": counterparty,
                        "amount": f"{sign}₹{row[6]}",
                        "note": Bank.decrypt_str(row[9]) if row[9] else "No note",
                        "status": row[7],
                        "date": str(row[8])[:16],
                        "method": row[10]
                    })
                return formatted_transactions
        
        

    def edit_profile(self):
        try:
            with sql.connect(dbname=os.getenv("db_name"),user=os.getenv("db_user"),host=os.getenv("db_host"),port=os.getenv("db_port")) as con:
                with con.cursor() as cursor:
                    cursor.execute("SELECT * FROM users")
                    d=cursor.fetchall()
                    return d
        except:
            return "An internal system error occured while editing the profile"

    def deposit_amount(self, amount:int) ->tuple[bool,str]:
            if amount < 1:
                return False, "Minimum deposit is ₹1."
            try:
                #databse connection
                with sql.connect(dbname=os.getenv("db_name"),user=os.getenv("db_user"),host=os.getenv("db_host"),port=os.getenv("db_port")) as con:
                    with con.cursor() as cursor:

                        #updating the balance
                        cursor.execute("UPDATE users SET balance = balance + %s WHERE userid = %s", (amount, self.userid))

                        # Log this as a transaction in the database so it shows on the dashboard
                        cursor.execute("SELECT username,account_number,balance FROM users WHERE userid = %s", (self.userid,))
                        user_data = cursor.fetchone()
                        user_name=user_data[0]
                        sender_acc=user_data[1]
                        balance=user_data[2]
        
                        cursor.execute('''
                            INSERT INTO transactions 
                            (transactionid, sender_username, sender_acc, receiver_acc, receiver_username, amount, method, note, status) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ''', (Bank.transactionid(),"Cash Deposite","0",sender_acc,user_name, amount, "internal_transfer", Bank.encrypt_str("Self Deposit"), "completed"))
                        # here the zero refferes to NULL value 
                        return True, f"Deposited ₹{amount:.2f} successfully!. New balance: ₹{balance}"
        
            except :
                return False, f"An internal system error occured. No money was deposited."
 
    def withdraw_amount(self, amount:int) ->tuple[bool,str]:
            if amount < 1:
                return False, "Minimum withdrawal is ₹1."
            try:
                # Execute the withdrawal
                with sql.connect(dbname=os.getenv("db_name"),user=os.getenv("db_user"),host=os.getenv("db_host"),port=os.getenv("db_port")) as con:
                    with con.cursor() as cursor:

                         #updating the balance
                        cursor.execute("UPDATE users SET balance = balance - %s WHERE userid = %s AND balance >= %s",(amount,self.userid,amount))

                        #if balance did not update return false
                        if cursor.rowcount==0:
                            return False, "Insufficient funds. Please check your balance."

                        # Log this as a transaction in the database so it shows on the dashboard
                        cursor.execute("SELECT username,account_number,balance FROM users WHERE userid = %s", (self.userid,))
                        user_data = cursor.fetchone()
                        user_name=user_data[0]
                        sender_acc=user_data[1]
                        balance=user_data[2]
        
                        cursor.execute('''
                            INSERT INTO transactions 
                            (transactionid, sender_username, sender_acc, receiver_acc, receiver_username, amount, method, note, status) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ''', (Bank.transactionid(), user_name, sender_acc,"0","ATM Withdrawal",amount,"atm",Bank.encrypt_str("ATM Withdrawal"), "completed"))
                        # here the zero refferes to NULL valuse 
                        return True, f"Successfully withdrew ₹{amount:.2f}. New balance: ₹{balance}"
        
            except:
                return False, "An internal system error occured. No money was withdrawed."
            
        
    def transfer(self,receiver_acc,amount,note,method) -> tuple[bool,str]:
            if amount <= 0:
                return False, "Transfer amount must be greater than zero."
            try:
                with sql.connect(dbname=os.getenv("db_name"),user=os.getenv("db_user"),host=os.getenv("db_host"),port=os.getenv("db_port")) as con:
                    with con.cursor() as cursor:
                        cursor.execute("SELECT account_number, balance, username FROM users WHERE userid = %s", (self.userid,))
                        sender_data = cursor.fetchone()
                        sender_acc = sender_data[0]
                        sender_balance = sender_data[1]
                        sender_name = sender_data[2]

                        if sender_acc == receiver_acc:
                            return False, "You cannot transfer money to your own account."
                        
                        cursor.execute("select username from users where account_number  = %s",(receiver_acc,))
                        receiver_name = cursor.fetchone()
                        if not receiver_name:
                            return False,"Receiver account not found. Please verify the account number."
                        
                        receiver_name=receiver_name[0]

                        if amount >sender_balance:
                            cursor.execute('''
                            INSERT INTO transactions 
                            (transactionid, sender_username, sender_acc, receiver_acc, receiver_username, amount, method, note, status) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ''', (Bank.transactionid(), sender_name, sender_acc, receiver_acc, receiver_name, amount, method, Bank.encrypt_str(note), "failed"))
                            return False, "Insufficient funds. Please check your balance."

                        #EXECUTE THE TRANSFER SAFELY
                        # 1. Deduct from SENDER
                        cursor.execute("UPDATE users SET balance = balance - %s WHERE userid = %s", (amount, self.userid))
            
                        # 2. Add to RECEIVER
                        cursor.execute("UPDATE users SET balance = balance + %s WHERE account_number = %s", (amount, receiver_acc))
            
                        # 3. Create Receipt for transaction
                        cursor.execute('''INSERT INTO transactions 
                           (transactionid,sender_username, sender_acc, receiver_acc, receiver_username, amount,method,note ,status) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)''', 
                            (Bank.transactionid(),sender_name, sender_acc, receiver_acc, receiver_name, amount,method,Bank.encrypt_str(note),"completed"))
                        return True, f"Successfully transferred ₹{amount} to {receiver_name}."
            except:
                return False, "An internal system error occured. No money was transferred."

    def apply_for_loan(self) ->tuple[bool,str]:
        try:
            with sql.connect(dbname=os.getenv("db_name"),user=os.getenv("db_user"),host=os.getenv("db_host"),port=os.getenv("db_port")) as con:
                with con.cursor() as cursor:
                    cursor.execute("SELECT balance, account_number FROM users WHERE userid = %s",(self.userid,))
                    user_data=cursor.fetchone()
                    # 1. GATHER DATA
                    balance =user_data[0]
                    acc_num=user_data[1]
        
                    # Count user's transactions from DB
                    cursor.execute("SELECT COUNT(*) FROM transactions WHERE sender_acc = %s OR receiver_acc = %s " , (acc_num,acc_num))
                    txn_count = cursor.fetchone()[0]

                    #prediction
                    features = np.array([[balance, txn_count]])
                    prediction = model.predict(features)
                    if prediction[0] == 1:
                        return True,"success, ✅ CONGRATULATIONS! Loan Approved by AI.", {"balance":balance,"txn_count":txn_count}
                    else:
                        return False, "failed you can't get loan",None
        except:
            return False,"An internal system error occured when approving loan"

    def download_statement(self):
        try:
            with sql.connect(dbname=os.getenv("db_name"),user=os.getenv("db_user"),host=os.getenv("db_host"),port=os.getenv("db_port")) as con:
                with con.cursor() as cursor:
                    cursor.execute("SELECT account_number FROM users WHERE userid = %s",(self.userid,))
                    test_acc=cursor.fetchone()
                    query=f'''SELECT * FROM transactions WHERE sender_acc= %s OR  receiver_acc= %s'''
                    df = pd.read_sql_query(query, con,params=(test_acc[0],test_acc[0]))
                    return "Statement ✅ succsessfully downloaded"
        except:
            return "An internal system error occured while downloading the statement"
        
    
class Loans(Bank):
    def __init__(self, userid:str, balance1:int):
        self.userid = userid
        self.balance1 = balance1
        self.interest_rate = 0.05

    def balance(self):
        try:
            interest1 = self.interest_rate * self.balance1
            total = interest1 + self.balance1
            return total
        except:
            return "An internal system error occured"

class Openaccount(Bank):
    def __init__(self, Username:str, Userid:str, Password:str,Balance1:int=0):
        self.Username = Username
        self.Userid=Userid
        self.Password = Password
        self.Balance1=Balance1

    @staticmethod
    def accountnum()->str: #this function is for account number generation
        return "".join(secrets.SystemRandom().choices(string.digits,k=10))
    
    def password_hash(self) ->str:
        return PasswordHasher().hash(self.Password)
       
    def open_account(self):
        acc_num = Openaccount.accountnum()
        try:
            with sql.connect(dbname=os.getenv("db_name"),user=os.getenv("db_user"),host=os.getenv("db_host"),port=os.getenv("db_port")) as con:
                with con.cursor() as cursor:
                    cursor.execute("INSERT INTO users (username, userid, password, account_number,balance) VALUES ( %s, %s, %s, %s, %s)", 
                       (self.Username,self.Userid, self.password_hash(), acc_num,self.Balance1))
                    today_date = datetime.now().strftime("%B %d, %Y")
                    return acc_num, today_date
        except sql.IntegrityError:
            return sql.IntegrityError()
        except:
            return "An internal system error occured while creating account"