# 使用说明

## 描述
用来抓取web3的信息，目前支持如下平台：
- twiter

## 使用方法

库的开发是基于**Python**版本:3.10.14。虚拟环境管理用的是**conda**。

### 创建新的环境

```shell

conda create -n web3_spider python=3.10.14

conda activate web3_spider

```
### 安装依赖库

   ```shell
   pip install -r requirements.txt
   ```

### 安装 playwright浏览器驱动

   ```shell
   playwright install
   ```