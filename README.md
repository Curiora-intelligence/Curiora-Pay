# Curiora Pay

Curiora Pay is a modern, fast, and intelligent payment and banking system built with **FastAPI** and **PostgreSQL**. It offers a seamless experience for managing accounts, processing transactions, and features an integrated AI-driven loan approval system.

## 🚀 Features

* **User Authentication & Authorization**: Secure login and signup flows with session management.
* **Dashboard**: Intuitive dashboard for users to view their account balance, transaction history, and CIBIL score.
* **Internal Transactions**: Real-time fund transfers between users.
* **AI Loan Approvals**: Integrated machine learning model (Logistic Regression) that evaluates loan eligibility based on user balance and transaction history.
* **Asynchronous Database**: High-performance, non-blocking database operations using `psycopg3` and PostgreSQL.

## 🛠️ Tech Stack

* **Backend**: FastAPI (Python)
* **Database**: PostgreSQL (async with Psycopg 3)
* **Frontend**: HTML/CSS/JS with Jinja2 Templates
* **Machine Learning**: Scikit-Learn (Logistic Regression), Pandas
* **Environment Management**: python-dotenv

## 📁 Project Structure

```
Curiora-Pay/
├── main.py                 # FastAPI application entry point
├── database.py             # Asynchronous database setup and schemas
├── ai for loan.py          # Machine learning model training script
├── loan_model.pkl          # Serialized loan approval model
├── routers/                # FastAPI route definitions (auth, dashboard)
├── services/               # Core business logic and integrations
├── templates/              # Jinja2 HTML templates
├── static/                 # CSS, JS, and static assets
└── .env                    # Environment variables (DB credentials, secret keys)
```

## ⚙️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Curiora-intelligence/Curiora-Pay.git
   cd Curiora-Pay
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   *(Ensure you have the required packages installed, e.g., `fastapi`, `uvicorn`, `psycopg`, `pandas`, `scikit-learn`, `jinja2`, `python-dotenv`, `starlette`)*
   ```bash
   pip install fastapi uvicorn psycopg[binary] pandas scikit-learn jinja2 python-dotenv itsdangerous
   ```

4. **Environment Variables:**
   Create a `.env` file in the root directory and add your configuration:
   ```env
   db_name=your_db_name
   db_user=your_db_user
   db_password=your_db_password
   db_host=localhost
   db_port=5432
   secret_key=your_session_secret_key
   ```

5. **Initialize Database:**
   Uncomment the initialization lines in `database.py` and run it to set up the tables:
   ```bash
   python database.py
   ```

6. **Train the AI Model (Optional):**
   The repository includes a pre-trained `loan_model.pkl`. To retrain the model on new data, run:
   ```bash
   python "ai for loan.py"
   ```

7. **Run the Application:**
   ```bash
   uvicorn main:app --reload
   ```
   The application will be accessible at `http://127.0.0.1:8000`.

## 🧠 AI Loan Approval Model

Curiora Pay features an experimental AI model designed to evaluate loan applications. 
The model analyzes two primary factors:
- **Account Balance**
- **Transaction Frequency (Count)**

Using a Logistic Regression model trained via `scikit-learn`, it calculates the probability of loan repayment and automatically approves or rejects the application.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
