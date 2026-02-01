from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from datetime import datetime
import requests
import csv
import io

app = Flask(__name__)
app.secret_key = 'kunci_sangat_rahasia_frontend'

API_BASE_URL = "http://localhost:8080/api"

def get_auth_headers():
    token = session.get('token')
    if token:
        return {'Authorization': f'Bearer {token}'}
    return {}

def organize_categories(categories_list):
    parents = [c for c in categories_list if not c.get('parent')]
    children = [c for c in categories_list if c.get('parent')]
    
    result = []
    
    for p in parents:
        result.append(p)
        
        p_id = p['id']
        my_kids = [k for k in children if k['parent']['id'] == p_id]
        
        for kid in my_kids:
            kid['name'] = f" ↳ {kid['name']}"
            result.append(kid)
            
    mapped_ids = [r['id'] for r in result]
    for c in categories_list:
        if c['id'] not in mapped_ids:
            result.append(c)
            
    return result

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
                session['user'] = {'username': username} 
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
    username = session.get('user', {}).get('username', 'User')
    user_role = 'CHILD' 
    
    family_members = {} 

    search_query = request.args.get('q', '').lower()

    try:
        resp_wallets = requests.get(f"{API_BASE_URL}/wallets", headers=headers)
        if resp_wallets.status_code == 200:
            wallets = resp_wallets.json()
            total_saldo = sum(w['balance'] for w in wallets)

        resp_trx = requests.get(f"{API_BASE_URL}/transactions", headers=headers)
        if resp_trx.status_code == 200:
            raw_transactions = resp_trx.json()
            
            if search_query:
                transactions = []
                for t in raw_transactions:
                    desc = t.get('description', '').lower() if t.get('description') else ''
                    cat = t['category']['name'].lower() if t.get('category') else ''
                    amt = str(t['amount'])
                    date = t['transactionDate']
                    
                    if search_query in desc or search_query in cat or search_query in amt or search_query in date:
                        transactions.append(t)
            else:
                transactions = raw_transactions

        resp_family = requests.get(f"{API_BASE_URL}/users/family", headers=headers)
        if resp_family.status_code == 200:
            members_list = resp_family.json()
            for m in members_list:
                family_members[m['id']] = m['username']
                if m['username'] == username:
                    user_role = m['role']
                
    except Exception as e:
        print(f"Error: {e}")

    expense_data = {}
    income_data = {}

    for t in transactions:
        cat_name = t['category']['name'] if t['category'] else 'Lainnya'
        
        if t['transactionType'] == 'EXPENSE':
            if cat_name in expense_data:
                expense_data[cat_name] += t['amount']
            else:
                expense_data[cat_name] = t['amount']
        elif t['transactionType'] == 'INCOME':
            if cat_name in income_data:
                income_data[cat_name] += t['amount']
            else:
                income_data[cat_name] = t['amount']

    expense_labels = list(expense_data.keys())
    expense_values = list(expense_data.values())
    
    income_labels = list(income_data.keys())
    income_values = list(income_data.values())

    return render_template('dashboard.html', 
                           wallets=wallets, 
                           transactions=transactions, 
                           total_saldo=total_saldo,
                           username=username,
                           role=user_role,
                           expense_labels=expense_labels, 
                           expense_values=expense_values,
                           income_labels=income_labels,
                           income_values=income_values,
                           family_members=family_members,
                           search_query=search_query)

@app.route('/tambah', methods=['GET', 'POST'])
def tambah_transaksi():
    if 'token' not in session:
        return redirect(url_for('login'))

    headers = get_auth_headers()
    
    mode = request.args.get('mode', 'EXPENSE') 

    if request.method == 'POST':
        raw_amount = request.form.get('amount', '0')
        clean_amount = raw_amount.replace('.', '')
        
        trx_date = request.form.get('transaction_date')
        if trx_date and len(trx_date) == 16: 
            trx_date += ":00"

        trx_type = request.form.get('type')

        data_transaksi = {
            "walletId": request.form.get('wallet_id'),
            "categoryId": request.form.get('category_id'),
            "amount": clean_amount,
            "description": request.form.get('description'),
            "type": trx_type,
            "transactionDate": trx_date
        }
        
        if trx_type == 'TRANSFER':
             data_transaksi["targetWalletId"] = request.form.get('target_wallet_id')
        
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

        if mode != 'TRANSFER':
            resp_categories = requests.get(f"{API_BASE_URL}/categories?type={mode}", headers=headers)
            if resp_categories.status_code == 200:
                raw_cats = resp_categories.json()
                categories = organize_categories(raw_cats)
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
    
    preset_type = request.args.get('type') 

    if request.method == 'POST':
        data = {
            "name": request.form.get('name'),
            "type": request.form.get('type'),
            "parentId": request.form.get('parent_id')
        }
        
        if not data['parentId']:
            data['parentId'] = None

        try:
            kirim = requests.post(f"{API_BASE_URL}/categories", json=data, headers=headers)
            if kirim.status_code == 200:
                flash("Kategori berhasil dibuat!", "success")
                return redirect(url_for('tambah_transaksi', mode=data['type']))
            else:
                flash(f"Gagal: {kirim.text}", "danger")
        except Exception as e:
            flash(f"Error: {e}", "danger")

    try:
        resp = requests.get(f"{API_BASE_URL}/categories", headers=headers)
        if resp.status_code == 200:
            all_cats = resp.json()
            parents = [c for c in all_cats if not c.get('parent')]
    except:
        pass

    return render_template('tambah_kategori.html', parents=parents, preset_type=preset_type)


