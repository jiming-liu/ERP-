# coding=utf-8
import json
import hashlib
import sys
import time
from urllib import parse
import urllib.parse
import requests
import pytest
import datetime
import time
import urllib.parse
import urllib.parse
from urllib import parse
from random import choice
import os

import TestLinkLinux
from ExecuteSQL import SendSQL

path = os.path.dirname(os.path.dirname(__file__))
sys.path.append(path)
"""
V1.0脚本思路：
通过订单号-->调用os订单列表-->获取到对应的下单数量，SKU，货号-->创建已支付采购订单-
->生成越库波次-->对越库波次进行汇集-->校验波次-->生成待出库波次

造数据步骤前提条件（必须满足）：
1.商城下单并更改专场时间及订单时间为前一天（与之前保持一致）
2.在ERP仓库基本配置--点货分离配置中导入越库追加配置csv文件（将用户ID导入）
3.确认是否有中分位可用，如无法确认最好新建一个

脚本运行：
1.先修改自己的配置（将账号密码改为自己的），在初始化配置中更改self.name,self.password
2.执行脚本输入订单号-->等待脚本执行完毕（如有报错信息发群里或私聊）

未生成越库波次原因有：
1.用户是否加入越库用户列表
2.商品是否存在非越库波次
3.是否有可用的越库中分位


V1.2更新说明：
1.解决生成欠货，上架任务耗时较长问题（通过跑脚本方式实现）
2.OS订单查询中广杭不同商品取值问题
3.新增连接数据库，自动更新订单时间，专场结束时间
4.解决获取仓位中没有区分广杭问题及同仓位被占用问题
5.解决同一订单中包含广杭两仓商品问题
6.解决供应商交易方式为先货后款问题
7.新增越库分离处理机制
8.解决波次有备注无法锁定问题

V1.3更新说明
1.封装部分代码
2.加入了日志记录
3.新增用户查询
4.新增质检分离处理机制
5.新增改标分离处理机制
6.解决波次有备注无法锁定问题

同一订单中存在多个供应商商品

"""



