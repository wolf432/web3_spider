module.exports = {
  apps : [{
    name: "web3_twitter_latest_content",
    script: "latest_content",
    interpreter: "/home/ubuntu/miniconda3/envs/web3_spider/bin/python",
    log_file: "logs/pm2_twitter.log",
    out_file: "logs/pm2_twitter_out.log",
    error_file: "logs/pm2_twitter_error.log",
    merge_logs: true,
  }]
};
