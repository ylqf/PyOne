#-*- coding=utf-8 -*-
import webbrowser
import json
import requests
import collections
import sys
if sys.version_info[0]==3:
    import urllib.parse as urllib
else:
    import urllib
import os
import time
import humanize
import StringIO
from dateutil.parser import parse
from Queue import Queue
from threading import Thread


#######网站目录
config_dir='/root/pyone/config'
#######分享目录
share_path='/2mm'
#######Azure directory应用设置,自行注册Azure directory
client_id='应用程序id'
client_secret='api密钥'
redirect_uri='http://yourdomain'

#######授权链接
od_type='business_21v' #国际版：bussiness; 世纪互联版：bussiness_21v
global app_url
if od_type=='business':
    BaseAuthUrl='https://login.microsoftonline.com'
    ResourceID='https://api.office.com/discovery/'
    app_url=''
elif od_type=='business_21v':
    BaseAuthUrl='https://login.partner.microsoftonline.cn'
    ResourceID='00000003-0000-0ff1-ce00-000000000000'
    app_url='https://2mm-my.sharepoint.cn/'  #世纪互联版需要自定义onedrive的域名,最后必须带/

LoginUrl=BaseAuthUrl+'/common/oauth2/authorize?response_type=code\
&client_id={client_id}&redirect_uri={redirect_uri}'.format(client_id=client_id,redirect_uri=urllib.quote(redirect_uri))
OAuthUrl=BaseAuthUrl+'/common/oauth2/token'
AuthData='client_id={client_id}&redirect_uri={redirect_uri}&client_secret={client_secret}&code={code}&grant_type=authorization_code&resource={resource_id}'
ReFreshData='client_id={client_id}&redirect_uri={redirect_uri}&client_secret={client_secret}&refresh_token={refresh_token}&grant_type=refresh_token&resource={resource_id}'

headers={}

################################################################################
###################################授权函数#####################################
################################################################################

def ODLogin():
    print('your browser should be open then url:{}\n,if not? open the url by yourself.'.format(LoginUrl))
    webbrowser.open(LoginUrl)

def OAuth(code):
    headers['Content-Type']='application/x-www-form-urlencoded'
    data=AuthData.format(client_id=client_id,redirect_uri=urllib.quote(redirect_uri),client_secret=client_secret,code=code,resource_id=ResourceID)
    url=OAuthUrl
    r=requests.post(url,data=data,headers=headers)
    return json.loads(r.text)

def ReFreshToken(refresh_token):
    headers['Content-Type']='application/x-www-form-urlencoded'
    data=ReFreshData.format(client_id=client_id,redirect_uri=urllib.quote(redirect_uri),client_secret=client_secret,refresh_token=refresh_token,resource_id=app_url)
    url=OAuthUrl
    r=requests.post(url,data=data,headers=headers)
    return json.loads(r.text)


def GetToken():
    if os.path.exists(os.path.join(config_dir,'token.json')):
        with open(os.path.join(config_dir,'token.json'),'r') as f:
            token=json.load(f)
        if time.time()>int(token.get('expires_on')):
            refresh_token=token.get('refresh_token')
            token=ReFreshToken(refresh_token)
            if token.get('access_token'):
                with open(os.path.join(config_dir,'token.json'),'w') as f:
                    json.dump(token,f,ensure_ascii=False)
        return token.get('access_token')
    else:
        return False

def GetAppUrl():
    global app_url
    if os.path.exists(os.path.join(config_dir,'AppUrl')):
        with open(os.path.join(config_dir,'AppUrl'),'r') as f:
            app_url=f.read().strip()
        return app_url
    else:
        if od_type=='business':
            token=GetToken()
            if token:
                header={'Authorization': 'Bearer {}'.format(token)}
                url='https://api.office.com/discovery/v2.0/me/services'
                r=requests.get(url,headers=header)
                retdata=json.loads(r.text)
                if retdata.get('value'):
                    return retdata.get('value')[0]['serviceResourceId']
            return False
        else:
            return app_url

if not GetToken():
    app_url=GetAppUrl()

################################################################################
###############################onedrive操作函数#################################
################################################################################
def GetExt(name):
    return name.split('.')[-1]

