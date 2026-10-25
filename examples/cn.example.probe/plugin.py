"""环境探测插件：启动时把"插件在本机到底能干什么"写进运行日志。

===========================================================================
为什么要专门做一个演示插件
===========================================================================
以前这里演示的是"权限有没有被沙箱拦住"。R-044 之后沙箱去掉了，插件与客户端
同权限运行 —— 于是这个插件改成回答另一个问题：**这个插件实际能碰到什么**。

用户在界面上看到的"权限声明"只是插件自报的清单，不再影响行为；真正决定它能做
什么的是"运行环境"（安卓上有 Chaquopy 所以能 import java；桌面 CPython 没有）。
把这三项打印出来，用户/插件作者就不用猜。
"""

import json
import os
import sys
import tempfile


def reply(request_id, result=None, error=None):
    message = {"id": request_id}

    if error is not None:
        message["error"] = {"message": error}
    else:
        message["result"] = result

    sys.stdout.write(json.dumps(message, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def log(text):
    sys.stdout.write(
        json.dumps({"method": "log", "params": {"message": text}}, ensure_ascii=False) + "\n"
    )
    sys.stdout.flush()


def probe_network():
    try:
        import socket  # noqa: F401

        return "可以（socket 导入成功）"
    except BaseException as error:
        return "不可以（{}）".format(type(error).__name__)


def probe_files():
    # 写到插件目录**外面**：能写才说明它真的能碰本机文件。
    target = os.path.join(tempfile.gettempdir(), "cncp-probe.txt")

    try:
        with open(target, "w", encoding="utf-8") as handle:
            handle.write("probe")
    except BaseException as error:
        return "不可以（{}）".format(type(error).__name__)

    try:
        os.remove(target)
    except BaseException:
        pass

    return "可以（临时目录写入并删除成功）"


def probe_hook():
    # 碰客户端本体：安卓上是 import java（能拿到 Activity / Context）；
    # 桌面 CPython 根本没有 java 模块，所以这里失败是"环境没有"，不是"被拦住"。
    try:
        import java  # noqa: F401

        return "可以（java 导入成功）"
    except BaseException as error:
        return "不可以（{}，桌面 CPython 没有 java）".format(type(error).__name__)


def report_all():
    log("网络：" + probe_network())
    log("文件：" + probe_files())
    log("挂钩：" + probe_hook())
    log("（本版本不限制插件：以上结果反映的是**运行环境**，不是权限）")


def main():
    log("环境探测插件已启动")
    report_all()

    for line in sys.stdin:
        line = line.strip()

        if not line:
            continue

        try:
            request = json.loads(line)
        except ValueError:
            log("收到非 JSON 行，已忽略")
            continue

        request_id = request.get("id")
        method = request.get("method")

        if method == "hello":
            reply(request_id, {"apiVersion": "1.0"})
        elif method == "invoke":
            report_all()
            reply(request_id, {"ok": True, "message": "探测完成，结果见运行日志"})
        elif method == "hook":
            report_all()
            reply(request_id, {"ok": True})
        elif method == "shutdown":
            reply(request_id, {"ok": True})
            return
        else:
            reply(request_id, error="不支持的方法：{}".format(method))


if __name__ == "__main__":
    main()
