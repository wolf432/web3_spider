module.exports = {
  apps : [{
    name: "web3_qtc_sync_content",
    script: "sync_content.py",
    interpreter: "/home/ubuntu/miniconda3/envs/web3_spider/bin/python",
    log_file: "logs/pm2_qtc.log",
    out_file: "logs/pm2_qtc_out.log",
    error_file: "logs/pm2_qtc_error.log",
    merge_logs: true,
  }]
};