def Dir(path='/'):
    if path=='/':
        BaseUrl=app_url+'_api/v2.0/me/drive/root/children?expand=thumbnails'
    else:
        if path.endswith('/'):
            path=path[:-1]
        BaseUrl=app_url+'_api/v2.0/me/drive/root:{}:/children?expand=thumbnails'.format(path)
    items,globalDict,extDict=GetItem(BaseUrl,items=collections.OrderedDict(),globalDict={},extDict={})
    return items,globalDict,extDict

def GetItem(url,items,globalDict,extDict):
    token=GetToken()
    header={'Authorization': 'Bearer {}'.format(token)}
    r=requests.get(url,headers=header)
    data=json.loads(r.text)
    values=data.get('value')
    print('fetching data from {}'.format(url))
    if len(values)>0:
        for value in values:
            item={}
            if value.get('folder'):
                item['type']='folder'
                item['name']=value['name']
                item['id']=value['id']
                item['size']=humanize.naturalsize(value['size'], gnu=True)
                item['lastModtime']=humanize.naturaldate(parse(value['lastModifiedDateTime']))
                if value.get('folder').get('childCount')==0:
                    item['value']={}
                else:
                    url=app_url+'_api/v2.0/me'+value.get('parentReference').get('path')+'/'+value.get('name')+':/children?expand=thumbnails'
                    item['value'],globalDict,extDict=GetItem(url,collections.OrderedDict(),globalDict,extDict)
                globalDict[value['id']]=dict(name=value['name'])
            else:
                item['type']='file',
                item['name']=value['name']
                item['id']=value['id']
                item['size']=humanize.naturalsize(value['size'], gnu=True)
                item['lastModtime']=humanize.naturaldate(parse(value['lastModifiedDateTime']))
                item['downloadUrl']=value['@content.downloadUrl']
                globalDict[value['id']]=dict(name=value['name'],downloadUrl=value['@content.downloadUrl'])
                extDict.setdefault(GetExt(value['name']),[]).append(value['id'])
            items[item['name']]=item
    if data.get('@odata.nextLink'):
        GetItem(data.get('@odata.nextLink'),items,globalDict,extDict)
    return items,globalDict,extDict


def UpdateFile():
    items,globalDict,extDict=Dir(share_path)
    with open(os.path.join(config_dir,'data.json'),'w') as f:
        json.dump(items,f,ensure_ascii=False)
    with open(os.path.join(config_dir,'KeyValue.json'),'w') as f:
        json.dump(globalDict,f,ensure_ascii=False)
    with open(os.path.join(config_dir,'extDict.json'),'w') as f:
        json.dump(extDict,f,ensure_ascii=False)
    print('update file success!')


def FileExists(filename):
    token=GetToken()
    headers={'Authorization':'bearer {}'.format(token),'Content-Type':'application/json'}
    search_url=app_url+"_api/v2.0/me/drive/root/search(q='{}')".format(filename)
    r=requests.get(search_url,headers=headers)
    jsondata=json.loads(r.text)
    if len(jsondata['value'])==0:
        return False
    else:
        return True

################################################上传文件
def _filesize(path):
    size=os.path.getsize(path)
    # print('{}\'s size {}'.format(path,size))
    return size

def _file_content(path,offset,length):
    size=_filesize(path)
    offset,length=map(int,(offset,length))
    if offset>size:
        print('offset must smaller than file size')
        return False
    length=length if offset+length<size else size-offset
    endpos=offset+length-1 if offset+length<size else size-1
    # print("read file {} from {} to {}".format(path,offset,endpos))
    with open(path,'rb') as f:
        f.seek(offset)
        content=f.read(length)
    return content


def _upload(filepath,remote_path): #remote_path like 'share/share.mp4'
    token=GetToken()
    headers={'Authorization':'bearer {}'.format(token)}
    url=app_url+'_api/v2.0/me/drive/root:/'+remote_path+':/content'
    r=requests.put(url,headers=headers,files={'file':open(filepath,'rb')})
    data=json.loads(r.content)
    if data.get('error'):
        print(data.get('error').get('message'))
        return False
    elif data.get('@content.downloadUrl'):
        print('upload success!')
        return data.get('@content.downloadUrl')
    else:
        print(data)
        return False



