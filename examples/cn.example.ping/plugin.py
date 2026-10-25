import json
import sys
import time

# 最小可用插件：演示协议，不真的连节点。
# 真做测速时把 test 分支换成"对节点发一次请求并计时"。


def reply(request_id, result=None, error=None):
    message = {"id": request_id}
    if error is not None:
        message["error"] = {"message": error}
    else:
        message["result"] = result
    sys.stdout.write(json.dumps(message, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def log(text):
    # 没有 id 的行会被客户端当日志打印
    sys.stdout.write(json.dumps({"method": "log", "params": {"message": text}}, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main():
    log("示例插件已启动")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except ValueError:
            log("收到非 JSON 行，已忽略")
            continue

        method = request.get("method")
        params = request.get("params") or {}
        request_id = request.get("id")

        if method == "hello":
            reply(request_id, {"apiVersion": "1.0"})
        elif method == "test":
            nodes = params.get("nodes") or []
            results = []
            for index, node in enumerate(nodes):
                started = time.time()
                # 模拟：每条线路 20~120ms
                delay = 20 + (index * 17) % 100
                time.sleep(delay / 1000.0)
                results.append({
                    "node": node,
                    "delayMs": int((time.time() - started) * 1000),
                    "mbps": 100 + index * 5,
                })
            reply(request_id, {"results": results})
        elif method == "shutdown":
            reply(request_id, {})
            break
        else:
            reply(request_id, error="不支持的方法：" + str(method))


if __name__ == "__main__":
    main()
