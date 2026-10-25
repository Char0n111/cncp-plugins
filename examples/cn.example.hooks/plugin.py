import json
import sys

# 钩子插件的最小例子：只做一件事 —— 把每次生命周期事件记一行日志。
#
# 它同时也是**安卓端插件引擎的验收工具**：
#   装上 → 进插件页应该看到「已就绪」→ 连一次网络 → 回到插件页，
#   运行日志里应该依次出现 connect.before / connect.after；
#   断开之后再来看，应该多一行 disconnect。
#
# 注意这里**没有**任何"连接成功就改节点/改配置"的动作：钩子能做的远比这多，
# 但示例只演示协议本身，不演示怎么干预用户连接。


def reply(request_id, result=None, error=None):
    message = {"id": request_id}
    if error is not None:
        message["error"] = {"message": error}
    else:
        message["result"] = result
    sys.stdout.write(json.dumps(message, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def log(text):
    # 没有 id 的行会被客户端当日志打印（和 Windows 端一致）
    sys.stdout.write(json.dumps({"method": "log", "params": {"message": text}}, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def describe(host):
    # host 里只有这五个字段：hostVersion / connected / selectedNodeName /
    # mode / connectionMode。**没有**节点地址、密码、UUID —— 这是硬约束。
    return "客户端 {0} · 节点 {1} · 模式 {2} · 连接方式 {3}".format(
        host.get("hostVersion", "?"),
        host.get("selectedNodeName") or "(自动选择)",
        host.get("mode", "?"),
        host.get("connectionMode", "?"),
    )


def main():
    log("示例钩子插件已启动")

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
        elif method == "hook":
            event = params.get("event")
            host = params.get("host") or {}
            log("钩子 {0}：{1}".format(event, describe(host)))
            # 钩子不需要回内容，但回一个空 result 能让宿主的等待立刻结束
            #（不回也不会出错，只是要等宿主 5 秒超时）。
            reply(request_id, {})
        elif method == "shutdown":
            reply(request_id, {})
            break
        else:
            reply(request_id, error="不支持的方法：" + str(method))


if __name__ == "__main__":
    main()