@app.route('/edit/<int:transaction_id>', methods=['GET', 'POST'])
def edit_transaksi(transaction_id):
    if 'token' not in session:
        return redirect(url_for('login'))
    
    headers = get_auth_headers()

    if request.method == 'POST':
        raw_amount = request.form.get('amount', '0')
        clean_amount = raw_amount.replace('.', '')
        
        trx_date = request.form.get('transaction_date')
        if trx_date and len(trx_date) == 16: 
            trx_date += ":00"
        
        trx_type = request.form.get('type')

        data_update = {
            "walletId": request.form.get('wallet_id'),
            "categoryId": request.form.get('category_id'),
            "amount": clean_amount,
            "description": request.form.get('description'),
            "type": trx_type,
            "transactionDate": trx_date
        }

        if trx_type == 'TRANSFER':
             data_update["targetWalletId"] = request.form.get('target_wallet_id')

        try:
            kirim = requests.put(f"{API_BASE_URL}/transactions/{transaction_id}", json=data_update, headers=headers)
            if kirim.status_code == 200:
                flash("Transaksi berhasil diperbarui!", "success")
                return redirect(url_for('dashboard'))
            else:
                flash(f"Gagal update: {kirim.text}", "danger")
        except Exception as e:
            flash(f"Error: {e}", "danger")

    try:
        resp_trx = requests.get(f"{API_BASE_URL}/transactions/{transaction_id}", headers=headers)
        if resp_trx.status_code != 200:
            flash("Transaksi tidak ditemukan", "danger")
            return redirect(url_for('dashboard'))
        transaction = resp_trx.json()
    except:
        return redirect(url_for('dashboard'))

    wallets = []
    categories = []
    try:
        wallets = requests.get(f"{API_BASE_URL}/wallets", headers=headers).json()
        cat_type = transaction['transactionType']
        
        if cat_type != 'TRANSFER':
            raw_cats = requests.get(f"{API_BASE_URL}/categories?type={cat_type}", headers=headers).json()
            categories = organize_categories(raw_cats)
    except:
        pass

    return render_template('edit_transaksi.html', transaction=transaction, wallets=wallets, categories=categories)

@app.route('/kalender')
def kalender():
    if 'token' not in session:
        return redirect(url_for('login'))

    headers = get_auth_headers()
    events = []
    transactions = [] 

    try:
        resp = requests.get(f"{API_BASE_URL}/transactions", headers=headers)
        if resp.status_code == 200:
            transactions = resp.json()
            
            summary = {}
            
            for t in transactions:
                date_str = t['transactionDate'][:10]
                amount = t['amount']
                jenis = t['transactionType']
                
                if date_str not in summary:
                    summary[date_str] = {'INCOME': 0, 'EXPENSE': 0}
                
                if jenis in ['INCOME', 'EXPENSE']:
                    summary[date_str][jenis] += amount

            for date, vals in summary.items():
                if vals['INCOME'] > 0:
                    events.append({
                        'title': f"+ {vals['INCOME']:,}".replace(',', '.'),
                        'start': date,
                        'color': '#198754',
                        'textColor': 'white',
                        'extendedProps': {'type': 'INCOME'}
                    })
                
                if vals['EXPENSE'] > 0:
                    events.append({
                        'title': f"- {vals['EXPENSE']:,}".replace(',', '.'),
                        'start': date,
                        'color': '#dc3545', 
                        'textColor': 'white',
                        'extendedProps': {'type': 'EXPENSE'}
                    })

    except Exception as e:
        print(f"Error Kalender: {e}")

    return render_template('kalender.html', events=events, transactions=transactions)

