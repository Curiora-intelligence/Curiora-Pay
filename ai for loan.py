import pandas as pd,os
from sklearn.linear_model import LogisticRegression
import pickle # To save the trained model
import warnings
warnings.filterwarnings("ignore", message="X does not have valid feature names")

data = {
    'balance': [100, 20000, 50, 5000, 100000, 300, 0, 15000],
    'txn_count': [1, 50, 0, 20, 100, 2, 0, 30],
    'loan_approved': [0, 1, 0, 1, 1, 0, 0, 1] 
}

df = pd.DataFrame(data)
print(df)

X = df[['balance', 'txn_count']]
y = df['loan_approved']          

model = LogisticRegression()
model.fit(X, y)

if not os.path.exists("loan_model.pkl"):
    with open('loan_model.pkl', 'wb') as f:
        pickle.dump(model, f)
else:
    print("model already exist")

print("✅ Model Trained & Saved as 'loan_model.pkl'")

def test_user(bal, txns):
    prediction = model.predict([[bal, txns]])
    prob = model.predict_proba([[bal, txns]])[0][1] 
    
    if prediction[0] == 1:
         status = "APPROVED"
    else:
         status="REJECTED"
    print(f"User (Bal: {bal}, Txns: {txns}) -> {status} (Confidence: {int(prob*100)}%)")

print("\n--- 🧪 TEST RESULTS ---")
test_user(50000, 60) 
test_user(50, 1)     