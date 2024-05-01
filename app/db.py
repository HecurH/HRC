import secrets
from datetime import datetime, timedelta, timezone
import hashlib
import psycopg2
from psycopg2 import pool
from datetime import datetime

from tools import hash_value


class User:
    """
    Пользователь
    """

    def __init__(self, username: str, db):
        self.username = username
        self.db = db

    def get_value(self, value: str):
        """
        Получить лююой параметр из бд.
        :param value:
        :return:
        """
        result = self.db.sql_get(f"SELECT {value} FROM users WHERE username = %s", (self.username,))
        return result[0][0] if result is not None and result != [] else None

    def get_token(self):
        """
        Получить токен пользователя.
        :return:
        """
        result = self.db.sql_get(f"SELECT token_hash FROM tokens WHERE username = %s", (self.username,))
        return result[0][0] if result is not None and result != [] else None

    def set_value(self, value: str, data: str):
        """
        Изменить лююой параметр в бд.
        :param value:
        :param data:
        :return:
        """
        result = self.db.sql(f"UPDATE users SET {value} = %s WHERE username = %s", (data, self.username,))

    def check_password(self, passwd: str):
        """
        Совпадают ли пароль пользователя и пароль предоставленный?
        :param passwd:
        :return:
        """
        return secrets.compare_digest(self.get_value('passhash'), hash_value(passwd))

    def get_friends(self) -> list:
        """
        Получить друзей пользователя.
        :return:
        """
        friends = set()

        result = self.db.sql_get(
            "SELECT suser FROM friends WHERE fuser = %s UNION SELECT fuser FROM friends WHERE suser = %s",
            (self.username, self.username))

        for user in result:
            friends.add(user[0])

        return list(friends)

    # def verify(self):
    #     """
    #     Подтвердить пользователя.
    #     :return:
    #     """
    #     self.db.sql("UPDATE users SET verified = true WHERE username = %s", (self.username,))

    def is_friends(self, friend):
        """
        Проверить является ли другой пользователь другом.
        :param friend:
        :return:
        """
        result = self.db.sql_get(
            "SELECT 1 FROM friends WHERE (fuser = %s AND suser = %s) OR (fuser = %s AND suser = %s)",
            (self.username, friend, friend, self.username,)
        )
        return True if result != [] else False

    def get_requests(self):
        sql_query = """
        SELECT *
        FROM friend_requests
        WHERE 
        sender = %s
        OR
        recipient = %s
        ORDER BY sended DESC
        """
        return [
            {
                "sender": i[0],
                "recipient": i[1],
                "sended": i[2]
            }
            for i in self.db.sql_get(sql_query, (self.username, self.username,))
        ]

    def get_messages(self, friend, amount, skip):
        sql_query = """
            SELECT 
                id, 
                sender, 
                recipient, 
                CASE WHEN %s = sender THEN senderEnc END, 
                CASE WHEN %s = recipient THEN recipientEnc END, 
                sended 
            FROM messages
            WHERE 
                (sender = %s AND recipient = %s)
                OR
                (sender = %s AND recipient = %s)
            ORDER BY sended DESC
            LIMIT %s
            OFFSET %s;

        """
        return [
            {
                "id": i[0],
                "sender": i[1],
                "recipient": i[2],
                "message": i[3] if i[3] else i[4],
                "sended": i[5].isoformat()
            }
            for i in self.db.sql_get(sql_query, (self.username, self.username, self.username, friend, friend, self.username, amount, skip,))
        ]

    # def send_message(self, recipient: str, senderEnc: str, recipientEnc: str):
    #     sql_query = """
    #     INSERT INTO messages
    #     (sender, recipient, senderEnc, recipientEnc, sended)
    #     VALUES
    #     (%s, %s, %s, %s, %s)
    #     """
    #     self.db.sql(sql_query, (self.username, recipient, senderEnc, recipientEnc, datetime.utcnow().timestamp(),))
    #
    # def online(self):
    #     """
    #     Сделать пользователя онлайн.
    #     """
    #     self.db.sql("UPDATE users SET online = true WHERE username = %s", (self.username,))
    #
    # def offline(self):
    #     """
    #     Сделать пользователя оффлайн.
    #     """
    #     self.db.sql("UPDATE users SET online = false WHERE username = %s", (self.username,))

    def delete(self):
        """
        Удалить пользователя.
        :return:
        """
        self.db.sql("DELETE FROM users WHERE username = %s", (self.username,))


