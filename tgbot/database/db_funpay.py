# - *- coding: utf- 8 - *-
import sqlite3

from pydantic import BaseModel

from tgbot.data.config import PATH_DATABASE
from tgbot.database.db_helper import dict_factory, update_format_where, update_format
from tgbot.utils.const_functions import get_unix, ded, gen_id


# Модель таблицы
class FunpayModel(BaseModel):
    increment: int
    position_id: int
    funpay_code: str
    funpay_used: int
    funpay_user_id: int
    funpay_amount: float
    funpay_unix: int


# Работа с FunPay
class Funpayx:
    storage_name = "storage_funpay"

    # Добавление записи
    @staticmethod
    def add(
            position_id: int,
            funpay_amount: float,
    ):
        funpay_code = gen_id(12)
        funpay_used = 0
        funpay_user_id = 0
        funpay_unix = get_unix()

        with sqlite3.connect(PATH_DATABASE) as con:
            con.row_factory = dict_factory

            con.execute(
                ded(f"""
                    INSERT INTO {Funpayx.storage_name} (
                        position_id,
                        funpay_code,
                        funpay_used,
                        funpay_user_id,
                        funpay_amount,
                        funpay_unix
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """),
                [
                    position_id,
                    funpay_code,
                    funpay_used,
                    funpay_user_id,
                    funpay_amount,
                    funpay_unix,
                ],
            )

        return funpay_code

    # Получение записи
    @staticmethod
    def get(**kwargs) -> FunpayModel:
        with sqlite3.connect(PATH_DATABASE) as con:
            con.row_factory = dict_factory
            sql = f"SELECT * FROM {Funpayx.storage_name}"
            sql, parameters = update_format_where(sql, kwargs)

            response = con.execute(sql, parameters).fetchone()

            if response is not None:
                response = FunpayModel(**response)

            return response

    # Получение записей
    @staticmethod
    def gets(**kwargs) -> list[FunpayModel]:
        with sqlite3.connect(PATH_DATABASE) as con:
            con.row_factory = dict_factory
            sql = f"SELECT * FROM {Funpayx.storage_name}"
            sql, parameters = update_format_where(sql, kwargs)

            response = con.execute(sql, parameters).fetchall()

            if len(response) >= 1:
                response = [FunpayModel(**cache_object) for cache_object in response]

            return response

    # Редактирование записи
    @staticmethod
    def update(funpay_code, **kwargs):
        with sqlite3.connect(PATH_DATABASE) as con:
            con.row_factory = dict_factory
            sql = f"UPDATE {Funpayx.storage_name} SET"
            sql, parameters = update_format(sql, kwargs)
            parameters.append(funpay_code)

            con.execute(sql + "WHERE funpay_code = ?", parameters)

    # Удаление записи
    @staticmethod
    def delete(**kwargs):
        with sqlite3.connect(PATH_DATABASE) as con:
            con.row_factory = dict_factory
            sql = f"DELETE FROM {Funpayx.storage_name}"
            sql, parameters = update_format_where(sql, kwargs)

            con.execute(sql, parameters)

    # Очистка всех записей
    @staticmethod
    def clear():
        with sqlite3.connect(PATH_DATABASE) as con:
            con.row_factory = dict_factory
            sql = f"DELETE FROM {Funpayx.storage_name}"

            con.execute(sql)