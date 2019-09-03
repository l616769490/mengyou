__version__ = '0.2.2'

from .right import (
    isLogin, getTokenFromHeader, getDB, decode, updateToken, authRight, getBodyAsJson, getBodyAsStr, encodeToken
)

from .oss import (
	getShanghaiOss
)