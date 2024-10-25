import os
import pymongo
from pymongo.errors import DuplicateKeyError
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sina.settings import LOCAL_MONGO_HOST, LOCAL_MONGO_PORT, DB_NAME



class WeiboLogin():
    def __init__(self):
        self.url_cn = 'https://passport.weibo.cn/signin/login'
        self.url_com = 'https://login.sina.com.cn/signup/signin.php'
        self.browser = webdriver.Chrome()
        self.browser.set_window_size(1050, 840)
        self.wait = WebDriverWait(self.browser, 20)

    def open_cn(self, name, passwd):
        """
        打开网页输入用户名密码并点击登录按钮
        :param name:
        :param passwd:
        :return: None
        """
        self.browser.delete_all_cookies()
        self.browser.get(self.url_cn)
        username = self.wait.until(EC.presence_of_element_located((By.ID, 'loginName')))
        password = self.wait.until(EC.presence_of_element_located((By.ID, 'loginPassword')))
        submit = self.wait.until(EC.element_to_be_clickable((By.ID, 'loginAction')))
        username.send_keys(name)
        password.send_keys(passwd)
        submit.click()

    def open_com(self, name, passwd):
        """
        打开网页输入用户名密码并点击登录按钮
        :param name:
        :param passwd:
        :return: None
        """
        self.browser.delete_all_cookies()
        self.browser.get(self.url_com)
        username = self.wait.until(EC.presence_of_element_located((By.ID, 'username')))
        username.clear()
        password = self.wait.until(EC.presence_of_element_located((By.ID, 'password')))
        submit = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']")))
        username.send_keys(name)
        password.send_keys(passwd)
        submit.click()

    def run(self, username, password):
        """
        运行自动化登录流程,但是验证码需要自己填上去
        :param username: 用户名
        :param password: 密码
        :return: cookies
        """
        self.open_com(username, password)
        # 设置显式等待,60s没有登录成功则触发超时异常
        WebDriverWait(self.browser, timeout=60).until(
            title_is()
        )
        cookies = self.browser.get_cookies()
        cookie = [item["name"] + "=" + item["value"] for item in cookies]
        # 必须转化成这种字符串形式
        cookie_str = '; '.join(item for item in cookie)
        # self.browser.quit()
        return cookie_str


class title_is(object):
    """An expectation for checking the title of a page.
    title is the expected title, which must be an exact match
    returns True if the title matches, false otherwise."""

    def __call__(self, driver):
        return ("我的" in driver.title) or ("微博" == driver.title)


if __name__ == '__main__':
    # 导入账号
    file_path = 'account.txt'
    with open(file_path, 'r') as f:
        lines = f.readlines()
    # 数据库实例
    mongo_client = pymongo.MongoClient(LOCAL_MONGO_HOST, LOCAL_MONGO_PORT)
    collection = mongo_client[DB_NAME]["account"]
    # 浏览器实例
    brower = WeiboLogin()
    for line in lines:
        line = line.strip()
        username = line.split('----')[0]
        password = line.split('----')[1]
        print('=' * 10 + username + '=' * 10)
        try:
            cookie_str = brower.run(username, password)
        except Exception as e:
            print(e)
            continue
        print('获取cookie成功')
        print('Cookie:', cookie_str)
        try:
            collection.insert_one(
                {"_id": username, "password": password, "cookie": cookie_str, "status": "success"})
        except DuplicateKeyError as e:
            collection.find_one_and_update({'_id': username}, {'$set': {'cookie': cookie_str, "status": "success"}})
