from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expense_tracker.db'
# Secret key este obligatorie pentru securitatea sesiunilor și autentificării
app.config['SECRET_KEY'] = 'banana'

db = SQLAlchemy(app)

# Configurarea Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Tabelul de legătură pentru relația Many-to-Many dintre Utilizatori și Bugete
user_budget_association = db.Table('user_budget',
                                   db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                                   db.Column('budget_id', db.Integer, db.ForeignKey('budget.id'))
                                   )


# Modelul Utilizatorului
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_confirmed = db.Column(db.Boolean, default=False)
    budgets = db.relationship('Budget', secondary=user_budget_association, backref='users') # Relația cu bugetele


# Modelul Bugetului
class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    initial_balance = db.Column(db.Float, default=0.0)
    balance = db.Column(db.Float, default=0.0)
    transactions = db.relationship('Transaction', backref='budget', lazy=True)


# Modelul Tranzacției
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    # Legătura cu bugetul specific
    budget_id = db.Column(db.Integer, db.ForeignKey('budget.id'), nullable=False)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if ' ' in username:
            flash('Numele de utilizator nu poate conține spații.')
            return redirect(url_for('register'))

        user_exists = User.query.filter_by(username=username).first()
        email_exists = User.query.filter_by(email=email).first()

        if user_exists or email_exists:
            flash('Username-ul sau email-ul sunt deja folosite.')
            return redirect(url_for('register'))

        # Securitate: Hashing pentru parolă
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password_hash=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        # Token-ul de confirmare
        token = s.dumps(email, salt='email-confirm')
        confirm_url = url_for('confirm_email', token=token, _external=True)

        # simulare email
        print(f"\n[EMAIL] Accesează acest link pentru a confirma contul: {confirm_url}\n")

        flash('Cont creat! Verifică consola pentru link-ul de confirmare.')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except:
        flash('Link-ul de confirmare este invalid sau a expirat.')
        return redirect(url_for('login'))

    user = User.query.filter_by(email=email).first()
    if user.is_confirmed:
        flash('Contul este deja confirmat. Te rugăm să te autentifici.')
    else:
        user.is_confirmed = True
        db.session.commit()
        flash('Cont confirmat cu succes! Te poți autentifica.')

    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')  # [cite: 28]
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        # Verificăm dacă utilizatorul există și parola este corectă
        if not user or not check_password_hash(user.password_hash, password):
            flash('Email sau parolă incorectă.')
            return redirect(url_for('login'))

        # Verificăm dacă contul a fost confirmat prin email
        if not user.is_confirmed:
            flash('Te rugăm să îți confirmi contul înainte de a te autentifica.')
            return redirect(url_for('login'))

        login_user(user)
        return redirect(url_for('dashboard'))

    return render_template('login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    budgets = current_user.budgets
    return render_template('dashboard.html', budgets=budgets)


@app.route('/check_user', methods=['POST'])
@login_required
def check_user():
    data = request.get_json()
    username = data.get('username')

    if username == current_user.username:
        return jsonify({'exists': False, 'error': 'Nu te poți adăuga pe tine însuți.'})

    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({'exists': True})

    return jsonify({'exists': False, 'error': 'Utilizatorul nu a fost găsit.'})


@app.route('/add_budget', methods=['POST'])
@login_required
def add_budget():
    name = request.form.get('name')
    balance_str = request.form.get('balance')
    shared_with = request.form.getlist('shared_with')

    try:
        balance = float(balance_str)
    except ValueError:
        flash('Soldul trebuie să fie un număr valid.')
        return redirect(url_for('dashboard'))

    new_budget = Budget(name=name, initial_balance=balance, balance=balance)
    new_budget.users.append(current_user)

    # Parcurgem lista de username-uri trimise din form
    for uname in shared_with:
        user_to_share = User.query.filter_by(username=uname).first()
        if user_to_share and user_to_share not in new_budget.users:
            new_budget.users.append(user_to_share)

    db.session.add(new_budget)
    db.session.commit()
    flash('Bugetul a fost creat cu succes!')

    return redirect(url_for('dashboard'))


@app.route('/add_transaction', methods=['POST'])
@login_required
def add_transaction():
    name = request.form.get('name')
    transaction_type = request.form.get('transaction_type')
    amount_str = request.form.get('amount')
    category = request.form.get('category')
    date_str = request.form.get('date')
    budget_id = request.form.get('budget_id')

    # Validarea datelor (Suma nu poate fi negativă)
    try:
        amount = float(amount_str)
        if amount <= 0:
            flash('Suma trebuie să fie mai mare decât zero.')
            return redirect(url_for('dashboard'))
    except ValueError:
        flash('Suma trebuie să fie un număr valid.')
        return redirect(url_for('dashboard'))

    # Securitate: Verificăm dacă bugetul ales aparține efectiv utilizatorului logat
    budget = Budget.query.get(budget_id)
    if not budget or current_user not in budget.users:
        flash('Eroare: Nu ai acces la acest buget.')
        return redirect(url_for('dashboard'))

    try:
        transaction_date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        transaction_date = datetime.now(timezone.utc)

    # Crearea tranzacției
    new_transaction = Transaction(
        name=name,
        transaction_type=transaction_type,
        amount=amount,
        category=category,
        date=transaction_date,
        budget_id=budget.id
    )

    if transaction_type == 'Venit':
        budget.balance += amount
    elif transaction_type == 'Cheltuială':
        budget.balance -= amount

    # Salvarea în baza de date
    db.session.add(new_transaction)
    db.session.commit()

    flash('Tranzacția a fost adăugată și balanța actualizată!')
    return redirect(url_for('dashboard'))


@app.route('/delete_budget/<int:budget_id>')
@login_required
def delete_budget(budget_id):
    budget = Budget.query.get_or_404(budget_id)
    if current_user not in budget.users:
        flash('Nu ai permisiunea de a șterge acest buget.')
        return redirect(url_for('dashboard'))

    for t in budget.transactions:
        db.session.delete(t)

    db.session.delete(budget)
    db.session.commit()
    flash('Bugetul și tranzacțiile sale au fost șterse cu succes.')
    return redirect(url_for('dashboard'))


@app.route('/delete_transaction/<int:transaction_id>')
@login_required
def delete_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    budget = Budget.query.get(transaction.budget_id)

    if current_user not in budget.users:
        flash('Nu ai permisiunea de a șterge această tranzacție.')
        return redirect(url_for('dashboard'))

    if transaction.transaction_type == 'Venit':
        budget.balance -= transaction.amount
    else:
        budget.balance += transaction.amount

    db.session.delete(transaction)
    db.session.commit()
    flash('Tranzacția a fost eliminată.')
    return redirect(url_for('dashboard'))


@app.route('/reports', methods=['GET', 'POST'])
@login_required
def reports():
    # Setăm automat datele pe luna curentă pentru confortul utilizatorului
    today = datetime.now(timezone.utc)
    start_of_month = today.replace(day=1).strftime('%Y-%m-%d')
    end_date_default = today.strftime('%Y-%m-%d')

    # Prelucrăm datele din formular, sau folosim valorile default
    start_date_str = request.form.get('start_date') or start_of_month
    end_date_str = request.form.get('end_date') or end_date_default

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    # Setăm ora la 23:59:59 pentru a include toate tranzacțiile din ziua finală
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)

    # Identificăm toate bugetele la care utilizatorul are acces
    budgets = current_user.budgets
    budget_ids = [b.id for b in budgets]

    # Căutăm tranzacțiile care aparțin acestor bugete ȘI se încadrează în perioada selectată
    transactions = Transaction.query.filter(
        Transaction.budget_id.in_(budget_ids),
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).all()

    total_income = 0
    total_expense = 0
    expense_category_totals = {}
    income_category_totals = {}

    for t in transactions:
        if t.transaction_type == 'Venit':
            total_income += t.amount
            if t.category in income_category_totals:
                income_category_totals[t.category] += t.amount
            else:
                income_category_totals[t.category] = t.amount

        elif t.transaction_type == 'Cheltuială':
            total_expense += t.amount
            if t.category in expense_category_totals:
                expense_category_totals[t.category] += t.amount
            else:
                expense_category_totals[t.category] = t.amount

    total_initial_capital = sum(b.initial_balance for b in budgets)
    display_income_total = total_income + total_initial_capital

    return render_template('reports.html',
                           start_date=start_date_str,
                           end_date=end_date_str,
                           total_income=display_income_total,
                           total_expense=total_expense,
                           expense_category_totals=expense_category_totals,
                           income_category_totals=income_category_totals,
                           budgets=budgets)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)