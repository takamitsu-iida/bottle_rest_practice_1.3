/* global angular, iida */
(function() {
  // モジュール名iidaはiida.startup.jsでグローバル変数として定義している
  var moduleName = iida.moduleName;

  // AngularJSのモジュールを登録
  angular.module(moduleName, [
    'ngResource',
    'ngAnimate',
    'ui.bootstrap',
    'ui.router'
  ]);

  // $log設定
  // $log.debug();によるデバッグメッセージの表示・非表示設定
  angular.module(moduleName).config(['$logProvider', function($logProvider) {
    $logProvider.debugEnabled(false);
  }]);

  // ディレクティブ定義
  // 戻るボタン <back></back>
  angular.module(moduleName).directive('back', ['$window', function($window) {
    return {
      restrict: 'E',
      replace: true,
      template: '<a><button type="button" class="btn btn-primary">戻る</button></a>',
      link: function(scope, elem, attrs) {
        elem.bind('click', function() {
          $window.history.back();
        });
      }
    };
  }]);

  // コントローラ 'navController'
  angular.module(moduleName).controller('navController', [function() {
    var ctrl = this;
    ctrl.title = 'bottle.rest';
    ctrl.links = [{
      a: 'pj1',
      href: '#/'
    }, {
      a: 'pj2',
      href: '#/'
    }, {
      a: 'pj3',
      href: '#/'
    }];
  }]);

  // UI Router
  // ルーティング設定
  angular.module(moduleName).config(['$stateProvider', '$urlRouterProvider', function($stateProvider, $urlRouterProvider) {
    // 一致しないURLは全て/に飛ばす
    $urlRouterProvider.otherwise('/');

    // ステートとURLを対応付ける
    $stateProvider.state('top', {
      url: '/',
      templateUrl: 'index.tpl',
      controller: 'topController',
      controllerAs: 'topCtrl'
    }).state('rest', {
      url: '/rest',
      templateUrl: 'rest.tpl',
      controller: 'restController',
      controllerAs: 'restCtrl'
    }).state('setting', {
      url: '/setting',
      templateUrl: 'setting.tpl',
      controller: 'settingController',
      controllerAs: 'settingCtrl'
    });
  }]);

  // topController
  // タイトルや説明書きはここに記載する
  angular.module(moduleName).controller('topController', [function() {
    var ctrl = this;
    ctrl.title = 'REST API';
    ctrl.description = 'Python bottleフレームワークのREST APIをAngularJSで叩くテストです。';
    ctrl.date = '2016/07/21';
    ctrl.author = 'Takamitsu IIDA';
    ctrl.mail = 'iida@jp.fujitsu.com';
  }]);

  // dataサービス
  // 'dataService'
  angular.module(moduleName).service('dataService', [function() {
    var svc = this;

    // サービスとして提供するオブジェクト
    svc.names = [];
  }]);

  // REST APIを叩く$resourceファクトリ
  angular.module(moduleName).factory('userResource', ['$resource', '$location', function($resource, $location) {
    // 標準で定義済みのアクション query, get, save, delete
    // 個別定義のアクション update
    return $resource(
      // 第一引数はURL
      // :nameはプレースホルダなので、/rest/users/iidaのようなURLに変換される
      // 'http://localhost:5000/names/:name',
      $location.protocol() + '://' + $location.host() + ':' + $location.port() + '/rest/users/:name', {
        // 第二引数はデフォルトパラメータ
        // オブジェクト内の同名のキーの値に置き換えられる
        name: '@name'
      }, {
        // 第三引数はアクションの定義
        query: {
          // 複数のデータを取得
          method: 'GET',
          isArray: false // デフォルトはtrue
        },
        get: {
          // 単一のデータを取得
          method: 'GET'
        },
        save: {
          // 新規データを登録
          method: 'POST'
        },
        delete: {
          // 既存データを削除
          method: 'DELETE'
        },
        update: {
          // データを修正
          method: 'PUT'
        }
      }
    );
  }]);

  // コントローラ 'restController'
  angular.module(moduleName).controller('restController', ['dataService', 'settingParamService', 'userResource', function(dataService, settingParamService, userResource) {
    var ctrl = this;
    ctrl.title = 'RESTテスト';
    angular.extend(ctrl, dataService);
    angular.extend(ctrl, settingParamService);

    // query()
    // HTTP GET
    // 複数のデータを取得
    ctrl.query = function() {
      userResource
        .get()
        .$promise
        .then(function(data) {
          console.log(data);
          ctrl.users = data.users;
        })
        .catch(function(data, status) {
          console.log(data);
        });
    };

    // ビューの<input>と紐付けたユーザ名
    ctrl.getParams = {
      name: '',
      message: ''
    };

    // get()
    // HTTP GET
    // 単一のデータを取得
    ctrl.get = function() {
      var param = {
        name: ctrl.getParams.name
      };

      userResource
        .get(param)
        .$promise
        .then(function(user) {
          ctrl.user = user;
        })
        .catch(function(data, status) {
          console.log('error');
        });
    };

    // ビューの<input>と紐付けた新規ユーザ名
    ctrl.saveParams = {
      newUserName: '',
      message: '保存できるかな？'
    };

    // save()
    // HTTP POST
    // 新規データを登録
    ctrl.save = function() {
      var param = {
        name: ctrl.saveParams.newUserName,
        message: '新規ユーザ'
      };

      userResource
        .save(param)
        .$promise
        .then(function(data) {
          console.log(data);
          ctrl.query();
        })
        .catch(function(obj, status) {
          console.log(obj);
        })
        .finally(function() {
          ctrl.newUserName = '';
        });
    };

    // ビューの<input>と紐付けた既存ユーザ名、変更名
    ctrl.updateParams = {
      oldUserName: '',
      newUserName: '',
      message: '変更できるかな？'
    };

    // update()
    // HTTP PUT
    // データを更新
    // GETメソッド以外のアクションを実行するときはprefixに「$」をつける
    ctrl.update = function() {
      var param = {
        name: ctrl.updateParams.oldUserName,
        newName: ctrl.updateParams.newUserName
      };

      userResource
        .update(param)
        .$promise
        .then(function(data) {
          console.log(data);
        })
        .catch(function(data, status) {
          console.log(data);
        });
    };

    // ビューの<input>と紐付けた削除するユーザ名
    ctrl.deleteParams = {
      deleteUserName: ''
    };

    // delete()
    // HTTP DELETE
    // データを削除
    ctrl.delete = function() {
      var param = {
        name: ctrl.deleteParams.deleteUserName
      };

      userResource
        .delete(param)
        .$promise
        .then(function(data) {
          console.log(data);
        })
        .catch(function(data, status) {
          console.log(data);
        });
    };
  }]);

  // サービス 'settingParamService'
  angular.module(moduleName).service('settingParamService', [function() {
    var svc = this;

    // 設定条件をまとめたオブジェクト
    svc.settingParam = {
      // ng-ifでこれをバインドすれば、デバッグ目的で入れている要素の表示・非表示が切り替わる
      debug: false,
      // コンフィグを表示するかどうか
      showConf: true
    };
  }]);

  // コントローラ 'settingController'
  angular.module(moduleName).controller('settingController', ['settingParamService', function(settingParamService) {
    var ctrl = this;
    ctrl.title = '動作設定';
    angular.extend(ctrl, settingParamService);
  }]);

  angular.module(moduleName).controller('_ModalDemoCtrl', ['$uibModalInstance', 'items', function($uibModalInstance, items) {
    // $uibModalInstanceはインジェクト可能な特別なオブジェクトで、モーダルインスタンスを表す
    // itemsは親側でresolveしたもので、ローカル変数として渡すときに使う
    var ctrl = this;

    ctrl.items = items;

    ctrl.selected = {
      item: '' // 先頭の値を初期値に使うなら、ctrl.items[0]
    };

    ctrl.ok = function() {
      $uibModalInstance.close(ctrl.selected.item);
    };

    ctrl.cancel = function() {
      $uibModalInstance.dismiss('cancel');
    };
  }]);

  angular.module(moduleName).controller('ModalProgressCtrl', ['$uibModal', '$timeout', function($uibModal, $timeout) {
    var ctrl = this;

    // モーダル表示のインスタンス
    ctrl.modalInstance = null;

    // show()で開く
    ctrl.show = function() {
      ctrl.modalInstance = $uibModal.open({
        animation: true,
        size: 'md',
        templateUrl: 'modal-progress-tmpl',
        controller: '_ModalProgressCtrl',
        controllerAs: 'ctrl', // テンプレートの中では ctrl として利用する
        bindToController: false,
        backdrop: 'static' // or false or 'static',
      });

      // 3秒後に閉じるテスト
      $timeout(function() {
        ctrl.close();
      }, 3000);
    };

    ctrl.close = function() {
      ctrl.modalInstance.close();
    };
  }]);

  angular.module(moduleName).controller('_ModalProgressCtrl', ['$uibModalInstance', function($uibModalInstance) {
    var ctrl = this;
    ctrl.ok = function() {
      $uibModalInstance.close();
    };
  }]);
})();
