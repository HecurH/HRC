import hashlib
from fastapi import HTTPException, status, Response, Header
from datetime import datetime
from fastapi.responses import JSONResponse
import json
import re
import secrets
from config import salt


class Tools:
    def __init__(self, db, mail):
        self.db = db
        self.mail = mail

    def authenticate_token(self, token: str):
        token_info = self.db.get_token_info(hash_value(token))
        if not token_info:
            return None
        return token_info

    async def token_required(self, token: str, x_real_ip: str = Header(None, alias='X-Real-IP')):
        token = self.authenticate_token(token)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверные учетные данные"
            )
        user = self.db.get_user(token[1])

        if x_real_ip != token[2]:
            self.db.sql("DELETE FROM tokens WHERE username = %s", (token[1],))
            self.mail.warn(user.get_value('email'), x_real_ip)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return user

    # def need_perms(self, permissions):
    #     def decorator(f):
    #         @wraps(f)
    #         def decorated_function(*args, **kwargs):
    #             token: str = request.authorization.token
    #             token_enc = self.hashing.hash_value(token, salt=salt)
    #             if self.db.get_token_perms(token_enc) in permissions:
    #                 return f(*args, **kwargs)
    #             else:
    #                 return mkjson({"code": 403, "message": "You don't have permission."}), 403, {
    #                     'Content-Type': 'application/json'}
    #
    #         return decorated_function
    #
    #     return decorator


def is_valid_nickname(input_string):
    pattern = re.compile(r'^[a-zA-Zа-яА-Я0-9!@#$%^&*()-_=+{}\[\]:;<>,.?/\\|]*$')

    return bool(pattern.match(input_string))


def is_valid_username(input_string):
    # Регулярное выражение для проверки
    pattern = re.compile(r'^[a-z0-9]*$')

    # Проверка совпадения
    return bool(pattern.match(input_string))


def convert_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime(item) for item in obj]
    else:
        return obj


def response(code, message):
    return JSONResponse(content=convert_datetime(message), status_code=code)


def hash_value(value):
    # Создаем объект хеширования с использованием алгоритма SHA-256
    sha256 = hashlib.sha256()

    # Обновляем хеш объект с байтами пароля и соли
    sha256.update((value + salt).encode('utf-8'))

    return sha256.hexdigest()


def generate_token():
    return secrets.token_urlsafe(64)


def generate_pass():
    return secrets.token_urlsafe(8)


def check_vals(*args) -> bool:
    """
    Проверить значения.
    :return:
    """

    for arg in args:
        if not arg:
            return False
        return True
    return False


me_can_grab = ['nickname', 'avatar', 'description', 'created', 'friends', 'pubkey', 'email', 'friend_requests']
me_can_change = ['nickname', 'avatar', 'description', 'password']
user_can_grab = ['nickname', 'avatar', 'description', 'created', "online"]


def mkjson(smth):
    return json.dumps(smth, indent=2, ensure_ascii=False, default=str)
