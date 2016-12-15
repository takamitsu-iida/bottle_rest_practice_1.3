// 名前空間を定義する
(function() {
  // このthisはグローバル空間
  this.iida = (function() {
    // モジュール名の定義
    var moduleName = 'iida.app';

    // ヒアドキュメント経由で静的データを取り込む場合、テキストデータをiida.heredoc配下にぶら下げる
    var heredoc = {};

    // 公開するオブジェクト
    return {
      moduleName: moduleName,
      heredoc: heredoc
    };
  })();
})();
