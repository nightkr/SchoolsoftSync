from flask.ext.sqlalchemy import SQLAlchemy
from Crypto.Cipher import AES
from Crypto.Hash import SHA256

db = SQLAlchemy()


class StoredCredential(db.Model):
    __tablename__ = "stored_credentials"

    school = db.Column('school', db.String(100), primary_key=True, nullable=False)
    username = db.Column('username', db.String(100), primary_key=True, nullable=False)
    encrypted_password = db.Column('encrypted_password', db.LargeBinary(255), nullable=False)
    # CBC-mode AES-encrypted with the SHA256 hash of school:username:password as key

    @staticmethod
    def _encrypted_password_mode():
        return AES.MODE_CBC

    @staticmethod
    def _verification_str():
        return "1234567890abcdef"

    def get_password_crypto_key(self, password, school=None, username=None):
        "Get the hashed password encryption key, school and username default to self.*"

        if school is None:
            school = self.school
        if username is None:
            username = self.username
        raw = "%s:%s:%s" % (school, username, password)
        return SHA256.new(raw).digest()

    def decrypt_password(self, hash):
        try:
            cipher = AES.new(hash, self._encrypted_password_mode(), " " * 16)
            decrypted = cipher.decrypt(self.encrypted_password).strip().decode("UTF-8")
        except Exception:  # Invalid value
            return

        if decrypted[:len(self._verification_str())] == self._verification_str():
            return decrypted[len(self._verification_str()):]

    def encrypt_password(self, password, school=None, username=None):
        if school is None:
            school = self.school
        if username is None:
            username = self.username

        password = password.encode("UTF-8")

        crypt_val = self._verification_str() + password
        crypt_val += ' ' * (AES.block_size - len(crypt_val) % AES.block_size)

        key = self.get_password_crypto_key(password, school, username)
        cipher = AES.new(key, self._encrypted_password_mode(), " " * 16)
        return key, cipher.encrypt(crypt_val)
