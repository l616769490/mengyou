###############################################################
# 
# 权限鉴定
# 
# 
# 
###############################################################
import json
import logging
import fcutils
import pymysql

_log = logging.getLogger()

# 配置文件地址
_CONF_HOST = 'https://1837732264572668.cn-shanghai.fc.aliyuncs.com/2016-08-15/proxy/ly-config/getConfigByName/'

def isLogin(environ):
    ''' 验证是否已登录，登录则更新token
    :return 错误返回 False
    :return 成功返回 True
    '''
    oldPayload = getTokenFromHeader(environ)
    if oldPayload == None:
        return Flase
    
    return True

def getTokenFromHeader(environ):
    ''' 验证是否存在3RDSession，存在返回解码的值失败返回None
    '''
    # 验证头信息
    if 'HTTP_3RD_SESSION' not in environ:
        return None
    
    http3RdSession = environ['HTTP_3RD_SESSION'].replace('\\n', '\n')
    decode_res = decode(http3RdSession)

    if decode_res['message'] == 'fail':
        return None

    return decode_res['data']['decode_str']

def getDB():
    # 获取数据库连接配置
    conf = json.loads(fcutils.getDataForStr(_CONF_HOST, 'ly_common_sql.json').text)
    db_conf = json.loads(conf['data'])
    # 连接数据库
    db = pymysql.connect(db_conf['url'], db_conf['username'], db_conf['password'], db_conf['database'], charset="utf8", cursorclass=pymysql.cursors.DictCursor)
    return db

def decode(data):
    ''' jwt解锁
    '''
    pub_key = json.loads(fcutils.getDataForStr(_CONF_HOST, 'rsa_public_key.pem').text)['data']
    request_data = fcutils.decode(data, pub_key)
    return request_data

def updateToken(payload):
    ''' 更新token
    '''
    # 一个月
    if payload['keep'] == 1:
        exp = fcutils.timeLater(1, 'month')
        payload['exp'] = exp
        return payload
    else:
        exp = fcutils.timeLater(0.5, 'hour')
        payload['exp'] = exp
        return payload

def authRight(environ):
    ''' 权限验证，成功返回True，失败返回False
    '''
    db = getDB()
    cursor = db.cursor()
    # seller_user, sellerId, roles, keep
    token = getTokenFromHeader(environ)
    if token == None or 'roles' not in token:
        return False
    # 获取接口地址
    requestUri = environ['fc.request_uri']
    fcInterfaceURL = requestUri.split('proxy')[1]
    if '?' in fcInterfaceURL:
        index = fcInterfaceURL.rfind('?')
        fcInterfaceURL = fcInterfaceURL[:index]
    
    roles = ','.join(str(r['id']) for r in token['roles'])
    # 获取该用户所有角色支持的接口集合
    sql = '''SELECT interface FROM ly_auth_interface WHERE id IN (
        SELECT interface_id FROM ly_auth_access_interface WHERE access_id IN (
            SELECT access_id FROM ly_auth_role_access WHERE role_id IN (%s))) AND `delete`="0"''' % roles
    cursor.execute(sql)
    roleUrls = cursor.fetchall()
    if roleUrls == None:
        return False
    cursor.close()
    interfaces = [rurl['interface'] for rurl in roleUrls]

    return True if fcInterfaceURL in interfaces else False

def getBodyAsJson(environ):
    ''' 获取json格式的请求体
    '''
    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except (ValueError):
        request_body_size = 0
    return json.loads(environ['wsgi.input'].read(request_body_size))

def getBodyAsStr(environ):
    ''' 获取string格式的请求体
    '''
    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except (ValueError):
        request_body_size = 0
    return environ['wsgi.input'].read(request_body_size)
    

def encodeToken(data):
    ''' 加密token
    格式：header.payload.signature
    :param data 签名参数
    :return 成功返回加密值，失败返回None
    '''
    conf = json.loads(fcutils.getDataForStr(_CONF_HOST, 'rsa_private_key.pem').text)
    if conf['status'] != '200':
        # 出错处理
        return None

    priv_key = conf['data']

    token_value = fcutils.encode(data, priv_key)
    
    return token_value
    
    



