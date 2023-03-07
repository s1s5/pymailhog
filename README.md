cloned from https://bitbucket.org/symfo/pymailhog/src/master/

[MailHog](https://github.com/mailhog/MailHog)は非常に便利なツールなのですが、文字コードにiso-2022-jpを指定すると文字化けし、正しく表示されません。

iso-2022-jpが正しく表示できるようPyMailHogを作成しました。  
Python3で動作する同様の機能を持ったツールです。

紹介ページはこちら  
https://symfoware.blog.fc2.com/blog-entry-2408.html

## Overview

* PyMailHogは1つのファイルだけで動作します
* stmpサーバーとwebサーバーが同時に起動します


## Getting started

zipapp形式で作成していますので、PyMailHog単体1あフィルのみで実行できます。

* ダウンロードリンクから最新版を取得
* Pythonコマンドに続いてダウンロードしたファイル名を指定し実行

```
$ python3 PyMailHog-{version]}
```

Linux系OSでは、実行権限を付与した後そのまま実行も可能です。  
python3 PyMailHog-{version}としても起動します。  

```
$ chmod +x PyMailHog-{version}
$ ./PyMailHog-{version}
```

デフォルトで  
SMTPサーバーポートは1025  
HTTPサーバーポートは8025  
で起動します。

オプション  
-spまたは--smtpportでsmtpポート  
-hpまたは--httpportでhttpポート  
を指定できます。

## Release note

### 0.0.4
2022-12-24

* cssフレームワークとしてpicnic cssを導入
* .eml形式でメールをダウンロードする機能を追加
* jquery を削除
* bootstrapを削除

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


