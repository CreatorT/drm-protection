import uuid, platform, os, sys, json, time
import hashlib, hmac, requests, jwt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ── Configuration ──────────────────────────────────────────────────────────
LICENSE_URL = 'https://licenses.example.com/api/v1/license'
PUBLIC_KEY = '''-----BEGIN PUBLIC KEY-----
...RSA PUBLIC KEY...
-----END PUBLIC KEY-----'''
CACHE_PATH = 'cache.bin'; CACHE_KEY = b'my_32_byte_aes_key_1234567890'
CLIENT_SECRET = b'client_shared_hmac_secret'

# ── Hardware ID Assembly ─────────────────────────────────────────────────
def get_hardware_id():
    mac = uuid.getnode()
    disk = platform.node()  # placeholder for real disk UUID
    cpu = platform.processor()
    raw = f"{mac}|{disk}|{cpu}|MY_SALT"
    return hashlib.sha256(raw.encode()).hexdigest()

# ── Secure Cache ───────────────────────────────────────────────────────────
def save_token(token):
    aes = AESGCM(CACHE_KEY)
    nonce = os.urandom(12)
    data = aes.encrypt(nonce, token.encode(), None)
    with open(CACHE_PATH, 'wb') as f:
        f.write(nonce + data)

def load_token():
    if not os.path.exists(CACHE_PATH): return None
    try:
        with open(CACHE_PATH,'rb') as f:
            buf = f.read()
        aes = AESGCM(CACHE_KEY)
        token = aes.decrypt(buf[:12], buf[12:], None)
        return token.decode()
    except Exception:
        return None

# ── License Verification ──────────────────────────────────────────────────
def verify_license():
    # 1) Check cache
    token = load_token()
    if token:
        try:
            decoded = jwt.decode(token, PUBLIC_KEY, algorithms=['RS256'])
            if decoded['hwid'] == get_hardware_id() and decoded['exp'] > time.time():
                return True
        except jwt.PyJWTError:
            pass

    # 2) Request new license
    hwid = get_hardware_id()
    ts = int(time.time()); nonce = os.urandom(8).hex()
    payload = { 'hwid': hwid, 'ts': ts, 'nonce': nonce }
    sig = hmac.new(CLIENT_SECRET, json.dumps(payload).encode(), hashlib.sha256).hexdigest()
    try:
        r = requests.post(LICENSE_URL, json={**payload,'sig':sig}, timeout=5)
        r.raise_for_status()
        token = r.json().get('token','')
        save_token(token)
        return True
    except Exception:
        return False

if __name__ == '__main__':
    if not verify_license():
        print('Unauthorized. Exiting.'); sys.exit(1)
    # --- Protected application entry point ---
    print('License valid. Launching app...')
