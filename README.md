# catchup_tech
情報収集用スクリプト

## Dockerイメージの作成

```bash
$ pwd
/hoge/catchup_tech
$ ls
app  docker  README.md
$ docker build --build-arg webhook='webhookxxxxx' -f docker/Dockerfile -t tech --no-cache .
```

## cronで毎朝5時に定期実行

```
$ crontab -l
0 5 * * * docker run -i tech
```