@app.route('/statistik')
def statistik():
    if 'token' not in session:
        return redirect(url_for('login'))

    headers = get_auth_headers()
    
    total_income = 0
    total_expense = 0
    
    wallet_names = []
    wallet_balances = []

    income_cat_map = {}
    expense_cat_map = {}

    try:
        resp_trx = requests.get(f"{API_BASE_URL}/transactions", headers=headers)
        if resp_trx.status_code == 200:
            transactions = resp_trx.json()
            for t in transactions:
                amount = t['amount']
                tipe = t['transactionType']
                cat_name = t['category']['name'] if t['category'] else 'Tanpa Kategori'

                if tipe == 'INCOME':
                    total_income += amount
                    if cat_name in income_cat_map:
                        income_cat_map[cat_name] += amount
                    else:
                        income_cat_map[cat_name] = amount

                elif tipe == 'EXPENSE':
                    total_expense += amount
                    if cat_name in expense_cat_map:
                        expense_cat_map[cat_name] += amount
                    else:
                        expense_cat_map[cat_name] = amount

        resp_wallet = requests.get(f"{API_BASE_URL}/wallets", headers=headers)
        if resp_wallet.status_code == 200:
            wallets = resp_wallet.json()
            for w in wallets:
                wallet_names.append(w['walletName'])
                wallet_balances.append(w['balance'])

    except Exception as e:
        print(f"Error Statistik: {e}")

    return render_template('statistik.html', 
                           income=total_income, 
                           expense=total_expense,
                           wallet_labels=wallet_names,
                           wallet_data=wallet_balances,
                           inc_cat_labels=list(income_cat_map.keys()),
                           inc_cat_values=list(income_cat_map.values()),
                           exp_cat_labels=list(expense_cat_map.keys()),
                           exp_cat_values=list(expense_cat_map.values()))

@app.route('/download_laporan')
def download_laporan():
    if 'token' not in session:
        return redirect(url_for('login'))

    headers = get_auth_headers()
    
    try:
        resp = requests.get(f"{API_BASE_URL}/transactions", headers=headers)
        if resp.status_code != 200:
            flash("Gagal mengambil data untuk download", "danger")
            return redirect(url_for('statistik'))
            
        transactions = resp.json()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['ID Transaksi', 'Tanggal', 'Tipe', 'Kategori', 'Keterangan', 'Jumlah (Rp)', 'Dompet Sumber', 'Dompet Tujuan'])
        
        for t in transactions:
            t_date = t['transactionDate'][:16].replace('T', ' ')
            t_type = t['transactionType']
            t_cat = t['category']['name'] if t.get('category') else '-'
            t_desc = t.get('description', '-')
            t_amount = t['amount']
            t_wallet = t['wallet']['walletName'] if t.get('wallet') else '-'
            t_target = t['targetWallet']['walletName'] if t.get('targetWallet') else '-'
            
            if t_type == 'TRANSFER':
                t_cat = 'TRANSFER ANTAR DOMPET'
            
            writer.writerow([t['id'], t_date, t_type, t_cat, t_desc, t_amount, t_wallet, t_target])
            
        output.seek(0)
        
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=laporan_keuangan.csv"}
        )

    except Exception as e:
        flash(f"Error download: {e}", "danger")
        return redirect(url_for('statistik'))

@app.route('/hapus/<int:transaction_id>', methods=['POST']) 
def hapus_transaksi(transaction_id):
    if 'token' not in session:
        return redirect(url_for('login'))
    
    headers = get_auth_headers()
    
    try:

        resp = requests.delete(f"{API_BASE_URL}/transactions/{transaction_id}", headers=headers)
        
        if resp.status_code == 200:
            flash("Transaksi berhasil dihapus & saldo dikembalikan.", "success")
        else:
            flash(f"Gagal menghapus: {resp.text}", "danger")
            
    except Exception as e:
        flash(f"Error sistem: {e}", "danger")
        
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        family_id = request.form.get('family_id')

        payload = {
            "username": username,
            "email": email,
            "password": password,
            "role": role,
            "familyId": family_id
        }

        try:
            resp = requests.post(f"{API_BASE_URL}/auth/register", json=payload)
            if resp.status_code == 200:
                flash("Registrasi berhasil! Silakan login.", "success")
                return redirect(url_for('login'))
            else:
                flash(f"Gagal: {resp.text}", "danger")
        except Exception as e:
            flash(f"Error: {e}", "danger")

    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)