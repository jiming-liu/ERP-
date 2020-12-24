#coding=utf-8
from ConnectMySQL import Connectmysql


class SendSQL():
    def Get_order_data(self,*order_sn):
        # 通过订单号查询下单信息#
        if len(order_sn)==1:
            sql = 'SELECT gl.supply_id,oi.user_id,oi.goods_no,oi.sku,gs.co_val,gs.si_val,oi.buy_num,oi.origin ' \
                  'FROM fmys_order_infos oi ' \
                  'JOIN fmys_goods_sku gs ' \
                  'ON oi.goods_no=gs.goods_no ' \
                  'AND oi.co_id=gs.co_id ' \
                  'AND oi.si_id=gs.si_id ' \
                  'JOIN fmys_order o ' \
                  'ON o.order_id=oi.order_id ' \
                  'JOIN fmys_goods_lib gl '\
                  'ON oi.goods_no = gl.goods_no '\
                  'WHERE order_sn = ' + str(order_sn[0])
        else:
            sql='SELECT gl.supply_id,oi.user_id,oi.goods_no,oi.sku,gs.co_val,gs.si_val,oi.buy_num,oi.origin  ' \
                'FROM fmys_order_infos oi ' \
                'JOIN fmys_goods_sku gs ' \
                'ON oi.goods_no=gs.goods_no ' \
                'AND oi.co_id=gs.co_id ' \
                'AND oi.si_id=gs.si_id ' \
                'JOIN fmys_order o ' \
                'ON o.order_id=oi.order_id ' \
                'JOIN fmys_goods_lib gl ' \
                'ON oi.goods_no = gl.goods_no ' \
                'WHERE order_sn in '+ str(order_sn)

        data = Connectmysql().Select(sql)

        GZ_goods_list = []
        HZ_goods_list = []
        list_header = ['supply_id','user_id', 'goods_no', 'sku', 'co_val', 'si_val', 'buy_num', 'origin']
        if data is not None:
            for tuple_value in data:
                value = list(tuple_value)
                if value[-1] == 1:
                    GZ_goods_list.append(dict(zip(list_header, value)))
                else:
                    HZ_goods_list.append(dict(zip(list_header, value)))

        return GZ_goods_list,HZ_goods_list

    def Get_special_id(self,*order_sn):
        # 通过订单号单独查询专场ID#
        if len(order_sn)==1:
            sql = 'SELECT DISTINCT oi.special_id ' \
                  'FROM fmys_order_infos oi ' \
                  'JOIN fmys_order o ' \
                  'ON oi.order_id=o.order_id ' \
                  'WHERE o.order_sn = ' + str(order_sn[0])
        else:
            sql='SELECT DISTINCT oi.special_id ' \
                'FROM fmys_order_infos oi ' \
                'JOIN fmys_order o ' \
                'ON oi.order_id=o.order_id ' \
                'WHERE o.order_sn in ' + str(order_sn)

        ID_list=[]
        ID=Connectmysql().Select(sql)
        # print(ID)

        if len(ID)==1:
            return ID[0]
        else:
            for i in range(len(ID)):
                ID_list.append(ID[i][0])
            return tuple(ID_list)

    def Revise_order(self,*order_sn):
        # 更新订单时间到前一天#
        if len(order_sn)==1:
            sql_1 = 'UPDATE fmys_order ' \
                    'SET add_time = UNIX_TIMESTAMP(timestampadd(day, -1, from_unixtime(add_time)))' \
                    'WHERE order_sn = ' + str(order_sn[0])
        else:
            sql_1='UPDATE fmys_order '\
                  'SET add_time = UNIX_TIMESTAMP(timestampadd(day, -1, from_unixtime(add_time)))'\
                  'WHERE order_sn in ' + str(order_sn)

        Connectmysql().Update(sql_1)

    def Revise_special(self,special_id):
        # 更新专场商品状态为已结束#
        if len(special_id)==1:
            sql_2 = 'UPDATE fmys_goods ' \
                    'SET special_status =3 ' \
                    'WHERE special_id = ' + str(special_id[0])

            Connectmysql().Update(sql_2)

            # 更新专场时间到前一天且状态为已结束#
            sql_3 = 'UPDATE fmys_special ' \
                    'SET special_status=3,special_period=special_period-1, ' \
                    'special_start_time = UNIX_TIMESTAMP(timestampadd(DAY,- 1,from_unixtime(special_start_time))), ' \
                    'special_end_time = UNIX_TIMESTAMP(timestampadd(DAY,- 1,from_unixtime(special_end_time))) ' \
                    'WHERE special_id = ' + str(special_id[0])

            Connectmysql().Update(sql_3)
        else:
            sql_2='UPDATE fmys_goods '\
                  'SET special_status =3 '\
                  'WHERE special_id in '+ str(special_id)

            Connectmysql().Update(sql_2)

            # 更新专场时间到前一天且状态为已结束#
            sql_3='UPDATE fmys_special '\
                  'SET special_status=3,special_period=special_period-1, ' \
                  'special_start_time = UNIX_TIMESTAMP(timestampadd(DAY,- 1,from_unixtime(special_start_time))), '\
                  'special_end_time = UNIX_TIMESTAMP(timestampadd(DAY,- 1,from_unixtime(special_end_time))) '\
                  'WHERE special_id in '+ str(special_id)

            Connectmysql().Update(sql_3)

# a=SendSQL().Get_special_id(12025715353003, 12032715352657)
# print(a)
# # SendSQL().Revise_order(12025715353003)
# SendSQL().Revise_special(a)
# b,c=SendSQL().Get_order_data(12025715353003, 12041615352864)
# print(b)
# print(c)