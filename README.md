[MailHog](https://github.com/mailhog/MailHog)は非常に便利なツールなのですが、文字コードにiso-2022-jpを指定すると文字化けし、正しく表示されません。

iso-2022-jpが正しく表示できるようPyMailHogを作成しました。  
Python3で動作する同様の機能を持ったツールです。

紹介ページはこちら  
https://symfoware.blog.fc2.com/blog-entry-2408.html

## Overview

* PyMailHogは1つのファイルだけで動作します
* stmpサーバーとwebサーバーが同時に起動します


## Getting started

* ダウンロードリンクから最新版を取得
* 実行権限を付与
* 実行

```
$ chmod +x PyMailHog-{version}
$ ./PyMailHog-{version}
```

または、python3 PyMailHog-{version}としても起動します。　　
```
$ python3 PyMailHog-{version]}
```
SMTPサーバーポートは1025  
HTTPサーバーポートは8025  
で起動します。

## Release note

### 0.0.3
2022-12-18
* smtpサーバーを内蔵サーバーから自作サーバーに変更
* httpサーバーを内蔵サーバーから自作サーバーに変更
* jquery 3.4 から 3.6.2へ変更
* vue.js 2.6.10 から 2.7.11へ変更
* filesize.js 3.1.2 から 9.0.11へ変更
* --smtpportオプションでsmtpポートを指定可能(デフォルト1025)
* --httpportオプションでhttpポートを指定可能(デフォルト8025)

### 0.0.2
2019-11-25
* jquery 1.11 から 3.4へ変更
* フレームワークをangular.js から vue.jsへ変更

### 0.0.1
2019-11-24  
* 初回リリース
* MailHogのUIをそのまま移植


