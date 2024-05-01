from typing import Annotated

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel

from tools import *
from crypto import generate_keys, encrypt
from db import User
from main import db
from main import mail

api = APIRouter(prefix="/api")
tools = Tools(db, mail)


@api.get("/")
def home():

    return "ONLINE"


@api.get("/login")
def login(username: str, password: str, x_real_ip: str = Header(None, alias='X-Real-IP')):
    user = db.get_user(username)
    if not user:
        return response(401, "Пользователь не найден.")
    if not user.check_password(password):
        return response(401, "Неверный пароль.")

    db.sql("DELETE FROM tokens WHERE username = %s", (username,))


    token = generate_token()
    db.sql("INSERT INTO tokens (token_hash, username, ip, created) VALUES (%s, %s, %s, TO_TIMESTAMP(%s))", (hash_value(token), username, x_real_ip, datetime.utcnow().timestamp(),))
    return response(200, token)






@api.get("/me/{info}")
def me(user: Annotated[User, Depends(tools.token_required)], info: str):
    if info not in me_can_grab:
        return response(400, "Неверное значение.")

    if info == 'friends':
        return response(200, user.get_friends())
    elif info == 'friend_requests':
        return response(200, user.get_requests())
    else:
        return response(200, str(user.get_value(info)))


class UserInfo(BaseModel):
    info: str
    value: str


@api.post("/me/{info}")
def me_change(user: Annotated[User, Depends(tools.token_required)], uinfo: UserInfo):
    if not uinfo.value:
        return response(400, "Не указано на что надо изменить.")
    if uinfo.info not in me_can_change:
        return response(400, "Неверный параметр.")

    if uinfo.info == "password":
        passhash = hash_value(uinfo.value)

        user.set_value('passhash', passhash)
        return response(200, "Изменено.")
    else:
        user.set_value(uinfo.info, uinfo.value)
        return response(200, "Изменено.")


class EncryptData(BaseModel):
    pubkey: str
    data: str


@api.post("/encrypt")
def enc(edata: EncryptData):
    if not check_vals(edata.pubkey, edata.data):
        return response(400, "Не все обязательные поля заполнены.")

    try:
        return response(200, encrypt(edata.pubkey, edata.data).decode())
    except Exception as e:
        return response(500, str(e))


@api.get("/users/{friend}/{info}")
def users(user: Annotated[User, Depends(tools.token_required)], friend: str, info: str):
    if info not in user_can_grab:
        return response(400, "Неверное значение.")

    if not db.check_user(friend):
        return response(404, "Пользователь не найден.")

    if not user.is_friends(friend):
        return response(403, "Пользователь не ваш друг.")

    return response(200, str(db.get_user(friend).get_value(info)))


@api.get("/messages/{friend}")
def messages(user: Annotated[User, Depends(tools.token_required)], friend: str, amount: int, skip: int = 0):
    friend = db.get_user(friend)
    if not amount:
        return response(400, "Поле 'amount' не заполнено.")
    if not friend:
        return response(400, "Пользователь не существует.")
    if not user.is_friends(friend.username):
        return response(400, "Пользователь не ваш друг.")

    return response(200, user.get_messages(friend.username, amount, skip))


class RegisterEntry(BaseModel):
    nickname: str
    username: str
    email: str


@api.post("/register")
def register(user: RegisterEntry):
    if not check_vals(user.nickname, user.username, user.email):
        return response(400, "Не все обязательные поля заполнены.")

    if len(user.username) > 15:
        return response(400, "Длина username превысила 15 символов.")
    elif len(user.nickname) > 15:
        return response(400, "Длипопрона nickname превысила 15 символов.")
    elif not is_valid_nickname(user.nickname):
        return response(400, "Проверьте nickname")
    elif not is_valid_username(user.username):
        return response(400, "Проверьте username")
    elif '@' not in user.email:
        return response(400, "Проверьте почту.")

    if db.check_user(user.username):
        return response(400, "Пользователь уже существует.")
    if db.check_email(user.email):
        return response(400, "Почта уже используется.")

    passwd = generate_pass()
    passhash = hash_value(passwd)

    priv, compub = generate_keys()

    try:
        mail.register(user.email, user.username, passwd, priv)
        db.create_user(user.username, user.nickname, passhash, user.email, compub)
        return response(200, "Пользователь зарегестрирован.")
    except Exception as e:
        return response(500, f"Пользователь не зарегестрирован! - {str(e)}")