class sestApi(object):

    pici_no = None
    resgoods = None
    goods_no = None
    sku = None

    def __init__(self):
        """
        初始化数据
        :return:
        """
        self.login_url = "http://erp1.yishou.com/erp/Admin/login"  # 登录接口
        self.order_info_url = "http://test2.yishou.com/os/order/orderDetail"  # 查询订单详情接口
        self.check_orders_url = "http://erp1.yishou.com/erp/wcgPlan/getInfo"  # 进入需审核的采购订单
        self.updata_check_url = "http://erp1.yishou.com/erp/wcgPlan/updateCheck"  # 更新审核状态
        self.supply_list_url = "http://erp1.yishou.com/erp/WcgPlan/waitConfirmSupplyList"  # 查询当前供应商采购核单列表
        self.purchase_url = "http://erp1.yishou.com/buyer/purchase/goodsDetailOfVerifyPurchase"  # 进入采购核单详情页面
        self.edit_purchase_url = "http://erp1.yishou.com/buyer/purchase/editOfVerifyPurchase"  # 提交开单操作
        self.orders_list_url = "http://erp1.yishou.com/erp/WcgOrder/list2"  # 查询已垫付采购订单审核列表
        self.get_order_info_url = "http://erp1.yishou.com/erp/WcgOrder/getOrderInfo"  # 进入采购订单详情进行审核
        self.check_orderinfo_url = "http://erp8.yishou.com/erp/WcgOrder/checkRepeat"  # 采购订单审核提交接口
        self.check_orderinfo_Prepay_url = "http://erp8.yishou.com/erp/WcgOrder/checkOrderPrepay"  # 采购订单审核接口
        self.create_pici_url = "http://erp8.yishou.com/erp/Tally2/createPici"  # 创建批次进行点货
        self.slet_goods_no_url = "http://erp1.yishou.com/erp/TakeStock/getTakeStockGoodsList"  # 查询当前供应商下可点货数据
        self.close_box_url = "http://erp1.yishou.com/erp/TakeStock/closeBox"  # 关闭容器
        self.get_dh_list_url = "http://erp8.yishou.com/erp/pici/getlist"  # 查询点货单列表
        self.select_goods_url = "http://erp8.yishou.com/erp/Common/selectSPUGoodsLib"  # 查询采购订单可选商品
        self.save_goods_url = "http://erp8.yishou.com/erp/WcgOrder/saveUnplannOrder"  # 手动创建采购订单
        self.emptyboxurl = 'http://erp1.yishou.com/erp/box/index'  # 获取容器号接口
        self.upshelf_url = "http://erp1.yishou.com/erp/Upshelf/getList"  # 获取上架任务列表
        self.detail_url = 'http://erp1.yishou.com/erp/Upshelf/detail'  # 进入上架单详情
        self.binddesknourl = "http://erp1.yishou.com/erp/TakeStock/bindDeskNo"  # 绑定工作台
        self.binfboxnourl = "http://erp1.yishou.com/erp/TakeStock/bindBoxNo"  # 绑定容器号
        self.select_pgid_url = "http://erp4.yishou.com/erp/PurchaseGroup/getList"  # 查询采购组ID
        self.getgoodsinfo = "http://erp1.yishou.com/erp/TakeStock/getTakeStockGoodsInfo"  # 根据款号进入点货详情
        self.nomraldabiaourl = "http://erp1.yishou.com/erp/TakeStock/nomralTakeStock"  # 打标操作
        self.dianhuo_url = "http://erp1.yishou.com/erp/pici/getlist"  # 获取点货单数据
        self.get_order_sn = "http://test2.yishou.com/os/order/orderList"  # 查询订单接口
        self.select_pici_url = "http://erp1.yishou.com/erp/WavePicking/getWavePickingList"  # 波次查询接口
        self.check_url = "http://erp5.yishou.com/storage/WavePicking/check"  # 校验打标ID
        self.zhongfen_url = "http://erp1.yishou.com/erp/SurpassSummary/surpassSummaryList"  # 查询中分任务
        self.zhongfen_info_url = "http://erp1.yishou.com/erp/SurpassSummary/confirmAssembleDiff"  # 查询中分任务详情
        self.get_jiaoyan_url = "http://erp1.yishou.com/storage/WavePicking/getWavePickingGoods"  # 获取波次信息接口
        self.get_kuaidi_url = "http://erp1.yishou.com/storage/WavePicking/getWayBill"  # 获取快递信息接口
        self.YueKu_imgurl = 'http://cdn-cloudprint.cainiao.com/waybill-print/cloudprint-imgs/9ab62bf1544248e9a99a36f995b6a733.png'  # 是否越库标凭证
        self.space_url = 'http://erp1.yishou.com/erp/ShippingSpace/spaceList'  # 获取控仓位
        self.select_shangjia_url = "http://erp8.yishou.com/erp/Upshelf/getList"#获取未领取的上架单
        self.select_shangjiainfo_url = "http://erp6.yishou.com/erp/Upshelf/detail"#获取上架单明细数据
        self.get_box_url = "http://erp5.yishou.com/suzaku/UpShelf/receive"#领取上架任务
        self.get_box_url1 = "http://erp7.yishou.com/suzaku/UpShelf/upSku"#上架操作
        self.get_bangdrq_url = "http://erp5.yishou.com/suzaku/UpShelf/getUpshelfOnScan"#扫容器号
        self.lock_pici_url = "http://erp5.yishou.com/erp/WavePicking/lockWavePicking"  # 锁定批次
        self.generate_url = "http://erp5.yishou.com/erp/PickingAssignment/generatePickingAssignment"  # 生成拣货任务
        self.select_generate_url = "http://erp5.yishou.com/erp/PickingAssignment/pickingAssignmentList"  # 查询拣货任务列表
        self.pda_jh_url = "http://erp6.yishou.com/suzaku/Picking/receive"#领取拣货任务
        self.pda_jhinfo_url = "http://erp6.yishou.com/suzaku/Picking/picking"#拣货操作扫描打标ID
        self.pda_tjjhinfo_url = "http://erp6.yishou.com/suzaku/Picking/sub"#提交拣货操作
        self.cangwei_url = "http://erp8.yishou.com/erp/AdminSetting/stockDetailSeparateSetting"  # 获取点货库存分离配置
        self.header_login = {}
        self.name = "刘继明"  # 需配置成自己的账户密码
        self.password = '123456'# 需配置成自己的账户密码
        self.box_no = ""
        self.deskno = 'GZGZT123'
        self.is_numble = 0#默认为0则表示非越库标
        self.pgname = ""
        self.order_sn = ""
        self.pgid = ""
        self.supply_id = ""
        self.goods_on_list = []
        self.goods_ary = []
        self.sku_list = []
        self.qrCode = []
        self.token = ""
        self.boci_id = ""
        self.us_no = ""
        self.order_id = ""
        self.today = datetime.date.today()
        self.tomorrow = self.today + datetime.timedelta(days=1)



    def test_login(self):
        m = hashlib.md5()
        m.update(self.password.encode(encoding="utf-8"))
        en_password = m.hexdigest()
        data = {'name': self.name,
                'password': en_password,
                'login_type': 'backend',
                'phone': '',
                'phoneCode': '',
                'returnUrl': '',
                'is_pc': '1'}
        res = requests.post(url=self.login_url, headers=self.header_login, data=data).json()
        print("开始执行脚本...")
        # 将请求头中的username进行编码，构造请求头中cookie数据
        New_name = urllib.parse.quote(self.name)
        self.token = res['data']['token']
        self.header_login['Cookie'] = "YISHOUSESS=" + res['data']['token'] + ";" + "token=" + res['data'][
            'token'] + ";" + "username=" + New_name

    def select_order_info(self, order_sn):
        self.order_sn = order_sn
        #修改专场及订单时间
        special_id=SendSQL().Get_special_id(order_sn)
        SendSQL().Revise_special(special_id)
        SendSQL().Revise_order(order_sn)
        GZ_goods_data,HZ_goods_data= SendSQL().Get_order_data(order_sn)
        if GZ_goods_data is not None:
            self.goods_ary = GZ_goods_data
            # print(GZ_goods_data)
        else:
            print('没有广州商品，杭州商品暂不支持,脚本中断')



    # def select_order_info(self, order_sn):
    #     """
    #     通过订单号去os订单列表查找下单数量及sku，货号
    #     """
    #     self.order_sn = order_sn
    #     data = {
    #         "select_type": "order_sn",
    #         "select_type_value": order_sn
    #     }
    #     try:
    #         # 根据订单号查询订单列表，获取订单ID
    #         response1 = requests.post(url=self.get_order_sn, headers=self.header_login, data=data).json()
    #         self.order_id = response1["data"]["list"][0]["order_id"]
    #         data_1 = {
    #             "order_id": self.order_id
    #         }
    #         # 根据订单ID查询订单明细，获取该订单所有的下单数量，货号，SKU等
    #         res1 = requests.post(url=self.order_info_url, headers=self.header_login, data=data_1).json()
    #         # if res1["data"]["order_data"]["infos"]["1"] != None:#广州在这应该取1，杭州则取2
    #         if res1["data"]["order_data"]["infos"]["1"] != None:
    #             for i in range(len(res1["data"]["order_data"]["infos"]["1"])):
    #                 self.goods_on_list.append(int(res1["data"]["order_data"]["infos"]["1"][i]["goods_no"]))
    #                 for a in range(len(res1["data"]["order_data"]["infos"]["1"][i]["detail"])):
    #                     val_dict = {}
    #                     val_dict["goods_no"] = res1["data"]["order_data"]["infos"]["1"][i]["detail"][a]["goods_no"]
    #                     val_dict["goods_name"] = res1["data"]["order_data"]["infos"]["1"][i]["detail"][a]["goods_name"]
    #                     val_dict["buy_num"] = res1["data"]["order_data"]["infos"]["1"][i]["detail"][a]["buy_num"]
    #                     val_dict["co_val"] = res1["data"]["order_data"]["infos"]["1"][i]["detail"][a]["co_val"]
    #                     val_dict["si_val"] = res1["data"]["order_data"]["infos"]["1"][i]["detail"][a]["si_val"]
    #                     val_dict["sku"] = res1["data"]["order_data"]["infos"]["1"][i]["detail"][a]["sku"]
    #                     self.supply_id = eval(res1["data"]["order_data"]["infos"]["1"][i]["detail"][a]["sa"])[
    #                         "goodstallID"]
    #                     self.goods_ary.append(val_dict)
    #             print("获取订单明细数据成功...脚本继续执行")
    #         #
    #         print(self.goods_on_list)
    #         print(self.goods_ary)
    #         exit()
    #         # if res1["data"]["order_data"]["infos"]["2"] != None:
    #         #     for i in range(len(res1["data"]["order_data"]["infos"]["2"])):
    #         #         self.goods_on_list.append(int(res1["data"]["order_data"]["infos"]["2"][i]["goods_no"]))
    #         #         for a in range(len(res1["data"]["order_data"]["infos"]["2"][i]["detail"])):
    #         #             val_dict = {}
    #         #             val_dict["goods_no"] = res1["data"]["order_data"]["infos"]["2"][i]["detail"][a]["goods_no"]
    #         #             val_dict["goods_name"] = res1["data"]["order_data"]["infos"]["2"][i]["detail"][a]["goods_name"]
    #         #             val_dict["buy_num"] = res1["data"]["order_data"]["infos"]["2"][i]["detail"][a]["buy_num"]
    #         #             val_dict["co_val"] = res1["data"]["order_data"]["infos"]["2"][i]["detail"][a]["co_val"]
    #         #             val_dict["si_val"] = res1["data"]["order_data"]["infos"]["2"][i]["detail"][a]["si_val"]
    #         #             val_dict["sku"] = res1["data"]["order_data"]["infos"]["2"][i]["detail"][a]["sku"]
    #         #             self.supply_id = eval(res1["data"]["order_data"]["infos"]["2"][i]["detail"][a]["sa"])[
    #         #                 "goodstallID"]
    #         #             self.goods_ary.append(val_dict)
    #         #     print("获取订单明细数据成功...脚本继续执行")
    #     #     else:
    #     #         print("获取订单明细数据失败，请检查...")
    #     except BaseException:
    #         print("获取订单明细数据报错：%s" % res1)

    def test_goods_Purchase(self):
        """
        手动创建采购订单,生成已垫付采购订单
        """
        try:
            for i in range(len(self.goods_ary)):
                    data_2 = {
                        "goods_no": self.goods_ary[i]['goods_no'],
                        "supply_id": self.goods_ary[i]['supply_id']
                    }
                    # 查询所需商品信息
                    res2 = requests.post(url=self.select_goods_url, headers=self.header_login, data=data_2).json()
                    price = res2["data"]["data"][0]["market_price"]
                    data_3 = {
                        "supply_id":self.goods_ary[i]['supply_id'],
                        "woid": 0,
                        "cg_type": 2,
                        "prepay_people": "wa",
                        "docs_ary[0]": "http://img1.yishouapp.com/oss/202006/17/15923829905ee9d60e3d7d4.JPG",
                        "pay_ary[0]": "http://img1.yishouapp.com/oss/202006/17/15923829925ee9d6107f9ed.JPG",
                        "goods_ary[0][goods_no]": self.goods_ary[i]["goods_no"],
                        "goods_ary[0][co_val]": self.goods_ary[i]["co_val"],
                        "goods_ary[0][si_val]": self.goods_ary[i]["si_val"],
                        "goods_ary[0][price]": price,
                        "goods_ary[0][num]": self.goods_ary[i]["buy_num"],
                    }
                    # print(data_3)
                    res8 = requests.post(url=dt.save_goods_url, headers=dt.header_login, data=data_3).json()
                    # print(res8)
                    if res8.get("code") == 200:
                        print("创建已垫付采购订单成功,脚本继续执行...")
        except BaseException:
            print("创建已垫付采购订单报错：%s" % res8)

    def check_order_info(self):
        """
        查询采购订单列表，进行审核操作
        """
        try:
            time_data = {
                "create_time[0]": self.today.strftime("%Y-%m-%d"),
                "create_time[1]": self.tomorrow.strftime("%Y-%m-%d"),
                "status": 0
            }
            res10 = requests.post(url=self.orders_list_url, headers=self.header_login, data=time_data).json()
            for i in range(len(res10["data"]["list"])):
                self.pgname = res10.get("data").get("list")[i]['pgname']
                data_1 = {
                    "woid": int(res10.get("data").get("list")[i]['woid'])
                }
                # 更新审核状态
                res4 = requests.post(url=dt.check_orderinfo_Prepay_url, headers=dt.header_login, data=data_1).json()
                if res4.get("code") == 200:
                    print("采购订单审核成功,脚本继续执行...")
        except BaseException:
            print("采购订单审核报错：%s" % res4)

    def test_achieve_box_no(self):
        """获取未使用的容器号"""
        try:
            box_data = {
                'status': 2
            }
            response = requests.post(url=self.emptyboxurl, data=box_data, headers=self.header_login).json()
            self.box_no = response['data']['list'][0]['box_no']
            # print(self.box_no)
        except BaseException:
            print("获取容器号报错：%s" % response)

    def test_bind_deskno(self):
        """绑定工作台"""
        try:
            box_data = {
                'desk_no': self.deskno,
            }
            response = requests.post(url=self.binddesknourl, data=box_data, headers=self.header_login).json()
        except BaseException:
            print("绑定工作台报错：%s" % response)

    def test_bind_box_no(self):
        """绑定容器操作"""
        try:
            box_data = {
                'box_no': self.box_no,
                "bind_type": "normal"
            }
            response = requests.post(url=self.binfboxnourl, data=box_data, headers=self.header_login).json()
        except BaseException:
            print("绑定容器报错：%s" % response)

    def test_select_supply_info(self):
        """
        查询当前供应商下所有可点货数据
        """
        try:
            pgid_date = {
                "pgname": self.pgname
            }
            res5 = requests.post(url=self.select_pgid_url, data=pgid_date, headers=self.header_login).json()
            self.pgid = res5["data"]["data"][0]["pgid"]
            supply_data = {
                "supply_id": self.supply_id,
                "pgid": self.pgid,
            }
            # 查询当前供应商下所有的点货数据，目前好像对脚本没起多大作用，先保留
            resgoods = requests.post(url=self.slet_goods_no_url, data=supply_data, headers=self.header_login).json()
        except BaseException:
            print("查询可点货数据报错：%s" % resgoods)

    def test_dh_info(self):
        """
        根据商品号点击进入商品详情页获取数据并返回SKU
        """
        try:
            for i in range(len(self.goods_ary)):
                dh_data = {
                    "goods_no": self.goods_ary[i]['goods_no'],
                    "pgid": self.pgid,
                    "supply_id": self.goods_ary[i]['supply_id']
                }

                # 根据货号进入详情点货页面
                response = requests.post(url=self.getgoodsinfo, data=dh_data, headers=self.header_login).json()
                #因耗时较长，这里提前跑生成欠货脚本
                qianhuoid = '/apps/lib/php-7.0.28/bin/php /apps/dat/www/erp5.yishou.com/think task:InsertWcgOweRecordExt'
                TestLinkLinux.StockIn().stockin(qianhuoid)
                print("生成欠货脚本运行成功，脚本继续...")
                # 循环请求查询该供应商下可点货数据，没有则一直等待，直到有为止
                while response["code"] != 200:
                    print("未生成欠货货信息，请等待...")
                    time.sleep(2)
                    response = requests.post(url=self.getgoodsinfo, data=dh_data, headers=self.header_login).json()

                else:
                    # 获取该货号下所有的sku并存入列表
                    for i in range(len(response['data']['detail'])):
                        sku = response['data']['detail'][i]['sku']

                        self.sku_list.append(sku)

            self.sku_list = list(set(self.sku_list))
            # print(self.sku_list)
        except BaseException:
            print("进入商品详情页数据报错：%s" % response)

    def test_create_db_info(self):
        """
        生成打标任务,并返回打标ID
        """
        try:
            # for i in self.goods_ary:
            #     data = {
            #         "supply_id": self.supply_id,
            #         "pgid": self.pgid,
            #         "sku": i["sku"],
            #         "dh_num": i["buy_num"]
            #     }
            #     time.sleep(3)
            #     response = requests.post(url=self.nomraldabiaourl, data=data, headers=self.header_login).json()
            #     # print(response)
            #     # 获取打标ID放入列表中
            #     for i in range(len(response['data']['print_data']['task']['documents'])):
            #         self.qrCode.append(response['data']['print_data']['task']['documents'][i]['contents'][0]['data']['qr_code'])

            for i in range(len(self.goods_ary)):
                data = {
                    "supply_id": self.goods_ary[i]['supply_id'],
                    "pgid": self.pgid,
                    "sku": self.goods_ary[i]["sku"],
                    "dh_num": self.goods_ary[i]["buy_num"]
                }
                time.sleep(3)
                response = requests.post(url=self.nomraldabiaourl, data=data, headers=self.header_login).json()
                # # 获取打标ID放入列表中  之前的逻辑
                for i in range(len(response['data']['print_data']['task']['documents'])):
                    # 判断是否越库标
                    if response['data']['print_data']['task']['documents'][i]['contents'][0]['data']['img_url'] == self.YueKu_imgurl:
                        self.is_numble = 1
                        self.qrCode.append(
                            response['data']['print_data']['task']['documents'][i]['contents'][0]['data']['qr_code'])
                    else:
                # 获取打标ID放入列表中
                        for i in range(len(response['data']['print_data']['task']['documents'])):
                            self.qrCode.append(response['data']['print_data']['task']['documents'][i]['contents'][0]['data']['qr_code'])

            print("打标成功，脚本继续执行...")
        except BaseException:
            print("生成打标任务数据报错：%s" % response)

    def test_Close_box_no(self):
        """
        关闭容器
        """
        try:
            close_data = {
                "close_type": "normal"
            }
            # 关闭容器操作
            response = requests.post(url=self.close_box_url, data=close_data, headers=self.header_login).json()
        except BaseException:
            print("关闭容器报错：%s" % response)

    def test_getlist_sj_work(self):
        """
        将批次入库操作
        """
        try:
            dianhuo_data = {
                'pgid[0]': self.pgid,
                'status': 10,
                "create_time[0]": self.today.strftime("%Y-%m-%d %H:%M:%S"),
                "create_time[1]": self.tomorrow.strftime("%Y-%m-%d %H:%M:%S"),
            }
            # 获取点货单中的批次ID
            response = requests.post(url=self.dianhuo_url, data=dianhuo_data, headers=self.header_login).json()
            pici_id = response["data"]["data"][0]["pici_id"]
            if pici_id != None:
                commandStockInOut = '/apps/lib/php-7.0.28/bin/php /apps/dat/www/erp1.yishou.com/think task:StockInOut %s' % pici_id
                TestLinkLinux.StockIn().stockin(commandStockInOut)
                print("批次入库成功，脚本继续...")
            else:
                print("批次入库失败，脚本中断请重试...")
        except BaseException:
            print("批次入库报错：%s" % response)

    def test_space_list(self):
        """
        获取空仓位
        """
        # 这里会根据广杭进行区分，同时还判断仓位是否为库存仓位，需配货商品无法上架到库存仓位
        response1 = requests.post(url=self.cangwei_url, headers=self.header_login).json()
        # print(response1["data"]["fahuo_area"])
        #通过random模块里的choice从列表元素中随机取一个值
        area = choice(response1["data"]["fahuo_area"])
        # print(area)
        try:
            space_data = {
                'area[0]': area,
                'is_use': 1,
                'is_band': 0,
            }
            response = requests.post(url=self.space_url, data=space_data, headers=self.header_login).json()
            space = response['data']['list'][0]
            self.emptyspace = space['area'] + space['shelf'] + '-' + space['floor'] + '-' + space['position']
            # print(self.emptyspace)
        except BaseException:
            print("获取空仓位报错：%s" % response)

    def test_shangjia_list(self):
        "上架单明细"
        try:
            if self.is_numble == 1:
                pass
            else:
                data = {
                    "search_type":2,
                    # "keyword":"GZRQ12876",#调试用，记得改回来
                    "keyword":self.box_no,
                    "status":2
                }
                response = requests.post(url=self.select_shangjia_url,data=data,headers=self.header_login).json()
                #因耗时较长，这里提前跑生成上架任务脚本
                shangjiaid = '/apps/lib/php-7.0.28/bin/php /apps/dat/www/erp5.yishou.com/think task:CheckStockInForUpshelf'
                TestLinkLinux.StockIn().stockin(shangjiaid)
                while response["data"].get("data") == None:
                    print("未找到可上架的任务，等待中....")
                    #这里有时候跑了脚本不一定马上生效，为了节省时间，这里如果一直没有则一直跑脚本
                    TestLinkLinux.StockIn().stockin(shangjiaid)
                    time.sleep(5)
                    response = requests.post(url=self.select_shangjia_url, data=data, headers=self.header_login).json()
                    print(response)
                else:
                    us_id = response["data"]["data"][0]["us_id"]
                    self.us_no = response["data"]["data"][0]["us_no"]
                    # print(us_id)
                    # print(self.us_no)
                    data2 = {
                        "us_id":us_id
                    }
                    response1 = requests.post(url=self.select_shangjiainfo_url,data=data2,headers=self.header_login).json()
                    self.dbid_list = []
                    for i in self.sku_list:
                        q_dbid_list = []
                        for a in range(len(response1["data"])):
                            if response1["data"][a]["sku"] == i:
                                q_dbid_list.append(int(response1["data"][a]["dbid"]))
                        self.dbid_list.append(q_dbid_list)
                    # print(self.dbid_list)
                    print("获取上架单明细数据成功,脚本继续执行...")
        except BaseException:
            print("获取上架明细报错：%s" % response1)
    def shangjia(self):
        #进行上架，先领取任务，在进行上架
        try:
            if self.is_numble == 1:
                pass
            else:
                data3 ={
                    "appType":"suzaku",
                    "box_no":self.box_no,
                    # "box_no":"GZRQ12876",#调试用
                    "device_id":"0df86d8f-8c1f-46bf-a828-5415025d13c4",
                    "login_type":"suzaku",
                    "plat_type":"android",
                    "sign":"6F6AABBD0976CA9FA010527611C82202",
                    "token":self.token,
                    "version":"4.0.0"
                }
                response2 = requests.post(url=self.get_box_url,data=data3,headers=self.header_login).json()
                # print(response2)
                if response2["code"] != 200:
                    print(response2)
                data5 = {
                    "appType":"suzaku",
                    "scan":self.box_no,
                    "device_id":"0df86d8f-8c1f-46bf-a828-5415025d13c4",
                    "login_type":"suzaku",
                    "plat_type":"android",
                    "sign":"6F6AABBD0976CA9FA010527611C82202",
                    "token":self.token,
                    "version":"4.0.0"
                }
                response3 = requests.post(url=self.get_bangdrq_url,data=data5,headers=self.header_login).json()
                # print(response3)
                if response3["code"] != 200:
                    print(response3)
                data4 = {
                    "appType": "suzaku",
                    "dbids[]": "",
                    "sku": "",
                    "space": "",
                    "us_no": self.us_no,
                    "device_id": "8a75dcff-fd3e-41e2-9a3e-e26ffea8e727",
                    "login_type": "suzaku",
                    "plat_type": "android",
                    "token": self.token,
                    "version": "4.0.0",
                }
                for i in range(len(self.sku_list)):
                    self.test_space_list()
                    data4["dbids[]"] = tuple(self.dbid_list[i])
                    data4["sku"] = self.sku_list[i]
                    data4["space"] = self.emptyspace
                    # print(self.emptyspace)
                    response4 = requests.post(url=self.get_box_url1,data=data4,headers=self.header_login).json()
                    # print(response4)
                    if response4["code"] != 200:
                        print(response4)
                    else:
                        print("PDA脚本上架成功，脚本继续执行...")
        except BaseException:
            print("PDA上架报错：%s" % response4)

    def select_boci(self):
        """查询波次,生成拣货任务"""
        # try:
        #     data = {
        #         'order_sn': self.order_sn,
        #         # 'order_sn': 12040315352550,
        #     }
        #     # 根据订单号查询波次，获取波次号
        #     response = requests.post(url=self.select_pici_url, data=data, headers=self.header_login).json()
        #     if response["data"]["total"] <= 0:
        #         print("未生成波次，请重试...")
        #     else:
        #         self.wave_picking_no = response['data']['data'][0]['wave_picking_no']
        #         self.boci_id = response['data']['data'][0]['wave_picking_id']
        #         # 对波次进行锁定操作
        #         data1 = {
        #             'order_sn': self.order_sn,
        #             # 'order_sn': 12040315352550,
        #             "multipleSelection[0]": self.wave_picking_no
        #         }
        #         response1 = requests.post(url=self.lock_pici_url, data=data1, headers=self.header_login).json()
        #         #生成拣货任务
        #         data2 = {
        #             'the_ids[0]': self.boci_id,
        #             "generate_type": 1
        #         }
        #         response2 = requests.post(url=self.generate_url, data=data2, headers=self.header_login).json()
        # except BaseException:
        #     print("生成拣货任务报错：%s" % response2)

        try:
            data = {
                'order_sn': self.order_sn,
                # 'order_sn': 12042115352819,
            }
            # print(data)
            # 根据订单号查询波次，获取波次号
            response = requests.post(url=self.select_pici_url, data=data, headers=self.header_login).json()
            if response["data"]["total"] <= 0:
                print("未生成波次，请重试...")

            else:
                self.wave_picking_no = response['data']['data'][0]['wave_picking_no']
                self.boci_id = response['data']['data'][0]['wave_picking_id']
                if response["data"]["data"][0]["wave_picking_picking_type"] == "越库分离":
                # 对波次进行汇集操作
                    data_1 = {
                        "search_value": self.wave_picking_no,
                        "search_key": "wave_picking_no"
                    }
                    # 查询中分任务获取明细ID
                    response1 = requests.post(url=self.zhongfen_url, data=data_1, headers=self.header_login).json()
                    # print(response1)
                    data_2 = {
                        "surpass_summary_id": response1["data"]["list"][0]["surpass_summary_id"]
                    }
                    # 查询中分明细，确认汇集差异
                    response2 = requests.post(url=self.zhongfen_info_url, data=data_2, headers=self.header_login).json()
                    # print(response2)
                else:
                    # 对波次进行锁定操作
                    data1_1 = {
                        'order_sn': self.order_sn,
                        # 'order_sn': 12042115352819,
                        "multipleSelection[0]": self.wave_picking_no
                    }
                    response1 = requests.post(url=self.lock_pici_url, data=data1_1, headers=self.header_login).json()
                    # print(response1)
                    #生成拣货任务
                    data2_1 = {
                        'the_ids[0]': self.boci_id,
                        "generate_type": 1
                    }
                    response2 = requests.post(url=self.generate_url, data=data2_1, headers=self.header_login).json()
        except BaseException:
            print("生成拣货任务报错：%s" % response2)

    def jianhuo_info(self):
        """对拣货任务进行拣货"""
        try:
            if self.is_numble ==1:
                pass
            else:
                data = {
                    'search_key': 5,
                    'search_val': self.wave_picking_no,
                    # 'search_val': "B12010262836305",
                }
                response= requests.post(url=self.select_generate_url, data=data, headers=self.header_login).json()
                print(response)
                jh_dh = response['data']['list'][0]['picking_assignment_no']
                jh_id = response['data']['list'][0]['picking_assignment_id']
                # print(jh_dh,jh_id)

                data1 = {
                    "picking_assignment_no":jh_dh,
                    "appType": "suzaku",
                    "device_id": "8a75dcff-fd3e-41e2-9a3e-e26ffea8e727",
                    "sign": "6F6AABBD0976CA9FA010527611C82202",
                    "login_type": "suzaku",
                    "plat_type": "android",
                    "token": self.token,
                    "version": "4.0.0",
                }
                data2 = {
                    "picking_assignment_no": jh_dh,
                    "dbid": "",
                    "appType": "suzaku",
                    "device_id": "8a75dcff-fd3e-41e2-9a3e-e26ffea8e727",
                    "sign": "6F6AABBD0976CA9FA010527611C82202",
                    "login_type": "suzaku",
                    "plat_type": "android",
                    "token": self.token,
                    "version": "4.0.0",
                }
                #领取拣货任务
                response1 = requests.post(url=self.pda_jh_url, data=data1, headers=self.header_login).json()
                #扫描打标ID进行拣货操作
                for i in self.qrCode:
                    data2["dbid"] = i
                    response2 = requests.post(url=self.pda_jhinfo_url, data=data2, headers=self.header_login).json()
                #提交拣货数据
                response3 = requests.post(url=self.pda_tjjhinfo_url, data=data1, headers=self.header_login).json()
                print("拣货成功，脚本继续执行...")
        except BaseException:
            print("拣货报错：%s" % response1)


    def check_dbid(self):
        try:
            # 根据获取到的波次号，打标ID进行波次校验操作
            data_3 = {
                "wave_picking_no": self.wave_picking_no,
                "qrCode": "",
                "deskNo": self.deskno
            }
            data_4 = {
                "deskNo": self.deskno,
                "wave_picking_no": self.wave_picking_no
            }
            response = requests.post(url=self.get_jiaoyan_url, data=data_4, headers=self.header_login).json()
            print("获取波次信息成功...脚本继续执行")
            # 遍历打标ID进行校验操作
            for i in range(len(self.qrCode)):
                data_3['qrCode'] = self.qrCode[i]
                response1 = requests.post(url=self.check_url, data=data_3, headers=self.header_login).json()
            data_4 = {
                "deskNo": self.deskno,
                "wave_picking_no": self.wave_picking_no,
                "qrCode": self.qrCode[-1],
                "is_pc": 1
            }
            # 校验完最后一个获取快递单号
            response3 = requests.post(url=self.get_kuaidi_url, data=data_4, headers=self.header_login).json()
            if response3["code"] == 200:
                print("波次校验成功...请手动导入重量")
            else:
                print(response3)
            #之前逻辑，保留
            # data = {
            #     'order_sn': self.order_sn,
            # }
            # # 根据订单号查询波次，获取波次号
            # response = requests.post(url=self.select_pici_url, data=data, headers=self.header_login).json()
            # if response["data"]["total"] <= 0:
            #     print("未生成越库波次，请重试...")
            # else:
            #     self.wave_picking_no = response['data']['data'][0]['wave_picking_no']
            #     # 对波次进行锁定操作
            #     data_1 = {
            #         "search_value": self.wave_picking_no,
            #         "search_key": "wave_picking_no"
            #     }
            #     # 查询中分任务获取明细ID
            #     response1 = requests.post(url=self.zhongfen_url, data=data_1, headers=self.header_login).json()
            #     data_2 = {
            #         "surpass_summary_id": response1["data"]["list"][0]["surpass_summary_id"]
            #     }
            #     # 查询中分明细，确认汇集差异
            #     response2 = requests.post(url=self.zhongfen_info_url, data=data_2, headers=self.header_login).json()
            #     # 根据获取到的波次号，打标ID进行波次校验操作
            #     data_3 = {
            #         "wave_picking_no": self.wave_picking_no,
            #         "qrCode": "",
            #         "deskNo": self.deskno
            #     }
            #     time.sleep(2)
            #     data_4 = {
            #         "deskNo": self.deskno,
            #         "wave_picking_no": self.wave_picking_no
            #     }
            #     response = requests.post(url=self.get_jiaoyan_url, data=data_4, headers=self.header_login).json()
            #     print("获取波次信息成功...脚本继续执行")
            #     # 遍历打标ID进行校验操作
            #     for i in range(len(self.qrCode)):
            #         data_3['qrCode'] = self.qrCode[i]
            #         response1 = requests.post(url=self.check_url, data=data_3, headers=self.header_login).json()
            #     data_4 = {
            #         "deskNo": self.deskno,
            #         "wave_picking_no": self.wave_picking_no,
            #         "qrCode": self.qrCode[-1],
            #         "is_pc": 1
            #     }
            #     # 校验完最后一个获取快递单号
            #     response3 = requests.post(url=self.get_kuaidi_url, data=data_4, headers=self.header_login).json()
            #     if response3["code"] == 200:
            #         print("波次校验成功...请手动导入重量")
            #     else:
            #         print(response3)
        except BaseException:
            print("波次校验报错：%s" % response1)


