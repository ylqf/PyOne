# PyOne - [oneindex](https://github.com/donwa/oneindex)的python版本

## 说明 ##
1. 写PyOne更多的是为了自己的个性化需求，不具有通用性，这个版本基本完全照抄了oneindex的功能
2. 因为是为了自己的个性化需求，因此PyOne不会经常更新，建议使用：[oneindex](https://github.com/donwa/oneindex)
3. PyOne适合Python程序猿进行二开

## 适用onedrive版本 ##
1. 世纪互联版
2. onedrive商业版（未测试）
3. onedrive教育版（未测试）

## 适用环境 ##
1. linux环境
2. Python2.7

## **提前准备**和**安装教程**内容请**仔细阅读**

## 提前准备 ##
0. 根据自己的onedrive版本，修改**function.py**的**od_type**值，
    - business_21v ：世纪互联版
    - business ：国际版
1. 需要自己注册Azure directory应用
    - 世纪互联版注册地址：https://portal.azure.cn/?whr=azure.com#blade/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/RegisteredApps
    - 国际版注册地址：https://portal.azure.com/#blade/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/RegisteredApps

    注册时，登录url设置成你的域名

    - 修改**function.py**的**client_id**值为**应用程序 ID**
    - 修改**function.py**的**redirect_uri**值为**刚才设置的域名**

    注册后，同一个页面，点“设置”

    - 所需权限
        - Windows Azure Active Directory - 委派权限 -Sign in and read user profile （默认值）
        - Office 365 SharePoint Online - 委派权限 - Read user files 和 Read and write user files （别选错，默认倒二、倒三位置）

    - 密钥
        - 添加密钥，到期时间选“1年内”
        - 保存后保存好密钥，修改**function.py**的**client_secret**值为密钥

2. 修改**function.py**的**config_dir**值为**源码所在目录下的config文件夹**
3. 修改**function.py**的**share_path**值为**你要分享的onedrive文件夹**

## 安装教程 ##
1. 首先将源码放到服务器某个目录下，假设当前网站目录是：/root/pyone
    - 因`config/`文件夹上传不了，运行：`mkdir config`，创建一个文件夹
2. 安装依赖环境：wget https://bootstrap.pypa.io/get-pip.py && python get-pip.py && pip install -r requirement.txt
3. 配置nginx环境：
```
server
{
    listen 80;
    server_name 你的域名;
        location / {
        proxy_pass http://127.0.0.1:34567;
        proxy_redirect off;
        proxy_set_header Host $host:80;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    access_log  /www/wwwlogs/pyone.log;
}
```
4. 运行：
    - 源码目录下运行: gunicorn -w4 -b 0:34567 run:app
5. 授权：
    - 访问你的域名，然后就可以去授权onedrive的操作了
6. 添加以下定时任务到crontab
```
# 更新密钥
0 * * * * python 源码目录/function.py GetToken
# 更新文件
*/10 * * * * python 源码目录/function.py UpdateFile
```

## 更多功能 ##
- **配置开机启动（centos）**
    - 修改supervisord.conf，将**directory**修改为源码所在目录
    - 运行: `echo "supervisord -c 源码目录/supervisord.conf" >> /etc/rc.d/rc.local`


- **上传一个文件：**
`python function.py Upload 本地文件路径 远程目录`

比如：`python function.py Upload /root/test.txt share` 即把本地的test/txt文件上传到onedrive的share目录


- **上传本地目录：**
`python function.py UploadDir 本地目录 远程目录`

比如：`python function.py UploadDir /root/video video` 即本本地的video目录下的所有文件上传到onedrive的video目录





-------------------------
-------------------------
点击链接加入群聊【站长技术交流】：https://jq.qq.com/?_wv=1027&k=50L3j17

-------------------------
-------------------------
Abbey最近准备做微信分享视频流量，有流量渠道的大佬欢迎合作，平台、视频都有了，就差流量

