from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import jwt, time, hmac, hashlib, os

app = Flask(__name__)
# ── Config ─────────────────────────────────────────────────────────────────
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@db:5432/licenses'
app.config['JWT_PRIVATE_KEY'] = open('keys/private.pem').read()
app.config['JWT_PUBLIC_KEY'] = open('keys/public.pem').read()
app.config['HMAC_SECRET'] = os.environ['HMAC_SECRET']
db = SQLAlchemy(app)
limiter = Limiter(app, key_func=get_remote_address, default_limits=['100/day','10/minute'])

# ── Models ─────────────────────────────────────────────────────────────────
class HWID(db.Model): hwid = db.Column(db.Text, primary_key=True)
class Nonce(db.Model):
    nonce = db.Column(db.Text, primary_key=True)
    hwid = db.Column(db.Text, db.ForeignKey('hwid.hwid'))
    ts = db.Column(db.BigInteger);
    used = db.Column(db.Boolean, default=False)

# ── License Endpoint ──────────────────────────────────────────────────────
@app.route('/api/v1/license', methods=['POST'])
@limiter.limit('5/minute')
def license():
    data = request.get_json() or {}
    hwid, ts, nonce, sig = data.get('hwid'), data.get('ts'), data.get('nonce'), data.get('sig')

    # 1) Validate HMAC
    expected = hmac.new(app.config['HMAC_SECRET'].encode(), msg=json.dumps({k:data[k] for k in ['hwid','ts','nonce']}).encode(),digestmod=hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return jsonify({'error':'Invalid signature'}), 400

    # 2) Check timestamp skew (±5 minutes)
    now = int(time.time())
    if abs(now - ts) > 300:
        return jsonify({'error':'Timestamp out of range'}), 400

    # 3) Prevent replay
    if Nonce.query.get(nonce) or HWID.query.get(hwid) is None:
        return jsonify({'error':'Invalid or reused nonce/HWID'}), 403

    # 4) Mark nonce
    db.session.add(Nonce(nonce=nonce, hwid=hwid, ts=ts, used=True))
    db.session.commit()

    # 5) Issue JWT
    payload = {'hwid':hwid, 'iat':now, 'nbf':now, 'exp':now + 86400}
    token = jwt.encode(payload, app.config['JWT_PRIVATE_KEY'], algorithm='RS256')
    return jsonify({'token':token})

if __name__=='__main__':
    app.run(host='0.0.0.0', port=5000)
