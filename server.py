#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""WebフレームワークBottleスクリプト.

ウェブサーバ機能に加えて、REST APIを提供します。

依存外部モジュール
  bottle
  gevent
  gevent-websocket
  jsonpickle  https://github.com/jsonpickle/jsonpickle
  tinydb  http://tinydb.readthedocs.io/en/latest/#

一括インストール
pip install -r requirements.txt
"""

__author__ = 'Takamitsu IIDA'
__version__ = '0.0'
__date__ = '2016/12/15'

# サーバ種別
# 開発時はbottle
__server__ = "bottle"
__server__ = "gevent"

# 標準モジュールのインポート
import logging
import os
import re
import sys
import threading  # Lockオブジェクトの作成に必要


def here(path=''):
  """相対パスを絶対パスに変換して返却します"""
  return os.path.abspath(os.path.join(os.path.dirname(__file__), path))

# libフォルダにおいたpythonスクリプトを読みこませるための処理
sys.path.append(here("./lib"))
sys.path.append(here("./lib/site-packages"))

if __server__ == "gevent":
  # geventを使う場合のお作法
  from gevent import monkey
  monkey.patch_all()

  # geventのWSGIServerとWebSocketを利用する
  from gevent.pywsgi import WSGIServer
  from geventwebsocket.handler import WebSocketHandler
  # from geventwebsocket import WebSocketError

# bottleフレームワークを読み込む
import bottle
from bottle import HTTPResponse
from bottle import delete
from bottle import get
from bottle import post
from bottle import put
# from bottle import redirect  # リダイレクトするならこれを使う
from bottle import route
from bottle import static_file
from bottle import template

# リクエストとレスポンスは用語が汎用すぎるのでimportせずに
# bottle.request、bottle.responseというように指定する
#
# レスポンスコード早見表
# 200 OK
# 201 Created POSTメソッドによりリソースが作成された
# 202 Accepted リクエストを受け付けたが、処理は終わっていない
# 204 No Content リクエストの処理は成功したが返す内容がない
# 304 Not Modified リソースに変更はない
# 400 Bad Request リクエストの内容が不正なとき、あるいは他に400番台に適したコードがない
# 401 Unauthorized 認証されていない
# 403 Forbidden 認証以外の理由でリソースにアクセス許可がない
# 404 Not Found リソースが存在しない
# 405 Method Not Allowed 使用されているHTTP動詞は許可されていない
# 409 Conflict 競合が発生している
# 412 Precondition Failed リクエストで指定された条件を満たさない(ETagの一致など)
# 500 Internal Server Error サーバで障害が発生
# 504 Service Unavailable 過負荷やメンテナンス等により一時的に処理ができない

import jsonpickle
jsonpickle.set_preferred_backend('json')
jsonpickle.set_encoder_options('json', sort_keys=False, indent=2, ensure_ascii=False)
# REST APIで複雑な構造をしたオブジェクトを返却するにはjsonpickleが便利
# jsonpickleの使い方
# デフォルトでは余計なクラス情報が付加されるので、unpicklableはFalseに指定する
# json_string = jsonpickle.encode(obj, unpicklable=False)

# 情報の保管庫として辞書型を保存できるtinydbを使う
from tinydb import Query
from tinydb import TinyDB

# tinydbの使い方
#
# 辞書型を格納する
# db.insert({'name': 'John', 'age': 22})
#
# 全データを配列で取得する
# db.all()
#
# 検索する
# q = Query()
# db.search(q.name == 'John')
#
# アップデートする
# nameがJohnになっている辞書型の'age'フィールドを23に変更する
# db.update({'age': 23}, q.name == 'John')
#
# 削除する
# db.remove(q.age < 22)
#
# 全部削除する
# db.purge()

#        1         2         3         4         5         6         7
# 34567890123456789012345678901234567890123456789012345678901234567890123456789
#
# RESTのテストです。
# GET/POST/DELETE/PUTの使い分けを確認します。

# テストデータとしてユーザ情報を保管するデータベース
if not os.path.exists(here('./data')):
  os.mkdir(here('./data'))
db = TinyDB(here('./data/users.json'))

# データベースにクエリをかけるためのオブジェクト
# ユーザ情報を格納することを前提にしているので、オブジェクト名をUserにしておくとわかりやすい
# User.name == 'abc' のように条件を書ける
User = Query()

# 名前が有効かどうかをチェックする正規表現
# アルファベットのみ、64文字以内、を条件とする
name_pattern = re.compile(r'^[a-zA-Z\d]{1,64}$')

# 排他制御のためのロック
# dbに変更を加えるときは
# with db_lock:
# でロックを獲得してから実行する
db_lock = threading.RLock()


# POSTメソッド
# 新規データを登録
# AngularJS save()
@post('/rest/users/<newname>')
def save_handler(newname):
  """新規にデータを保存します"""
  # 戻り値となる辞書型データ
  result_dict = {}
  result_dict["status"] = "SUCCESS"  # or ERROR
  result_dict["message"] = ""  # メッセージ文字列

  logging.info("%s will be created.", newname)

  # 処理の途中で異常を検知したら例外を出すので、tryで捕捉する
  # 例外の使い分け
  #  raise ValueError 正しい型だが適切でない値を受け取った場合
  #  raise KeyError 辞書型のキーが集合内に見つからなかった場合
  try:
    # リクエストからJSON形式のデータを取り出す
    try:
      data = bottle.request.json
      print(data)
      # このdataの中身は英数字であってもUNICODEになっている。strで欲しい場合はこうする。
      # data = { str(key) : str(value) for key, value in data.items() }
    except Exception:
      raise ValueError

    # nameキーの値を取り出す
    try:
      name = data.get("name", "")
    except Exception:
      raise ValueError

    # nameの形式をチェックする
    try:
      if name_pattern.match(name) is None:
        print("name pattern check error")
        raise ValueError
    except Exception:
      raise ValueError

    # データベースに同じ名前が存在したらエラー
    if db.get(User.name == name):
      raise KeyError

    # JSONデータをデータベースに追加する
    try:
      with db_lock:
        db.insert(data)
    except Exception:
      raise ValueError
  #
  except ValueError:
    # 400 Bad Request リクエストの内容が不正なとき、あるいは他に400番台に適したコードがない
    r = http_response(status=400)
    result_dict["status"] = "ERROR"
    result_dict["message"] = "パラメータエラー, 値が不正です"
    r.body = jsonpickle.encode(result_dict, unpicklable=False)
    return r
  except KeyError:
    # 409 Conflict 競合が発生している
    r = http_response(status=409)
    result_dict["status"] = "ERROR"
    result_dict["message"] = "パラメータエラー, そのキーは既に存在します"
    r.body = jsonpickle.encode(result_dict, unpicklable=False)
    return r

  # 200を返す
  r = http_response(status=200)
  result_dict["status"] = "SUCCESS"
  result_dict["message"] = "追加したオブジェクトをdataキーに格納して返却します"
  result_dict["data"] = data
  r.body = jsonpickle.encode(result_dict, unpicklable=False)
  return r


# GETメソッド
# 複数のデータを取得
# AngularJS query()
@get('/rest/users')
@get('/rest/users/')
def query_handler():
  """一覧を返却します"""
  # 戻り値となる辞書型データ
  result_dict = {}
  result_dict["status"] = "SUCCESS"  # or ERROR
  result_dict["message"] = "usersキーに配列を入れて一覧を返却します"
  result_dict["users"] = db.all()

  r = http_response(status=200)
  r.body = jsonpickle.encode(result_dict, unpicklable=False)
  return r


# GETメソッド
# 単一のデータを取得
@get('/rest/users/<name>')
def get_handler(name):
  """指定された名前のオブジェクトを返却します"""
  # 戻り値となる辞書型データ
  result_dict = {}
  result_dict["status"] = "SUCCESS"  # or ERROR
  result_dict["message"] = "userキーに一致するオブジェクトを格納して返却します"
  result_dict["user"] = db.get(User.name == name)

  r = http_response(status=200)
  r.body = jsonpickle.encode(result_dict, unpicklable=False)
  return r


# PUTメソッド
# データを修正
@put('/rest/users/<oldname>')
def update_handler(oldname):
  """渡された名前をアップデートします"""
  # 戻り値となる辞書型データ
  result_dict = {}
  result_dict["status"] = "SUCCESS"  # or ERROR
  result_dict["message"] = ""  # メッセージ文字列

  try:
    # JSONデータを取り出す
    try:
      data = bottle.request.json
    except Exception:
      raise ValueError

    # newNameキーの値を取り出す
    try:
      newname = data.get("newName", "")
      if not name_pattern.match(newname):
        raise ValueError
    except (TypeError, KeyError):
      raise ValueError

    # oldnameが存在するか、確認する
    if db.get(User.name == oldname) is None:
      raise KeyError(404)

    # newnameが存在するか、確認する
    if db.get(User.name == newname):
      raise KeyError(409)

    # データベースをアップデートする
    try:
      with db_lock:
        db.update({'name': newname}, User.name == oldname)
    except Exception:
      raise ValueError

  except ValueError:
    r = http_response(status=400)
    result_dict["status"] = "ERROR"
    result_dict["message"] = "キーの書式エラー"
    result_dict["data"] = data
    r.body = jsonpickle.encode(result_dict, unpicklable=False)
    return r
  except KeyError as e:
    r = http_response(status=e.args[0])
    result_dict["status"] = "ERROR"
    result_dict["message"] = "不正なキーが指定されています"
    result_dict["data"] = data
    r.body = jsonpickle.encode(result_dict, unpicklable=False)
    return r

  # 200を返す
  r = http_response(status=200)
  result_dict["status"] = "SUCCESS"
  result_dict["message"] = "userキーに更新したオブジェクトを返却します"
  result_dict["user"] = db.get(User.name == newname)
  r.body = jsonpickle.encode(result_dict, unpicklable=False)
  return r


# DELETEメソッド
@delete('/rest/users/<name>')
def delete_handler(name):
  """指定した名前のオブジェクトを削除します"""
  # 戻り値となる辞書型データ
  result_dict = {}
  result_dict["status"] = "SUCCESS"  # or ERROR
  result_dict["message"] = ""  # メッセージ文字列

  try:
    # nameが存在するか、確認します
    if db.get(User.name == name) is None:
      raise KeyError

    # データベースから削除します
    try:
      with db_lock:
        db.remove(User.name == name)
    except Exception:
      raise ValueError

  except ValueError:
    r = http_response(status=400)
    result_dict["status"] = "ERROR"
    result_dict["message"] = "データベースから削除ができないデータです"
    result_dict["data"] = name
    r.body = jsonpickle.encode(result_dict, unpicklable=False)
    return r
  except KeyError:
    r = http_response(status=404)
    result_dict["status"] = "ERROR"
    result_dict["message"] = "パラメータエラー, 存在しない値が指定されています"
    result_dict["name"] = name
    r.body = jsonpickle.encode(result_dict, unpicklable=False)
    return r

  r = http_response(status=200)
  result_dict["message"] = "削除したnameを返却します"
  result_dict["name"] = name
  r.body = jsonpickle.encode(result_dict, unpicklable=False)
  return r


#
# bottleの共通コードです。
#

def http_response(status=200):
  """ヘッダを調整したHTTPResponseオブジェクトを返却します"""
  #
  # Python2と3で文字列の扱いが違うため、ここの処理はややこしい
  # set_header()のキー部分はASCIIを前提としている
  # Python2 + __future__ の場合には、接頭辞bを付ける必要がある
  #
  r = HTTPResponse(status=status)
  r.set_header('Content-Type', 'application/json')
  r.set_header('Cache-Control', 'no-cache')
  r.set_header('Access-Control-Allow-Origin', '*')
  r.set_header('Access-Control-Allow-Methods', 'PUT, GET, POST, DELETE, OPTIONS')
  r.set_header('Access-Control-Allow-Headers', 'Authorization, Origin, Accept, Content-Type, X-Requested-With')
  return r


@route('/', method='OPTIONS')
@route('/<path:path>', method='OPTIONS')
def options_handler():
  """OPTIONメソッドで確認を受けた時は、ボディ部を空っぽにしたレスポンスを返します"""
  r = http_response(status=200)
  return r


@route('/favicon.ico')
def favicon():
  """./static/site/img/favicon.icoを用意すればブラウザにfaviconが表示されます"""
  return static_file('favicon.ico', root=here('./static/site/img'))


@route('/')
@route('/index.htm')
@route('/index.html')
def index():
  """トップページ(index)を返却します"""
  return static_file('index.html', root=here('.'))


@route('<:re:.*/static/><path:path>')
def server_static(path):
  """URL内に/static/が入っていたら、./staticをルートとしてファイルを返却します"""
  return static_file(path, root=here('./static'))

# /staticに存在しないURLを踏むと、404が返る
# /staticを含まないURLを踏むと、405が返る

ERROR_MESSAGE = {
  400: "リクエストの内容が不正です",
  401: "認証されていません",
  403: "リソースに対するアクセス許可がありません(認証以外)",
  404: "リソースが存在しません",
  405: "指定されたURLに対するHTTP動詞は許可されていません",
  409: "競合が発生しています",
  412: "リクエストで指定された条件を満たしません",
  500: "サーバで障害が発生しました",
  504: "過負荷やメンテナンス等により一時的に処理ができない状態です"
}


@bottle.error(400)
@bottle.error(401)
@bottle.error(403)
@bottle.error(404)
@bottle.error(405)
@bottle.error(409)
@bottle.error(412)
@bottle.error(500)
@bottle.error(504)
def show_error(error):
  """カスタマイズしたエラーページを表示します"""
  message = ERROR_MESSAGE.get(error.status_code, "")
  return template("error.tpl", status=error.status, url=bottle.request.url, message=message)



def main():
  """HTTPサーバを起動します"""

  # 自分の端末のみならlocalhostでよい
  # 外部から接続を受けるなら 0.0.0.0 にする
  BOTTLE_HOSTNAME = "localhost"
  BOTTLE_PORT = 8000

  if __server__ == "gevent":
    print("geventを使ってサーバを起動します")
    print("http://{0}:{1}/".format(BOTTLE_HOSTNAME, BOTTLE_PORT))
    server = WSGIServer((BOTTLE_HOSTNAME, BOTTLE_PORT), bottle.default_app(), handler_class=WebSocketHandler)
    try:
      server.serve_forever()
    except KeyboardInterrupt:
      # サーバ終了時のクリーンナップはここで実行
      pass
  else:
    server = bottle.run(host=BOTTLE_HOSTNAME, port=BOTTLE_PORT, debug=True, reloader=True)
    sys.exit(0)

if __name__ == '__main__':
  main()
