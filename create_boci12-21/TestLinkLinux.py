import paramiko
import pymysql

class StockIn:
    def stockin(self,command):
        # 服务器相关信息,下面输入你个人的用户名、密码、ip等信息
        ip="192.168.1.221"
        port=22
        user="apps"
        password ="sogua@))^"
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # 建立连接
        ssh.connect(ip,port,user,password,timeout = 10)
        #输入linux命令
        execute=command
        stdin,stdout,stderr = ssh.exec_command(execute)
        # 输出命令执行结果
        result = stdout.read()
        # print(result.decode('utf-8'))
        #关闭连接
        ssh.close()

    def connet_sql(self):
        #连接数据库操作
        """
        修改专场时间
        :return:
        """
        conn = pymysql.connect(host='192.168.1.221', port=3306, user='qa', passwd='@test190411^', db='yishou',
                               charset='utf8')

        # 如果使用事务引擎，可以设置自动提交事务，或者在每次操作完成后手动提交事务conn.commit()
        conn.autocommit(1)  # conn.autocommit(True)
        # 使用cursor()方法获取操作游标
        cursor = conn.cursor()
        mysql = 'UPDATE fmys_special SET ' \
                'special_start_time = UNIX_TIMESTAMP(timestampadd(DAY,-1,from_unixtime(special_start_time))),' \
                'special_end_time=UNIX_TIMESTAMP(timestampadd(DAY,-1,from_unixtime(special_end_time))),' \
                'special_period=special_period-1,special_add_time=UNIX_TIMESTAMP(timestampadd(DAY,-1,from_unixtime(special_add_time))),' \
                'special_status=3 ' \
                'where special_id = 116457;'

        count = cursor.execute(mysql)
        result = cursor.fetchall()
        print(result)
        for row in result:
            print(row)
a = StockIn()
a.connet_sql()