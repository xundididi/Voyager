
# 测试是否存在WAF的PAYLOAD
IPS_WAF_CHECK_PAYLOAD = "AND 1=1 UNION ALL SELECT 1,NULL,'<script>alert(\"XSS\")</script>',table_name FROM information_schema.tables WHERE 2>1--/**/; EXEC xp_cmdshell('cat ../../../etc/passwd')#"

IPS_WAF_CHECK_TIMEOUT = 3

DYNAMICITY_BOUNDARY_LENGTH = 20

# 网页对比度 高于0.95就任务两个页面正常
UPPER_RATIO_BOUND = 0.95

# 正常HTTP请求的user-agent
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:71.0) Gecko/20100101 Firefox/71.0"

# 黑客请求的user-agent
HACKER_AGENT = "sqlmap/1.3.12.28#dev (http://sqlmap.org)"
