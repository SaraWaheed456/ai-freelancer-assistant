from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response, send_file, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from fpdf import FPDF
from groq import Groq
import os
import tempfile
import time

app = Flask(__name__)
app.secret_key = "ai_freelancer_secret_key_2026"
DB_NAME = "database.db"
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------- GROQ SETUP ----------
def get_groq_key():
    conn = get_db()
    setting = conn.execute('SELECT value FROM settings WHERE user_id = ? AND key = ?', 
                          (session.get('user_id'), 'groq_api_key')).fetchone()
    conn.close()
    if setting and setting['value']:
        return setting['value']
    return "your-groq-api-key-here"

def generate_ai_content(prompt):
    for attempt in range(3):
        try:
            client = Groq(api_key=get_groq_key())
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                timeout=30
            )
            return response.choices[0].message.content
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
                continue
            raise e

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

    c.execute("""CREATE TABLE IF NOT EXISTS user_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        full_name TEXT,
        skills TEXT,
        bio TEXT,
        phone TEXT,
        location TEXT,
        profile_picture TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id))""")

    c.execute("""CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        key TEXT NOT NULL,
        value TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id))""")

    c.execute("""CREATE TABLE IF NOT EXISTS proposals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        client_name TEXT, project_title TEXT,
        project_description TEXT, skills TEXT,
        budget TEXT, timeline TEXT, tone TEXT,
        generated_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id))""")

    c.execute("""CREATE TABLE IF NOT EXISTS cover_letters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        job_title TEXT, company_name TEXT,
        experience TEXT, skills TEXT,
        portfolio_url TEXT, generated_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id))""")

    c.execute("""CREATE TABLE IF NOT EXISTS gig_descriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category TEXT, skills TEXT,
        experience_level TEXT, delivery_time TEXT,
        features TEXT, revisions TEXT,
        generated_description TEXT, seo_keywords TEXT,
        faq_suggestions TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id))""")

    c.execute("""CREATE TABLE IF NOT EXISTS pricing_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        hourly_rate TEXT, estimated_hours TEXT,
        complexity TEXT, urgency TEXT,
        additional_charges TEXT, tax TEXT,
        suggested_price TEXT, ai_analysis TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id))""")

    c.execute("""CREATE TABLE IF NOT EXISTS client_replies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        client_message TEXT, tone TEXT,
        generated_reply TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id))""")

    c.execute("""CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        client_name TEXT, client_email TEXT,
        project_title TEXT, services TEXT,
        amount TEXT, tax TEXT,
        total_amount TEXT, due_date TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id))""")

    c.execute("""CREATE TABLE IF NOT EXISTS contracts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        client_name TEXT, client_email TEXT,
        freelancer_name TEXT, freelancer_email TEXT,
        project_scope TEXT, timeline TEXT,
        payment_terms TEXT, terms_conditions TEXT,
        generated_contract TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id))""")
    
    # Add missing columns if they don't exist
    try:
        c.execute("ALTER TABLE user_profiles ADD COLUMN bio TEXT")
    except:
        pass
    try:
        c.execute("ALTER TABLE user_profiles ADD COLUMN phone TEXT")
    except:
       pass
    try:
        c.execute("ALTER TABLE user_profiles ADD COLUMN location TEXT")
    except:
       pass
    try:
       c.execute("ALTER TABLE user_profiles ADD COLUMN profile_picture TEXT")
    except:
      pass
    try:
       c.execute("CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, key TEXT NOT NULL, value TEXT, FOREIGN KEY (user_id) REFERENCES users(id))")
    except:
       pass

    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ---------- AUTH ----------
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password']
        if not email or not password:
            flash('Please fill in all fields.')
            return redirect(url_for('login'))
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['email'] = user['email']
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form['fullname'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        confirm = request.form['confirmPassword']
        if not fullname or not email or not password:
            flash('Please fill in all fields.')
            return redirect(url_for('register'))
        if len(password) < 6:
            flash('Password must be at least 6 characters.')
            return redirect(url_for('register'))
        if password != confirm:
            flash("Passwords don't match.")
            return redirect(url_for('register'))
        hashed = generate_password_hash(password)
        conn = get_db()
        try:
            cur = conn.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, hashed))
            conn.execute('INSERT INTO user_profiles (user_id, full_name) VALUES (?, ?)', (cur.lastrowid, fullname))
            conn.commit()
        except sqlite3.IntegrityError:
            flash('Email already registered.')
            conn.close()
            return redirect(url_for('register'))
        conn.close()
        flash('Account created! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        flash('Reset link sent if email exists.')
        return redirect(url_for('forgot_password'))
    return render_template('forgot_password.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------- DASHBOARD ----------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    profile = conn.execute('SELECT * FROM user_profiles WHERE user_id = ?', (session['user_id'],)).fetchone()
    proposal_count = conn.execute('SELECT COUNT(*) FROM proposals WHERE user_id = ?', (session['user_id'],)).fetchone()[0]
    cover_letter_count = conn.execute('SELECT COUNT(*) FROM cover_letters WHERE user_id = ?', (session['user_id'],)).fetchone()[0]
    gig_count = conn.execute('SELECT COUNT(*) FROM gig_descriptions WHERE user_id = ?', (session['user_id'],)).fetchone()[0]
    pricing_count = conn.execute('SELECT COUNT(*) FROM pricing_history WHERE user_id = ?', (session['user_id'],)).fetchone()[0]
    reply_count = conn.execute('SELECT COUNT(*) FROM client_replies WHERE user_id = ?', (session['user_id'],)).fetchone()[0]
    invoice_count = conn.execute('SELECT COUNT(*) FROM invoices WHERE user_id = ?', (session['user_id'],)).fetchone()[0]
    contract_count = conn.execute('SELECT COUNT(*) FROM contracts WHERE user_id = ?', (session['user_id'],)).fetchone()[0]
    recent_proposals = conn.execute('SELECT * FROM proposals WHERE user_id = ? ORDER BY created_at DESC LIMIT 2', (session['user_id'],)).fetchall()
    recent_covers = conn.execute('SELECT * FROM cover_letters WHERE user_id = ? ORDER BY created_at DESC LIMIT 2', (session['user_id'],)).fetchall()
    recent_gigs = conn.execute('SELECT * FROM gig_descriptions WHERE user_id = ? ORDER BY created_at DESC LIMIT 2', (session['user_id'],)).fetchall()
    recent_replies = conn.execute('SELECT * FROM client_replies WHERE user_id = ? ORDER BY created_at DESC LIMIT 2', (session['user_id'],)).fetchall()
    conn.close()
    full_name = profile['full_name'] if profile else session['email']
    profile_picture = profile['profile_picture'] if profile and profile['profile_picture'] else None
    return render_template('dashboard.html',
        full_name=full_name, profile_picture=profile_picture,
        proposal_count=proposal_count, cover_letter_count=cover_letter_count,
        gig_count=gig_count, pricing_count=pricing_count,
        reply_count=reply_count, invoice_count=invoice_count,
        contract_count=contract_count,
        recent_proposals=recent_proposals, recent_covers=recent_covers,
        recent_gigs=recent_gigs, recent_replies=recent_replies)

# ---------- HISTORY ----------
@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    proposals = conn.execute('SELECT *, "proposal" as type FROM proposals WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],)).fetchall()
    covers = conn.execute('SELECT *, "cover_letter" as type FROM cover_letters WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],)).fetchall()
    gigs = conn.execute('SELECT *, "gig" as type FROM gig_descriptions WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],)).fetchall()
    invoices = conn.execute('SELECT *, "invoice" as type FROM invoices WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],)).fetchall()
    contracts = conn.execute('SELECT *, "contract" as type FROM contracts WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],)).fetchall()
    replies = conn.execute('SELECT *, "reply" as type FROM client_replies WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],)).fetchall()
    pricing = conn.execute('SELECT * FROM pricing_history WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('history.html',
        proposals=proposals, covers=covers, gigs=gigs,
        invoices=invoices, contracts=contracts, replies=replies,pricing=pricing)

# ---------- PROFILE ----------
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    user_profile = conn.execute('SELECT * FROM user_profiles WHERE user_id = ?', (session['user_id'],)).fetchone()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_profile':
            full_name = request.form.get('full_name', '').strip()
            bio = request.form.get('bio', '').strip()
            phone = request.form.get('phone', '').strip()
            location = request.form.get('location', '').strip()
            skills = request.form.get('skills', '').strip()

            profile_picture_path = user_profile['profile_picture'] if user_profile and user_profile['profile_picture'] else None

            # Profile picture handle karo
            if 'profile_picture' in request.files:
                file = request.files['profile_picture']
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(f"user_{session['user_id']}_{file.filename}")
                    save_path = os.path.join('static', 'uploads', filename)
                    file.save(save_path)
                    profile_picture_path = f"uploads/{filename}"

            conn.execute("""UPDATE user_profiles 
                SET full_name=?, bio=?, phone=?, location=?, skills=?, profile_picture=?
                WHERE user_id=?""",
                (full_name, bio, phone, location, skills, profile_picture_path, session['user_id']))
            conn.commit()
            flash('Profile updated successfully!')

        elif action == 'change_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            if not check_password_hash(user['password'], current_password):
                flash('Current password is incorrect.')
            elif len(new_password) < 6:
                flash('New password must be at least 6 characters.')
            elif new_password != confirm_password:
                flash("New passwords don't match.")
            else:
                conn.execute('UPDATE users SET password = ? WHERE id = ?',
                    (generate_password_hash(new_password), session['user_id']))
                conn.commit()
                flash('Password changed successfully!')

        conn.close()
        return redirect(url_for('profile'))

    conn.close()
    return render_template('profile.html', profile=user_profile, user=user)

# ---------- SETTINGS ----------
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'save_api_key':
            api_key = request.form.get('groq_api_key', '').strip()
            existing = conn.execute('SELECT * FROM settings WHERE user_id = ? AND key = ?',
                (session['user_id'], 'groq_api_key')).fetchone()
            if existing:
                conn.execute('UPDATE settings SET value = ? WHERE user_id = ? AND key = ?',
                    (api_key, session['user_id'], 'groq_api_key'))
            else:
                conn.execute('INSERT INTO settings (user_id, key, value) VALUES (?, ?, ?)',
                    (session['user_id'], 'groq_api_key', api_key))
            conn.commit()
            flash('API Key saved successfully!')

        elif action == 'save_preferences':
            for key in ['theme', 'language', 'notifications']:
                value = request.form.get(key, '')
                existing = conn.execute('SELECT * FROM settings WHERE user_id = ? AND key = ?',
                    (session['user_id'], key)).fetchone()
                if existing:
                    conn.execute('UPDATE settings SET value = ? WHERE user_id = ? AND key = ?',
                        (value, session['user_id'], key))
                else:
                    conn.execute('INSERT INTO settings (user_id, key, value) VALUES (?, ?, ?)',
                        (session['user_id'], key, value))
            conn.commit()
            flash('Settings saved successfully!')

        conn.close()
        return redirect(url_for('settings'))

    all_settings = {}
    rows = conn.execute('SELECT key, value FROM settings WHERE user_id = ?', (session['user_id'],)).fetchall()
    for row in rows:
        all_settings[row['key']] = row['value']
    conn.close()
    return render_template('settings.html', settings=all_settings)

# ---------- PROPOSALS ----------
@app.route('/proposals')
def proposals():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    all_proposals = conn.execute('SELECT * FROM proposals WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('proposals.html', proposals=all_proposals)

@app.route('/proposals/create', methods=['GET', 'POST'])
def create_proposal():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    generated_text = None
    if request.method == 'POST':
        client_name = request.form['client_name'].strip()
        project_title = request.form['project_title'].strip()
        project_description = request.form['project_description'].strip()
        skills = request.form['skills'].strip()
        budget = request.form['budget'].strip()
        timeline = request.form['timeline'].strip()
        tone = request.form['tone']
        action = request.form.get('action')
        if not all([client_name, project_title, project_description, skills, budget, timeline]):
            flash('Please fill in all required fields.')
            return render_template('create_proposal.html', generated_text=None)
        prompt = f"""Write a professional freelance proposal:
- Client Name: {client_name}
- Project Title: {project_title}
- Project Description: {project_description}
- My Skills: {skills}
- Budget: {budget}
- Timeline: {timeline}
- Tone: {tone}
Write a compelling {tone.lower()} tone proposal. No markdown formatting."""
        try:
            generated_text = generate_ai_content(prompt)
        except Exception as e:
            flash(f"AI Error: {str(e)}")
            return render_template('create_proposal.html', generated_text=None)
        if action == 'save':
            conn = get_db()
            conn.execute("""INSERT INTO proposals (user_id, client_name, project_title, project_description, skills, budget, timeline, tone, generated_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (session['user_id'], client_name, project_title, project_description, skills, budget, timeline, tone, generated_text))
            conn.commit()
            conn.close()
            flash('Proposal saved!')
            return redirect(url_for('proposals'))
        return render_template('create_proposal.html', generated_text=generated_text,
            client_name=client_name, project_title=project_title,
            project_description=project_description, skills=skills,
            budget=budget, timeline=timeline, tone=tone)
    return render_template('create_proposal.html', generated_text=None)

@app.route('/proposals/edit/<int:pid>', methods=['GET', 'POST'])
def edit_proposal(pid):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    proposal = conn.execute('SELECT * FROM proposals WHERE id = ? AND user_id = ?', (pid, session['user_id'])).fetchone()
    if not proposal:
        flash('Proposal not found.')
        return redirect(url_for('proposals'))
    if request.method == 'POST':
        conn.execute('UPDATE proposals SET generated_text = ? WHERE id = ?', (request.form['generated_text'], pid))
        conn.commit()
        conn.close()
        flash('Proposal updated!')
        return redirect(url_for('proposals'))
    conn.close()
    return render_template('edit_proposal.html', proposal=proposal)

@app.route('/proposals/delete/<int:pid>')
def delete_proposal(pid):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    conn.execute('DELETE FROM proposals WHERE id = ? AND user_id = ?', (pid, session['user_id']))
    conn.commit()
    conn.close()
    flash('Proposal deleted.')
    return redirect(url_for('proposals'))

@app.route('/proposals/export/<int:pid>')
def export_proposal_pdf(pid):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    p = conn.execute('SELECT * FROM proposals WHERE id = ? AND user_id = ?', (pid, session['user_id'])).fetchone()
    conn.close()
    if not p:
        flash('Proposal not found.')
        return redirect(url_for('proposals'))
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, p['project_title'], ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Client: {p['client_name']} | Budget: {p['budget']} | Timeline: {p['timeline']}", ln=True)
    pdf.ln(5)
    pdf.multi_cell(0, 7, p['generated_text'])
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf.output(tmp.name)
    tmp.close()
    return send_file(tmp.name, mimetype='application/pdf', as_attachment=True, download_name=f'proposal_{pid}.pdf')

# ---------- COVER LETTERS ----------
@app.route('/cover-letters')
def cover_letters():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    all_letters = conn.execute('SELECT * FROM cover_letters WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('cover_letters.html', cover_letters=all_letters)

@app.route('/cover-letters/create', methods=['GET', 'POST'])
def create_cover_letter():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    generated_text = None
    if request.method == 'POST':
        job_title = request.form['job_title'].strip()
        company_name = request.form['company_name'].strip()
        experience = request.form['experience'].strip()
        skills = request.form['skills'].strip()
        portfolio_url = request.form.get('portfolio_url', '').strip()
        action = request.form.get('action')
        if not all([job_title, company_name, experience, skills]):
            flash('Please fill in all required fields.')
            return render_template('create_cover_letter.html', generated_text=None)
        prompt = f"""Write a professional cover letter:
- Job Title: {job_title}
- Company: {company_name}
- Experience: {experience}
- Skills: {skills}
- Portfolio: {portfolio_url}
Professional, natural, no markdown."""
        try:
            generated_text = generate_ai_content(prompt)
        except Exception as e:
            flash(f"AI Error: {str(e)}")
            return render_template('create_cover_letter.html', generated_text=None)
        if action == 'save':
            conn = get_db()
            conn.execute("""INSERT INTO cover_letters (user_id, job_title, company_name, experience, skills, portfolio_url, generated_text)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (session['user_id'], job_title, company_name, experience, skills, portfolio_url, generated_text))
            conn.commit()
            conn.close()
            flash('Cover letter saved!')
            return redirect(url_for('cover_letters'))
        return render_template('create_cover_letter.html', generated_text=generated_text,
            job_title=job_title, company_name=company_name,
            experience=experience, skills=skills, portfolio_url=portfolio_url)
    return render_template('create_cover_letter.html', generated_text=None)

@app.route('/cover-letters/edit/<int:lid>', methods=['GET', 'POST'])
def edit_cover_letter(lid):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    letter = conn.execute('SELECT * FROM cover_letters WHERE id = ? AND user_id = ?', (lid, session['user_id'])).fetchone()
    if not letter:
        flash('Cover letter not found.')
        return redirect(url_for('cover_letters'))
    if request.method == 'POST':
        conn.execute('UPDATE cover_letters SET generated_text = ? WHERE id = ?', (request.form['generated_text'], lid))
        conn.commit()
        conn.close()
        flash('Cover letter updated!')
        return redirect(url_for('cover_letters'))
    conn.close()
    return render_template('edit_cover_letter.html', letter=letter)

@app.route('/cover-letters/delete/<int:lid>')
def delete_cover_letter(lid):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    conn.execute('DELETE FROM cover_letters WHERE id = ? AND user_id = ?', (lid, session['user_id']))
    conn.commit()
    conn.close()
    flash('Cover letter deleted.')
    return redirect(url_for('cover_letters'))

@app.route('/cover-letters/export/<int:lid>')
def export_cover_letter_pdf(lid):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    l = conn.execute('SELECT * FROM cover_letters WHERE id = ? AND user_id = ?', (lid, session['user_id'])).fetchone()
    conn.close()
    if not l:
        flash('Not found.')
        return redirect(url_for('cover_letters'))
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"Cover Letter - {l['job_title']}", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Company: {l['company_name']}", ln=True)
    pdf.ln(5)
    pdf.multi_cell(0, 7, l['generated_text'])
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf.output(tmp.name)
    tmp.close()
    return send_file(tmp.name, mimetype='application/pdf', as_attachment=True, download_name=f'cover_letter_{lid}.pdf')

# ---------- GIG GENERATOR ----------
@app.route('/gig-generator')
def gig_generator():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    all_gigs = conn.execute('SELECT * FROM gig_descriptions WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('gig_generator.html', gigs=all_gigs)

@app.route('/gig-generator/create', methods=['GET', 'POST'])
def create_gig():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    generated_description = seo_keywords = faq_suggestions = None
    if request.method == 'POST':
        category = request.form['category'].strip()
        skills = request.form['skills'].strip()
        experience_level = request.form['experience_level']
        delivery_time = request.form['delivery_time'].strip()
        features = request.form['features'].strip()
        revisions = request.form['revisions'].strip()
        action = request.form.get('action')
        if not all([category, skills, delivery_time, features, revisions]):
            flash('Please fill in all required fields.')
            return render_template('create_gig.html', generated_description=None)
        prompt = f"""Generate Fiverr gig content:
- Category: {category}
- Skills: {skills}
- Experience: {experience_level}
- Delivery: {delivery_time}
- Features: {features}
- Revisions: {revisions}

Format EXACTLY like this:
GIG DESCRIPTION:
[150-200 word description]

SEO KEYWORDS:
[8-10 comma separated keywords]

FAQ:
Q1: [question]
A1: [answer]
Q2: [question]
A2: [answer]
Q3: [question]
A3: [answer]"""
        try:
            ai_response = generate_ai_content(prompt)
            parts = ai_response.split('SEO KEYWORDS:')
            generated_description = parts[0].replace('GIG DESCRIPTION:', '').strip()
            if len(parts) > 1:
                faq_parts = parts[1].split('FAQ:')
                seo_keywords = faq_parts[0].strip()
                faq_suggestions = faq_parts[1].strip() if len(faq_parts) > 1 else ''
        except Exception as e:
            flash(f"AI Error: {str(e)}")
            return render_template('create_gig.html', generated_description=None)
        if action == 'save':
            conn = get_db()
            conn.execute("""INSERT INTO gig_descriptions (user_id, category, skills, experience_level, delivery_time, features, revisions, generated_description, seo_keywords, faq_suggestions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (session['user_id'], category, skills, experience_level, delivery_time, features, revisions, generated_description, seo_keywords, faq_suggestions))
            conn.commit()
            conn.close()
            flash('Gig description saved!')
            return redirect(url_for('gig_generator'))
        return render_template('create_gig.html',
            generated_description=generated_description, seo_keywords=seo_keywords,
            faq_suggestions=faq_suggestions, category=category, skills=skills,
            experience_level=experience_level, delivery_time=delivery_time,
            features=features, revisions=revisions)
    return render_template('create_gig.html', generated_description=None)

@app.route('/gig-generator/delete/<int:gid>')
def delete_gig(gid):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    conn.execute('DELETE FROM gig_descriptions WHERE id = ? AND user_id = ?', (gid, session['user_id']))
    conn.commit()
    conn.close()
    flash('Gig deleted.')
    return redirect(url_for('gig_generator'))

# ---------- PRICING ----------
@app.route('/pricing')
def pricing():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    all_pricing = conn.execute('SELECT * FROM pricing_history WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('pricing.html', pricing_history=all_pricing)

@app.route('/pricing/create', methods=['GET', 'POST'])
def create_pricing():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    suggested_price = ai_analysis = None
    if request.method == 'POST':
        hourly_rate = request.form['hourly_rate']
        estimated_hours = request.form['estimated_hours']
        complexity = request.form['complexity']
        urgency = request.form['urgency']
        additional_charges = request.form.get('additional_charges', '0') or '0'
        tax = request.form.get('tax', '0') or '0'
        action = request.form.get('action')
        try:
            base = float(hourly_rate) * float(estimated_hours)
            cm = {'Simple': 1.0, 'Medium': 1.3, 'Complex': 1.6}
            um = {'Normal': 1.0, 'Urgent': 1.2, 'Very Urgent': 1.5}
            calculated = base * cm.get(complexity, 1.0) * um.get(urgency, 1.0)
            calculated += float(additional_charges)
            calculated += calculated * (float(tax) / 100)
            suggested_price = f"${calculated:.2f}"
        except ValueError:
            flash('Please enter valid numbers.')
            return render_template('create_pricing.html', suggested_price=None)
        prompt = f"""Freelancing pricing expert. Analyze:
- Hourly Rate: ${hourly_rate}/hr
- Hours: {estimated_hours}
- Complexity: {complexity}
- Urgency: {urgency}
- Additional: ${additional_charges}
- Tax: {tax}%
- Calculated Price: {suggested_price}
Give: 1. MARKET ANALYSIS 2. RECOMMENDED DELIVERY TIME 3. SERVICE IMPROVEMENT TIPS. No markdown."""
        try:
            ai_analysis = generate_ai_content(prompt)
        except Exception as e:
            flash(f"AI Error: {str(e)}")
            return render_template('create_pricing.html', suggested_price=suggested_price, ai_analysis=None)
        if action == 'save':
            conn = get_db()
            conn.execute("""INSERT INTO pricing_history (user_id, hourly_rate, estimated_hours, complexity, urgency, additional_charges, tax, suggested_price, ai_analysis)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (session['user_id'], hourly_rate, estimated_hours, complexity, urgency, additional_charges, tax, suggested_price, ai_analysis))
            conn.commit()
            conn.close()
            flash('Pricing saved!')
            return redirect(url_for('pricing'))
        return render_template('create_pricing.html',
            suggested_price=suggested_price, ai_analysis=ai_analysis,
            hourly_rate=hourly_rate, estimated_hours=estimated_hours,
            complexity=complexity, urgency=urgency,
            additional_charges=additional_charges, tax=tax)
    return render_template('create_pricing.html', suggested_price=None)

@app.route('/pricing/delete/<int:pid>')
def delete_pricing(pid):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    conn.execute('DELETE FROM pricing_history WHERE id = ? AND user_id = ?', (pid, session['user_id']))
    conn.commit()
    conn.close()
    flash('Pricing record deleted.')
    return redirect(url_for('pricing'))

# ---------- CLIENT REPLIES ----------
@app.route('/client-replies')
def client_replies():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    all_replies = conn.execute('SELECT * FROM client_replies WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('client_replies.html', replies=all_replies)

@app.route('/client-replies/create', methods=['GET', 'POST'])
def create_reply():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    generated_reply = None
    if request.method == 'POST':
        client_message = request.form['client_message'].strip()
        tone = request.form['tone']
        action = request.form.get('action')
        if not client_message:
            flash('Please enter the client message.')
            return render_template('create_reply.html', generated_reply=None)
        prompt = f"""You are a professional freelancer. Reply to this client message:
"{client_message}"
Tone: {tone}. Professional, respectful, address concern directly. 3-5 sentences. No markdown."""
        try:
            generated_reply = generate_ai_content(prompt)
        except Exception as e:
            flash(f"AI Error: {str(e)}")
            return render_template('create_reply.html', generated_reply=None)
        if action == 'save':
            conn = get_db()
            conn.execute('INSERT INTO client_replies (user_id, client_message, tone, generated_reply) VALUES (?, ?, ?, ?)',
                (session['user_id'], client_message, tone, generated_reply))
            conn.commit()
            conn.close()
            flash('Reply saved!')
            return redirect(url_for('client_replies'))
        return render_template('create_reply.html',
            generated_reply=generated_reply, client_message=client_message, tone=tone)
    return render_template('create_reply.html', generated_reply=None)

@app.route('/client-replies/delete/<int:rid>')
def delete_reply(rid):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    conn.execute('DELETE FROM client_replies WHERE id = ? AND user_id = ?', (rid, session['user_id']))
    conn.commit()
    conn.close()
    flash('Reply deleted.')
    return redirect(url_for('client_replies'))

# ---------- INVOICES ----------
@app.route('/invoices')
def invoices():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    all_invoices = conn.execute('SELECT * FROM invoices WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('invoices.html', invoices=all_invoices)

@app.route('/invoices/create', methods=['GET', 'POST'])
def create_invoice():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        client_name = request.form['client_name'].strip()
        client_email = request.form['client_email'].strip()
        project_title = request.form['project_title'].strip()
        services = request.form['services'].strip()
        amount = request.form['amount']
        tax = request.form.get('tax', '0') or '0'
        due_date = request.form['due_date']
        if not all([client_name, client_email, project_title, services, amount, due_date]):
            flash('Please fill in all required fields.')
            return render_template('create_invoice.html')
        try:
            total = float(amount) + float(amount) * (float(tax) / 100)
            total_amount = f"${total:.2f}"
        except ValueError:
            flash('Please enter valid numbers.')
            return render_template('create_invoice.html')
        conn = get_db()
        conn.execute("""INSERT INTO invoices (user_id, client_name, client_email, project_title, services, amount, tax, total_amount, due_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (session['user_id'], client_name, client_email, project_title, services, amount, tax, total_amount, due_date))
        conn.commit()
        last_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.close()
        flash('Invoice created!')
        return redirect(url_for('export_invoice_pdf', iid=last_id))
    return render_template('create_invoice.html')

@app.route('/invoices/delete/<int:iid>')
def delete_invoice(iid):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    conn.execute('DELETE FROM invoices WHERE id = ? AND user_id = ?', (iid, session['user_id']))
    conn.commit()
    conn.close()
    flash('Invoice deleted.')
    return redirect(url_for('invoices'))

@app.route('/invoices/export/<int:iid>')
def export_invoice_pdf(iid):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    inv = conn.execute('SELECT * FROM invoices WHERE id = ? AND user_id = ?', (iid, session['user_id'])).fetchone()
    conn.close()
    if not inv:
        flash('Invoice not found.')
        return redirect(url_for('invoices'))
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(0, 12, "INVOICE", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Invoice #: INV-{iid:04d}", ln=True)
    pdf.cell(0, 8, f"Date: {inv['created_at'][:10]}", ln=True)
    pdf.cell(0, 8, f"Due Date: {inv['due_date']}", ln=True)
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Bill To:", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, inv['client_name'], ln=True)
    pdf.cell(0, 7, inv['client_email'], ln=True)
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Project:", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, inv['project_title'], ln=True)
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Services:", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 7, inv['services'])
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f"Subtotal: ${inv['amount']}", ln=True)
    pdf.cell(0, 8, f"Tax: {inv['tax']}%", ln=True)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"TOTAL: {inv['total_amount']}", ln=True)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf.output(tmp.name)
    tmp.close()
    return send_file(tmp.name, mimetype='application/pdf', as_attachment=True, download_name=f'invoice_{iid}.pdf')

# ---------- CONTRACTS ----------
@app.route('/contracts')
def contracts():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    all_contracts = conn.execute('SELECT * FROM contracts WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('contracts.html', contracts=all_contracts)

@app.route('/contracts/create', methods=['GET', 'POST'])
def create_contract():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    generated_contract = None
    if request.method == 'POST':
        client_name = request.form['client_name'].strip()
        client_email = request.form['client_email'].strip()
        freelancer_name = request.form['freelancer_name'].strip()
        freelancer_email = request.form['freelancer_email'].strip()
        project_scope = request.form['project_scope'].strip()
        timeline = request.form['timeline'].strip()
        payment_terms = request.form['payment_terms'].strip()
        terms_conditions = request.form['terms_conditions'].strip()
        action = request.form.get('action')
        if not all([client_name, client_email, freelancer_name, freelancer_email, project_scope, timeline, payment_terms]):
            flash('Please fill in all required fields.')
            return render_template('create_contract.html', generated_contract=None)
        prompt = f"""Generate a professional freelance contract:
- Client: {client_name} ({client_email})
- Freelancer: {freelancer_name} ({freelancer_email})
- Project Scope: {project_scope}
- Timeline: {timeline}
- Payment Terms: {payment_terms}
- Terms: {terms_conditions}
Include sections: Parties, Project Scope, Timeline, Payment, Revisions, IP Rights, Termination, T&C, Signatures. No markdown."""
        try:
            generated_contract = generate_ai_content(prompt)
        except Exception as e:
            flash(f"AI Error: {str(e)}")
            return render_template('create_contract.html', generated_contract=None)
        if action == 'save':
            conn = get_db()
            conn.execute("""INSERT INTO contracts (user_id, client_name, client_email, freelancer_name, freelancer_email, project_scope, timeline, payment_terms, terms_conditions, generated_contract)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (session['user_id'], client_name, client_email, freelancer_name, freelancer_email, project_scope, timeline, payment_terms, terms_conditions, generated_contract))
            conn.commit()
            conn.close()
            flash('Contract saved!')
            return redirect(url_for('contracts'))
        return render_template('create_contract.html',
            generated_contract=generated_contract,
            client_name=client_name, client_email=client_email,
            freelancer_name=freelancer_name, freelancer_email=freelancer_email,
            project_scope=project_scope, timeline=timeline,
            payment_terms=payment_terms, terms_conditions=terms_conditions)
    return render_template('create_contract.html', generated_contract=None)

@app.route('/contracts/delete/<int:cid>')
def delete_contract(cid):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    conn.execute('DELETE FROM contracts WHERE id = ? AND user_id = ?', (cid, session['user_id']))
    conn.commit()
    conn.close()
    flash('Contract deleted.')
    return redirect(url_for('contracts'))

@app.route('/contracts/export/<int:cid>')
def export_contract_pdf(cid):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.execute('SELECT * FROM contracts WHERE id = ? AND user_id = ?', (cid, session['user_id'])).fetchone()
    conn.close()
    if not c:
        flash('Contract not found.')
        return redirect(url_for('contracts'))
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "FREELANCE CONTRACT", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Date: {c['created_at'][:10]}", ln=True)
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Parties:", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Client: {c['client_name']} ({c['client_email']})", ln=True)
    pdf.cell(0, 7, f"Freelancer: {c['freelancer_name']} ({c['freelancer_email']})", ln=True)
    pdf.ln(4)
    pdf.multi_cell(0, 7, c['generated_contract'])
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf.output(tmp.name)
    tmp.close()
    return send_file(tmp.name, mimetype='application/pdf', as_attachment=True, download_name=f'contract_{cid}.pdf')

# ---------- RUN ----------

# ---------- RUN ----------
init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)