dt = sestApi()
num = sys.argv[1]
if int(num) == 1 or num ==None:
    order_sn = input("请输入订单号：")
    dt.test_login()
    dt.select_order_info(order_sn)
    dt.test_goods_Purchase()
    dt.check_order_info()
    dt.test_achieve_box_no()
    dt.test_bind_deskno()
    dt.test_bind_box_no()
    dt.test_select_supply_info()
    dt.test_dh_info()
    dt.test_create_db_info()
    dt.test_Close_box_no()
    dt.test_getlist_sj_work()
    dt.test_shangjia_list()
    dt.shangjia()
    dt.select_boci()
    dt.jianhuo_info()
    dt.check_dbid()
elif int(num) ==2:
    order_sn = input("请输入订单号：")
    dt.test_login()
    dt.select_order_info(order_sn)
    dt.test_goods_Purchase()
    dt.check_order_info()
    dt.test_achieve_box_no()
    dt.test_bind_deskno()
    dt.test_bind_box_no()
    dt.test_select_supply_info()
    dt.test_dh_info()
    dt.test_create_db_info()
    dt.test_Close_box_no()
    dt.test_getlist_sj_work()
    dt.test_shangjia_list()
    dt.shangjia()
else:
    print("请输入对应指令\n1:运行全部脚本\n2:运行至上架脚本")