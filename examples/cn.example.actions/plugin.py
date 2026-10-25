import json
import sys

# 演示「给客户端加功能」的最小插件。
#
# 与 cn.example.ping 的区别：那个替换的是客户端本来就有的一步（测速），
# 这个带来的是客户端本来没有的东西 —— 用户在插件窗口里能点到三个入口。
#
# 客户端只负责把入口画出来，具体做什么全在这里。所以插件想加什么功能，
# 不需要等客户端发版。


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


# 演示"借宿主的手做事"：用 call 信封问一次状态，不用 id 信封。
_next_call = [0]


def ask_snapshot():
    _next_call[0] += 1
    sys.stdout.write(json.dumps({"call": _next_call[0], "method": "snapshot", "params": {}}, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def describe_host(host):
    if not host:
        return "客户端没给状态。"

    connected = "已连接" if host.get("connected") else "未连接"
    node = host.get("selectedNodeName") or "（没选节点）"
    mode = {"rule": "规则模式", "global": "全局模式"}.get(host.get("mode"), host.get("mode") or "？")
    connection = {"system": "系统代理", "tun": "TUN", "direct": "直连"}.get(
        host.get("connectionMode"), host.get("connectionMode") or "？")

    return (
        "客户端版本：" + str(host.get("hostVersion") or "？") + "\n"
        + "状态：" + connected + "\n"
        + "当前节点：" + node + "\n"
        + "代理模式：" + mode + "\n"
        + "接管方式：" + connection
    )


def main():
    log("示例功能插件已启动")

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

        elif method == "invoke":
            action = params.get("action")
            text = params.get("input") or ""
            host = params.get("host") or {}

            if action == "show-status":
                reply(request_id, {"ok": True, "message": describe_host(host)})

            elif action == "echo":
                if not text:
                    reply(request_id, {"ok": False, "message": "输入框是空的。"})
                else:
                    reply(request_id, {"ok": True, "message": "你输入的是：" + text})

            elif action == "enabled-marker":
                state = "打开" if text == "true" else "关闭"
                reply(request_id, {"ok": True, "message": "开关现在是：" + state})

            else:
                # 客户端的菜单和插件版本可能不一致（比如插件升级了但没重启），
                # 所以不认识的动作要明确回一句，不要静默。
                reply(request_id, {"ok": False, "message": "不认识的动作：" + str(action)})

        elif method == "hook":
            # 生命周期事件。插件拿不到配置，只有状态快照。
            event = params.get("event")
            host = params.get("host") or {}
            connected = "已连接" if host.get("connected") else "未连接"
            log("钩子 " + str(event) + "，当前" + connected)

            # 需要问客户端要点什么，用 call 信封（见文档 4.11）
            reply(request_id, {})
            ask_snapshot()

        elif method == "task":
            # 周期任务：客户端到点调用，插件不要自己 sleep
            task_id = params.get("id")
            log("周期任务 " + str(task_id) + "，当前版本 " + str((params.get("host") or {}).get("hostVersion")))
            reply(request_id, {"message": "任务 " + str(task_id) + " 已完成"})

        elif method == "shutdown":
            reply(request_id, {})
            break

        else:
            # 客户端可能按能力调 hello / invoke 之外的方法；
            # 没实现的方法回错误比装作成功好排查。
            reply(request_id, error="不支持的方法：" + str(method))


if __name__ == "__main__":
    main()
