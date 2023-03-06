
class AccessTokenFail(Exception):
    """ 访问令牌失败 """

    def __init__(self, err_desc: str = "访问令牌失败"):
        self.err_desc = err_desc
class PermissionNotEnough(Exception):
    """ 权限不足,拒绝访问 """

    def __init__(self, err_desc: str = "权限不足,拒绝访问"):
        self.err_desc = err_desc
