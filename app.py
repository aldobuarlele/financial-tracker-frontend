from flask import Flask, render_template, request, redirect, url_for, flash, session
import requests

app = Flask(__name__)
app.secret_key = 'kunci_sangat_rahasia_frontend'

API_BASE_URL = "http://localhost:8080/api"

def get_auth_headers():
    token = session.get('token')
    if token:
        return {'Authorization': f'Bearer {token}'}
    return {}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        payload = {'username': username, 'password': password}
        
        try:
            response = requests.post(f"{API_BASE_URL}/auth/login", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                session['token'] = data.get('accessToken')
                session['username'] = username
                return redirect(url_for('dashboard'))
            else:
                flash('Login Gagal! Username atau Password salah.', 'danger')
        except Exception as e:
            flash(f'Error koneksi ke Backend: {e}', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def dashboard():
    if 'token' not in session:
        return redirect(url_for('login'))

    headers = get_auth_headers()
    wallets = []
    transactions = []
    total_saldo = 0
    chart_labels = []
    chart_values = []

    try:
        resp_wallets = requests.get(f"{API_BASE_URL}/wallets", headers=headers)
        if resp_wallets.status_code == 200:
            wallets = resp_wallets.json()
            total_saldo = sum(w['balance'] for w in wallets)
        elif resp_wallets.status_code == 403:
            return redirect(url_for('logout'))

        resp_trx = requests.get(f"{API_BASE_URL}/transactions", headers=headers)
        if resp_trx.status_code == 200:
            transactions = resp_trx.json()
            
            expense_map = {}
            for t in transactions:
                if t['transactionType'] == 'EXPENSE':
                    cat_name = t['category']['name'] if t['category'] else 'Lain-lain'
                    amount = t['amount']
                    if cat_name in expense_map:
                        expense_map[cat_name] += amount
                    else:
                        expense_map[cat_name] = amount
            
            chart_labels = list(expense_map.keys())
            chart_values = list(expense_map.values())
            
    except:
        pass

    return render_template('dashboard.html', 
                           wallets=wallets, 
                           total_saldo=total_saldo, 
                           transactions=transactions,
                           chart_labels=chart_labels,
                           chart_values=chart_values,
                           username=session.get('username'))

@app.route('/tambah', methods=['GET', 'POST'])
def tambah_transaksi():
    if 'token' not in session:
        return redirect(url_for('login'))

    headers = get_auth_headers()
    
    mode = request.args.get('mode', 'EXPENSE') 

    if request.method == 'POST':
        raw_amount = request.form.get('amount', '0')
        clean_amount = raw_amount.replace('.', '')

        data_transaksi = {
            "walletId": request.form.get('wallet_id'),
            "categoryId": request.form.get('category_id'),
            "amount": clean_amount,
            "description": request.form.get('description'),
            "type": request.form.get('type'),
            "transactionDate": request.form.get('transaction_date')
        }
        
        try:
            kirim = requests.post(f"{API_BASE_URL}/transactions", json=data_transaksi, headers=headers)
            if kirim.status_code == 200:
                flash("Transaksi berhasil disimpan!", "success")
                return redirect(url_for('dashboard'))
            else:
                flash(f"Gagal menyimpan: {kirim.text}", "danger")
        except Exception as e:
            flash(f"Error sistem: {e}", "danger")

    wallets = []
    categories = []

    try:
        resp_wallets = requests.get(f"{API_BASE_URL}/wallets", headers=headers)
        if resp_wallets.status_code == 200:
            wallets = resp_wallets.json()

        resp_categories = requests.get(f"{API_BASE_URL}/categories?type={mode}", headers=headers)
        if resp_categories.status_code == 200:
            categories = resp_categories.json()
    except:
        pass

    return render_template('form_transaksi.html', wallets=wallets, categories=categories, mode=mode)

@app.route('/tambah-dompet', methods=['GET', 'POST'])
def tambah_dompet():
    if 'token' not in session:
        return redirect(url_for('login'))
    
    headers = get_auth_headers()

    if request.method == 'POST':
        raw_balance = request.form.get('balance', '0')
        clean_balance = raw_balance.replace('.', '')

        data = {
            "walletName": request.form.get('wallet_name'),
            "walletType": request.form.get('wallet_type'),
            "balance": clean_balance
        }

        try:
            kirim = requests.post(f"{API_BASE_URL}/wallets", json=data, headers=headers)
            if kirim.status_code == 200:
                flash("Dompet berhasil dibuat!", "success")
                return redirect(url_for('dashboard'))
            else:
                flash(f"Gagal: {kirim.text}", "danger")
        except Exception as e:
            flash(f"Error: {e}", "danger")

    return render_template('tambah_dompet.html')

@app.route('/tambah-kategori', methods=['GET', 'POST'])
def tambah_kategori():
    if 'token' not in session:
        return redirect(url_for('login'))
    
    headers = get_auth_headers()

    if request.method == 'POST':
        data = {
            "name": request.form.get('name'),
            "type": request.form.get('type')
        }

        try:
            kirim = requests.post(f"{API_BASE_URL}/categories", json=data, headers=headers)
            if kirim.status_code == 200:
                flash("Kategori berhasil dibuat!", "success")
                return redirect(url_for('tambah_transaksi', mode=data['type']))
            else:
                flash(f"Gagal: {kirim.text}", "danger")
        except Exception as e:
            flash(f"Error: {e}", "danger")

    return render_template('tambah_kategori.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)