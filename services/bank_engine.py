import psycopg as sql
from enum import Enum
import secrets,string,uuid,os,pickle,numpy as np,pandas as pd,warnings
from datetime import datetime
warnings.filterwarnings("ignore", message="X does not have valid feature names")

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
    def transactionid(): #this function is for transactionid generation
        return str(uuid.uuid4())
    
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
                        "note": row[9] if row[9] else "No note",
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
            return "Error occured while editing the profile"

    def deposit_amount(self, amount:int):
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
                            ''', (Bank.transactionid(), "Cash Deposit","0", sender_acc,user_name, amount, "internal_transfer", "Self Deposit", "completed"))
                        # here the zero refferes to NULL value 
                        return True, f"Deposited ₹{amount:.2f} successfully!. New balance: ₹{balance}"
        
            except :
                return False, "System error. No money was deposited."
 
    def withdraw_amount(self, amount:int):
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
                            ''', (Bank.transactionid(), user_name, sender_acc, "0", "ATM Withdrawal", amount, "atm", "Self Withdrawal", "completed"))
                        # here the zero refferes to NULL valuse 
                        return True, f"Successfully withdrew ₹{amount:.2f}. New balance: ₹{balance}"
        
            except:
                return False, "System error. No money was withdrawed."
            
        
    def transfer(self,receiver_acc,amount,note,method):
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
                            ''', (Bank.transactionid(), sender_name, sender_acc, receiver_acc, receiver_name, amount, method, note, "failed"))
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
                            (Bank.transactionid(),sender_name, sender_acc, receiver_acc, receiver_name, amount,method,note,"completed"))
                        return True, f"Successfully transferred ₹{amount} to {receiver_name}."
            except:
                return False, "System error. No money was transferred."

    def apply_for_loan(self):
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
            return False,"System error when approving loan"

    def download_statement(self):
        try:
            with sql.connect(dbname="mybankdb",user="saiganeshsattenapalli",host="localhost",port="5432") as con:
                with con.cursor() as cursor:
                    cursor.execute("SELECT account_number FROM users WHERE userid = %s",("saiganesh",))
                    test_acc=cursor.fetchone()
                    query=f'''SELECT * FROM transactions WHERE sender_acc= %s OR  receiver_acc= %s'''
                    df = pd.read_sql_query(query, con,params=(test_acc[0],test_acc[0]))
                    return "Statement ✅ succsessfully downloaded"
        except:
            return "Error occured while downloading the statement"
        
    
class Loans(Bank):
    def __init__(self, userid, balance1):
        self.userid = userid
        self.balance1 = balance1
        self.interest_rate = 0.05

    def balance(self):
        try:
            interest1 = self.interest_rate * self.balance1
            total = interest1 + self.balance1
            print(f"📈 Total amount with 5% Interest: ₹{total}")
        except:
            print("Error occured while calculating intrest")

class Openaccount(Bank):
    def __init__(self, Username, Userid, Password,Balance1=0):
        self.Username = Username
        self.Userid=Userid
        self.Password = Password
        self.Balance1=Balance1

    @staticmethod
    def accountnum(): #this function is for account number generation
        return "".join(secrets.SystemRandom().choices(string.digits,k=10))
        
    def open_account(self):
        acc_num = Openaccount.accountnum()
        try:
            with sql.connect(dbname=os.getenv("db_name"),user=os.getenv("db_user"),host=os.getenv("db_host"),port=os.getenv("db_port")) as con:
                with con.cursor() as cursor:
                    cursor.execute("INSERT INTO users (username, userid, password, account_number,balance) VALUES ( %s, %s, %s, %s, %s)", 
                       (self.Username,self.Userid, self.Password, acc_num,self.Balance1))
                    today_date = datetime.now().strftime("%B %d, %Y")
                    return acc_num, today_date
        except sql.IntegrityError:
            return sql.IntegrityError()
        except:
            return "An error occured while creating account"