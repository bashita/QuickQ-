from flask import session, Flask, render_template, request, redirect, url_for, flash, session
import pymysql
from datetime import datetime
import random
import string
import io
import base64
import qrcode
app = Flask(__name__)
app.secret_key = 'quickq'

# --- MySQL connection ---
db= pymysql.connect(
       host="localhost",
       user="root",
       password="mysql",
       database="QuickQ"
)
cursor = db.cursor(pymysql.cursors.DictCursor)

def generate_queue_code():
    """Generate a random 6-character alphanumeric code for the queue."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(6))
def generate_admin_token():
    """Generate a random token for admin authentication."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(20))
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/createQ.html', methods=['GET', 'POST'])
def createQ():
       if request.method == 'POST':
              queue_name = request.form['queue_name']
              queue_code = generate_queue_code()
              admin_token = generate_admin_token()
       
              # Insert into database
              sql = "INSERT INTO Queues (queue_name, queue_code, admin_token) VALUES (%s, %s, %s)"
              cursor.execute(sql, (queue_name, queue_code, admin_token))
              db.commit()
       
              flash('Queue created successfully!', 'success')
              return render_template('Qcreated.html', queue_name=queue_name, queue_code=queue_code, admin_token=admin_token)
       return render_template('createQ.html')

@app.route('/manageQ.html', methods=['GET', 'POST'])
def manage_queue_form():
    if request.method == 'POST':
        admin_token = request.form['admin_token']
        return redirect(url_for('manage_queue', admin_token=admin_token))

    return render_template('manageQ_form.html')

