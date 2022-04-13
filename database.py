import psycopg2
from typing import List
from .secrets import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
from leveelogic.objects.crosssection import Crosssection


class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            f"dbname='{DB_NAME}' user='{DB_USER}' password='{DB_PASSWORD}' host='{DB_HOST}' port='{DB_PORT}'"
        )

    def select_one(self, sql):
        cur = self.conn.cursor()
        cur.execute(sql)
        row = cur.fetchone()
        cur.close()
        return row

    def select_all(self, sql):
        cur = self.conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        cur.close()
        return rows

    def execute(self, sql):
        cur = self.conn.cursor()
        try:
            cur.execute(sql)
            self.conn.commit()
            cur.close()
        except Exception as e:
            print(e)
            return False

        return True

    def update_crosssection(self, crosssection_id: int, crosssection: Crosssection):
        sql = f"UPDATE crosssections SET raw='{crosssection.to_short_string()}' WHERE id={crosssection_id}"
        print(sql)
        self.execute(sql)

    def get_crosssection_by_id(self, crosssection_id: int) -> Crosssection:
        row = self.select_one(f"SELECT raw FROM crosssections WHERE id={crosssection_id}")        
        crs = Crosssection.from_short_string(row[0])
        print(crs)
        return crs


