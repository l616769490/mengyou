__version__ = '0.1.9'

from .right import (
    isLogin, getTokenFromHeader, getDB, decode, updateToken, authRight, getBodyAsJson, getBodyAsStr, encodeToken
)

from .oss import (
	getShanghaiOss
)