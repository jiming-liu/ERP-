
import mysql.connector

class Connectmysql:
    def __init__(self):
        self.connect=mysql.connector.connect(
            host='192.168.1.221',
            user='qa',
            password='@test190411^',
            port='3306',
            database='yishou',
            charset='utf8',
            buffered=True)


    def Select(self,sql):
        try:
            # cursor=self.connect.cursor(dictionary=True)
            cursor = self.connect.cursor()

            cursor.execute(sql)

            data=cursor.fetchall()
            self.connect.close()
            print('--查询成功--')
            return data
        except Exception:
            print('查询失败！！')
            self.connect.rollback()

    def Update(self,sql):
        try:
            cursor=self.connect.cursor()

            cursor.execute(sql)
            self.connect.commit()

            self.connect.close()
            print('--修改成功--')
        except Exception:
            print('修改失败！！')
            self.connect.rollback()






# sql_1='select * from fmys_stock_in_record where status=4'
#
# data=Connectmysql().connect(sql_1)
# print(data)