@app.route('/manage/<admin_token>')
def manage_queue(admin_token):

    cursor = db.cursor(pymysql.cursors.DictCursor)

    # Find queue
    cursor.execute("""
        SELECT * FROM queues
        WHERE admin_token = %s
    """, (admin_token,))

    queue = cursor.fetchone()

    if not queue:
        return "Invalid Admin Token"

    queue_id = queue['id']

    # Get all queue members
    cursor.execute("""
        SELECT * FROM queue_members
        WHERE queue_id = %s
        ORDER BY token_number
    """, (queue_id,))

    members = cursor.fetchall()

    # Build a join URL for the QR code and printable link
    join_url = url_for('join_queue', _external=True) + '?queue_code=' + queue['queue_code']
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(join_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    qr_code_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

    # Get current serving member if the queue has a current token
    current_token = queue.get('current_token')
    current_member = None
    if current_token:
        cursor.execute("""SELECT * FROM queue_members WHERE queue_id = %s AND token_number = %s """, (queue_id, current_token))
        current_member = cursor.fetchone()

    cursor.close()

    return render_template('manageQ.html', queue=queue, members=members, current_member=current_member, qr_code_data=qr_code_data, join_url=join_url)

@app.route('/next/<admin_token>')
def next_token(admin_token):

    cursor = db.cursor(pymysql.cursors.DictCursor)

    # Find queue
    cursor.execute("""
        SELECT * FROM queues
        WHERE admin_token = %s
    """, (admin_token,))

    queue = cursor.fetchone()

    if not queue:
        cursor.close()
        return "Invalid Admin Token"

    current_token = queue.get('current_token') or 0

    # Find next member
    cursor.execute("""
        SELECT *
        FROM queue_members
        WHERE queue_id = %s
        AND token_number > %s
        ORDER BY token_number
        LIMIT 1
    """, (
        queue['id'],
        current_token
    ))

    next_member = cursor.fetchone()

    if next_member:

        cursor.execute("""
            UPDATE queues
            SET current_token = %s
            WHERE id = %s
        """, (
            next_member['token_number'],
            queue['id']
        ))

    else:

        # Queue finished
        cursor.execute("""
            UPDATE queues
            SET current_token = NULL
            WHERE id = %s
        """, (
            queue['id'],
        ))

    db.commit()
    cursor.close()
    return redirect(f'/manage/{admin_token}')

@app.route('/joinQ.html', methods=['GET', 'POST'])
def join_queue():

    queue_code = request.args.get('queue_code', '')

    if request.method == 'POST':

        queue_code = request.form['queue_code']
        action = request.form.get('action', 'join')
        nickname = request.form.get('nickname', '').strip()

        cursor = db.cursor(pymysql.cursors.DictCursor)

        # Find queue using queue code
        cursor.execute("""
            SELECT * FROM queues
            WHERE queue_code = %s
            AND is_active = TRUE
        """, (queue_code,))

        queue = cursor.fetchone()

        # Queue not found
        if not queue:

            cursor.close()

            return render_template(
                'joinQ.html',
                error="Queue not found",
                queue_code=queue_code
            )

        # Internal queue ID
        queue_id = queue['id']

        # =========================
        # VIEW STATUS
        # =========================
        if action == 'status':

            # Total members
            cursor.execute("""
                SELECT COUNT(*) AS total_members
                FROM queue_members
                WHERE queue_id = %s
            """, (queue_id,))

            total = cursor.fetchone()['total_members']

            # Current serving member
            cursor.execute("""
                SELECT * FROM queue_members
                WHERE queue_id = %s
                AND token_number = %s
            """, (
                queue_id,
                queue.get('current_token') or 0
            ))

            current_member = cursor.fetchone()

            # Waiting count
            cursor.execute("""
                SELECT COUNT(*) AS waiting_count
                FROM queue_members
                WHERE queue_id = %s
                AND token_number > %s
            """, (
                queue_id,
                queue.get('current_token') or 0
            ))

            waiting = cursor.fetchone()['waiting_count']

            cursor.close()

            return render_template(
                'joinQ.html',
                queue_code=queue_code,
                queue_status={
                    'queue_name': queue['queue_name'],
                    'queue_code': queue['queue_code'],
                    'total_members': total,
                    'waiting_count': waiting,
                    'current_member': current_member,
                    'current_token': queue.get('current_token')
                }
            )

        # =========================
        # JOIN QUEUE
        # =========================
        if action == 'join':

            # Prevent duplicate joins from same browser
            session_key = f"queue_{queue_id}"

            if session.get(session_key):

                cursor.close()

                return render_template(
                    'joinQ.html',
                    error="You already joined this queue",
                    queue_code=queue_code
                )

            # Nickname required
            if not nickname:

                cursor.close()

                return render_template(
                    'joinQ.html',
                    error="Nickname is required to join the queue",
                    queue_code=queue_code
                )

            # Check nickname uniqueness
            cursor.execute("""
                SELECT * FROM queue_members
                WHERE queue_id = %s
                AND LOWER(nickname) = LOWER(%s)
            """, (
                queue_id,
                nickname
            ))

            existing_user = cursor.fetchone()

            if existing_user:

                cursor.close()

                return render_template(
                    'joinQ.html',
                    error="Nickname already taken in this queue",
                    queue_code=queue_code
                )

            # Find highest token
            cursor.execute("""
                SELECT MAX(token_number) AS max_token
                FROM queue_members
                WHERE queue_id = %s
            """, (queue_id,))

            result = cursor.fetchone()

            # Generate token number
            if result['max_token'] is None:
                token_number = 1
            else:
                token_number = result['max_token'] + 1

            # Insert member
            cursor.execute("""
                INSERT INTO queue_members
                (queue_id, token_number, nickname)
                VALUES (%s, %s, %s)
            """, (
                queue_id,
                token_number,
                nickname
            ))

            db.commit()

            # Save browser session
            session[session_key] = True

            # Fetch current serving member
            cursor.execute("""
                SELECT * FROM queue_members
                WHERE queue_id = %s
                AND token_number = %s
            """, (
                queue_id,
                queue['current_token']
            ))

            serving_member = cursor.fetchone()

            cursor.close()

            return render_template(
                'Qjoined.html',
                queue=queue,
                token_number=token_number,
                nickname=nickname,
                serving_member=serving_member
            )

        cursor.close()

        return render_template(
            'joinQ.html',
            queue_code=queue_code
        )

    return render_template(
        'joinQ.html',
        queue_code=queue_code
    )
if __name__ == '__main__':
       app.run(debug=True)