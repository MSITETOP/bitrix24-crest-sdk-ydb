# bitrix24-crest-sdk-ydb
Tiny Python SDK to call Bitrix24 REST methods via OAuth 2.0 use YDB storage


bx24 = CRestApp(
    member_id = 'member_id', 
    client_id = 'app........', 
    client_secret = 'client_secret', 
    ydb_endpoint = 'grpcs://ydb.serverless.yandexcloud.net:2135', 
    ydb_database = '/ru-central1/.../....', 
    ydb_credentials = 't1............................'
)

Получение кредлов базы ydb

cd ubuntu
yc config set service-account-key authorized_key.json
yc iam create-token

POST DATA PARAMS
arParamsInstall = {
      "DOMAIN": "site.....com", 
      "PROTOCOL": "1", 
      "LANG": "ru", 
      "APP_SID": "APP_SID",
      "AUTH_ID": "AUTH_ID", 
      "AUTH_EXPIRES": "3600",   
      "REFRESH_ID": "REFRESH_ID",
      "member_id": "member_id",
      "status": "F",  
      "PLACEMENT": "DEFAULT",  
}
bx24.installApp(arParamsInstall)

bx24.call('crm.deal.list', {
    'filter': {"ID":49},
    'select': ['TITLE']
})

batch={
    'contacts': 'crm.contact.list', 
    'deals': 'crm.deal.list'
}
batchParams={
    'contacts': [
        'select[]=TITLE', 
        'order[ID]=DSC', 
        'filter[>ID]=15'
    ], 
    'deals' : [
        'select[]=TITLE',
    ]
}
bx24.callBatch(batch=batch, batch_params=batchParams)