def CreateUploadSession(path):
    token=GetToken()
    headers={'Authorization':'bearer {}'.format(token),'Content-Type':'application/json'}
    url=app_url+'_api/v2.0/me/drive/root:/'+path+':/createUploadSession'
    data={
          "item": {
            "@microsoft.graph.conflictBehavior": "rename",
          }
        }
    r=requests.post(url,headers=headers,data=json.dumps(data))
    retdata=json.loads(r.content)
    if r.status_code==409:
        print('file exists')
        return False
    else:
        return retdata

def UploadSession(uploadUrl, filepath, offset, length):
    token=GetToken()
    size=_filesize(filepath)
    offset,length=map(int,(offset,length))
    if offset>size:
        print('offset must smaller than file size')
        return False
    length=length if offset+length<size else size-offset
    endpos=offset+length-1 if offset+length<size else size-1
    print('upload file {} from {} to {}'.format(filepath,offset,endpos))
    filebin=_file_content(filepath,offset,length)
    headers={}
    # headers['Authorization']='bearer {}'.format(token)
    headers['Content-Length']=str(length)
    headers['Content-Range']='bytes {}-{}/{}'.format(offset,endpos,size)
    r=requests.put(uploadUrl,headers=headers,data=filebin)
    data=json.loads(r.content)
    if r.status_code==202:
        offset=data.get('nextExpectedRanges')[0].split('-')[0]
        UploadSession(uploadUrl, filepath, offset, length)
    elif data.get('@content.downloadUrl'):
        print('upload success!')
        return data.get('@content.downloadUrl')
    else:
        print('upload fail')
        print(data.get('error').get('message'))
        r=requests.get(uploadUrl)
        if r.status_code==404:
            print('please retry upload file {}'.format(filepath))
            requests.delete(uploadUrl)
            return False
        data=json.loads(r.content)
        if data.get('nextExpectedRanges'):
            offset=data.get('nextExpectedRanges')[0].split('-')[0]
            UploadSession(uploadUrl, filepath, offset, length)
        else:
            print('please retry upload file {}'.format(filepath))
            requests.delete(uploadUrl)
            return False

def Upload(filepath,remote_path=None):
    token=GetToken()
    headers={'Authorization':'bearer {}'.format(token),'Content-Type':'application/json'}
    if remote_path is None:
        remote_path=os.path.basename(filepath)
    elif remote_path.endswith('/'):
        remote_path=os.path.join(remote_path,os.path.basename(filepath))
    if remote_path.startswith('/'):
        remote_path=remote_path[1:]
    print('local file path:  {}\nremote file path:  {}'.format(filepath,remote_path))
    if _filesize(filepath)<10485760:
        print('upload small file')
        result=_upload(filepath,remote_path)
        if result!=False:
            print('upload success')
        else:
            print('upload fail')
    else:
        print('upload large file')
        session_data=CreateUploadSession(remote_path)
        if session_data==False:
            print('file exists')
        else:
            if session_data.get('uploadUrl'):
                uploadUrl=session_data.get('uploadUrl')
                length=327680*10
                offset=0
                UploadSession(uploadUrl,filepath,offset,length)
            else:
                print(session_data)
                print('create upload session fail!')
                return False


class MultiUpload(Thread):
    def __init__(self,waiting_queue):
        super(MultiUpload,self).__init__()
        self.queue=waiting_queue

    def run(self):
        while not self.queue.empty():
            localpath,remote_dir=self.queue.get()
            Upload(localpath,remote_dir)

def LoadLocalFile():
    with open(os.path.join(config_dir,'data.json'),'r') as f:
        remotefiles=json.load(f)
    return remotefiles

def UploadDir(local_dir,remote_dir,threads=5):
    items,globalDict=Dir(remote_dir)
    #remotefiles=LoadLocalFile()
    localfiles=os.listdir(local_dir)
    waiting_files=[os.path.join(local_dir,i) for i in localfiles if not items.get(i)]
    queue=Queue()
    tasks=[]
    if not remote_dir.endswith('/'):
        remote_dir+='/'
    for file in waiting_files:
        queue.put((file,remote_dir))
    for i in range(min(threads,queue.qsize())):
        t=MultiUpload(queue)
        t.start()
        tasks.append(t)
    for t in tasks:
        t.join()







if __name__=='__main__':
    func=sys.argv[1]
    if len(sys.argv)>2:
        args=sys.argv[2:]
        eval(func+str(tuple(args)))
    else:
        eval(func+'()')
