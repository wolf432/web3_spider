module.exports = {
    apps: [
        {
            name: "web3_twitter_latest_content",
            script: "latest_content.py",
            interpreter: "/home/ubuntu/miniconda3/envs/web3_spider/bin/python",
        },
        {
            name: "web3_twitter_sync_content",
            script: "sync_user_content.py",
            interpreter: "/home/ubuntu/miniconda3/envs/web3_spider/bin/python",
        }
    ]
};
