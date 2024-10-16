module.exports = {
    apps: [
        {
            name: "web3_ann_binance",
            script: "binance.py",
            interpreter: "/root/miniconda3/envs/web3_spider/bin/python"
        },
        {
            name: "web3_ann_okex",
            script: "okex.py",
            interpreter: "/root/miniconda3/envs/web3_spider/bin/python"
        }
    ]
};
