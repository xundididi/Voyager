#!/usr/bin/env bash


# 准备Python环境
git clone https://github.com/pyenv/pyenv.git ~/.pyenv
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bash_profile
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bash_profile
source ~/.bash_profile
pyenv install 3.8.1
pyenv global 3.8.1
pip install pipenv
pipenv install


# 下载所需的镜像
docker pull ap0llo/oneforall:0.0.8
docker pull ap0llo/nmap:7.80
docker pull ap0llo/dirsearh:0.3.9
docker pull al0llo/poc:xunfeng
docker pull al0llo/poc:kunpeng
docker pull mongo:4.1

# 运行数据库
docker run --rm -d -p 127.0.0.1:27017:27017 -e MONGO_INITDB_ROOT_USERNAME=root -e MONGO_INITDB_ROOT_PASSWORD=shad0wBrok3r mongo:4.1


# 初始化xunfeng镜像
docker run --rm --network="host" ap0llo/poc:xunfeng init

# 初始化kunpeng镜像
docker run --rm --network="host" ap0llo/poc:kunpeng init