class DB:
    """
    Класс для управления базой данных
    """

    def __init__(self, user, password, name, host="postgres", port=5432):

        self.user = user
        self.name = name
        self.password = password
        self.host = host
        self.port = port

        self.connection_pool = psycopg2.pool.SimpleConnectionPool(1, 50, database=name, user=user, password=password,
                                                                  host=host)

        # conn = psycopg2.connect(database=name, user=user, password=password, host=host)

    def tables_check(self):
        try:
            conn = self.connection_pool.getconn()
            with conn:
                with conn.cursor() as cur:
                    # Проверка наличия таблицы users
                    self.check_and_create_table(cur, 'users', """
                                        CREATE TABLE users
                                        (
                                            nickname text NOT NULL,
                                            username text NOT NULL,
                                            online boolean NOT NULL,
                                            description text,
                                            avatar text,
                                            email text NOT NULL,
                                            passhash text NOT NULL,
                                            pubkey text NOT NULL,
                                            verified boolean NOT NULL,
                                            created timestamp without time zone NOT NULL,
                                            PRIMARY KEY (username)
                                        )
                                    """)

                    # Проверка наличия таблицы messages
                    self.check_and_create_table(cur, 'messages', """
                                        CREATE TABLE messages
                                        (
                                            id bigserial NOT NULL,
                                            sender text NOT NULL,
                                            recipient text NOT NULL,
                                            senderEnc text NOT NULL,
                                            recipientEnc text NOT NULL,
                                            sended timestamp without time zone NOT NULL,
                                            PRIMARY KEY (id)
                                        );
                                    """)

                    # Проверка наличия таблицы friends
                    self.check_and_create_table(cur, 'friends', """
                                        CREATE TABLE friends (
                                            fuser text NOT NULL,
                                            suser text NOT NULL
                                        )
                                    """)

                    # Проверка наличия таблицы friend_requests
                    self.check_and_create_table(cur, 'friend_requests', """
                                        CREATE TABLE friend_requests
                                        (
                                            sender text NOT NULL,
                                            recipient text NOT NULL,
                                            sended timestamp without time zone NOT NULL
                                        );
                                    """)
                    self.check_and_create_table(cur, 'tokens', """
                                        CREATE TABLE tokens
                                        (
                                            token_hash text NOT NULL,
                                            username text NOT NULL,
                                            ip text NOT NULL,
                                            created timestamp without time zone NOT NULL,
                                            PRIMARY KEY (token_hash)
                                        );
                                    """)

        except (psycopg2.Error, Exception) as e:
            print("An error occurred:", e)
        finally:
            # Всегда освобождаем соединение
            self.connection_pool.putconn(conn)

    def check_and_create_table(self, cur, table_name, create_table_query):
        cur.execute(f"""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = '{table_name}'
        """)
        if not cur.fetchone():
            cur.execute(create_table_query)

    def sql(self, sql, params=None):
        try:
            conn = self.connection_pool.getconn()
            with conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)

        except (psycopg2.Error, Exception) as e:
            print("An error occurred:", e)
        finally:
            self.connection_pool.putconn(conn)

    def sql_get(self, sql, params=None):
        try:
            conn = self.connection_pool.getconn()
            with conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    return cur.fetchall()
        except (psycopg2.Error, Exception) as e:
            print("An error occurred:", e)
        finally:
            self.connection_pool.putconn(conn)

    def check_user(self, username):
        return self.sql_get("SELECT EXISTS(SELECT 1 FROM users WHERE username = %s)", (username,))[0][0]

    def check_email(self, email):
        return self.sql_get("SELECT EXISTS(SELECT 1 FROM users WHERE email = %s)", (email,))[0][0]

    def check_verified(self):
        users = self.sql_get("SELECT username, created FROM users WHERE verified = false")
        ts = datetime.utcnow()

        if users:
            for user in users:
                created = user[1]
                if (ts - created) >= timedelta(minutes=30):
                    usr = self.get_user(user[0])
                    usr.delete()

    def check_tokens(self):
        tokens = self.sql_get("SELECT token_hash, created FROM tokens")
        ts = datetime.utcnow()

        if tokens:
            for token in tokens:
                created = token[1]
                if (ts - created) >= timedelta(days=1):
                    self.sql("DELETE FROM tokens WHERE token_hash = %s", (token[0],))

    def create_user(self, username, nickname, pashash, email, pubk):
        self.sql(
            "INSERT INTO users (nickname, username, online, description, avatar, email, passhash, pubkey, verified, created) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, TO_TIMESTAMP(%s))",
            (nickname, username, False, '', '', email, pashash, pubk, False, datetime.utcnow().timestamp(),))

    def get_user(self, username) -> User:
        res = self.sql_get("SELECT username FROM users WHERE username = %s", (username,))

        return User(username, self) if res != [] else None

    def get_token_info(self, token):
        res = self.sql_get("SELECT * FROM tokens WHERE token_hash = %s", (token,))

        return res[0] if res != [] else None
