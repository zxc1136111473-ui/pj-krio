(function () {
  const vscode = acquireVsCodeApi();
  const $ = (id) => document.getElementById(id);
  const log = $("log");
  const promptEl = $("prompt");
  const modelEl = $("model");
  const originEl = $("origin");
  const usageEl = $("usage");
  const btnSend = $("btnSend");
  const agentEl = $("agentMode");

  let sending = false;
  let currentAssistant = null;
  let assistantText = "";

  function addMsg(kind, label, text) {
    const div = document.createElement("div");
    div.className = "msg " + kind;
    if (label) {
      const l = document.createElement("div");
      l.className = "label " + kind;
      l.textContent = label;
      div.appendChild(l);
    }
    if (text !== undefined && text !== null && text !== "") {
      const span = document.createElement("span");
      // 代码块渲染：``` 围栏块 → 等宽样式 + 复制按钮
      const fences = String(text).split(/```/);
      if (fences.length > 1) {
        for (let i = 0; i < fences.length; i++) {
          if (i % 2 === 0) {
            if (fences[i]) {
              const s = document.createElement("span");
              s.textContent = fences[i];
              span.appendChild(s);
            }
          } else {
            const codeText = fences[i].replace(/^[a-zA-Z0-9_+-]*\r?\n/, "");
            const pre = document.createElement("pre");
            pre.className = "codeblock";
            pre.textContent = codeText;
            const btn = document.createElement("button");
            btn.className = "copybtn";
            btn.textContent = "复制";
            btn.addEventListener("click", () => {
              navigator.clipboard.writeText(codeText).catch(() => {});
              btn.textContent = "已复制";
              setTimeout(() => (btn.textContent = "复制"), 1200);
            });
            pre.appendChild(btn);
            span.appendChild(pre);
          }
        }
      } else {
        span.textContent = text;
      }
      div.appendChild(span);
    }
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;
    return div;
  }

  function setSending(v) {
    sending = v;
    btnSend.disabled = v;
    btnSend.textContent = v ? "…" : "发送";
    const stop = $("btnStop");
    if (stop) stop.classList.toggle("hidden", !v);
  }

  function send() {
    if (sending) return;
    const prompt = promptEl.value.trim();
    if (!prompt) return;
    promptEl.value = "";
    // 「你是谁」这类问题服务端只会自称 Amazon Q，本地直接答，不浪费请求
    if (/你是(什么|哪个)?模型|what model|who are you|你是谁/i.test(prompt) && prompt.length < 40) {
      addMsg("user", "你", prompt);
      addMsg(
        "assistant",
        "Q · " + (modelEl.value || "") + " [" + (originEl.value || "") + "]",
        "底层模型是 " +
          (modelEl.value || "claude-opus-5") +
          "（origin=" +
          (originEl.value || "CONSOLE") +
          "）。服务端人设锁死成 Amazon Q，所以问「你是谁」只会说 AWS 套话，改不了。写代码请保持 Agent 勾上，直接下任务（改文件/跑命令）。"
      );
      return;
    }
    if (/调用什么工具|有什么工具|what tools|which tools|能用(哪些|什么)工具|你可以调用/i.test(prompt) && prompt.length < 80) {
      addMsg("user", "你", prompt);
      addMsg(
        "assistant",
        "Q · Agent 本地工具",
        "Agent 勾上后，插件在本地执行这些工具（不是 Amazon Q 自带的 AWS 工具）：\n" +
          "• write_file {path, content} — 写/覆盖工作区文件\n" +
          "• replace_in_file {path, old, new} — 替换文件片段\n" +
          "• read_file {path} — 读文件\n" +
          "• list_dir {path} — 列目录\n" +
          "• search_content {pattern, path?} — 搜索内容\n" +
          "• run_command {command} — 在工作区跑 shell（仅桌面）\n\n" +
          "不要问工具清单，直接下任务。例如：在 src/ 新建 hello.py，写 fibonacci 并用 python3 跑一下。"
      );
      return;
    }
    setSending(true);
    vscode.postMessage({
      type: "send",
      prompt: prompt,
      model: modelEl.value,
      origin: originEl.value,
      agent: agentEl.checked,
    });
  }

  promptEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      send();
    } else if (e.key === "Escape") {
      promptEl.value = "";
    }
  });
  btnSend.addEventListener("click", send);
  $("btnStop").addEventListener("click", () => vscode.postMessage({ type: "stop" }));
  modelEl.addEventListener("change", () =>
    vscode.postMessage({ type: "setModel", model: modelEl.value })
  );
  $("thinkMode").addEventListener("change", () =>
    vscode.postMessage({ type: "setThinkMode", mode: $("thinkMode").value })
  );
  originEl.addEventListener("change", () =>
    vscode.postMessage({ type: "setOrigin", origin: originEl.value })
  );
  $("btnUsage").addEventListener("click", () => vscode.postMessage({ type: "usage" }));
  $("btnClear").addEventListener("click", () => {
    log.innerHTML = "";
    currentAssistant = null;
    assistantText = "";
  });
  $("btnNewSession").addEventListener("click", () => vscode.postMessage({ type: "newSession" }));
  $("sessionSel").addEventListener("change", () => {
    if ($("sessionSel").value) vscode.postMessage({ type: "switchSession", id: $("sessionSel").value });
  });

  function renderSessions(m) {
    const sel = $("sessionSel");
    sel.innerHTML = "";
    for (const s of m.list) {
      const o = document.createElement("option");
      o.value = s.id;
      o.textContent = (s.name || "会话") + " (" + s.count + ")";
      sel.appendChild(o);
    }
    sel.value = m.currentId;
  }

  function renderHistory(messages) {
    log.innerHTML = "";
    currentAssistant = null;
    assistantText = "";
    for (const msg of messages || []) {
      if (msg.role === "user") addMsg("user", "你", msg.text);
      else if (msg.role === "assistant") addMsg("assistant", "Q", msg.text);
      else if (msg.role === "tool") {
        const icons = { read: "📖", write: "✏️", run: "▶", agent: "🤖" };
        const labels = { read: "读", write: "写", run: "运行", agent: "子代理" };
        const icon = icons[msg.kind] || "🔧";
        addMsg("system", `${icon} ${labels[msg.kind] || "工具"}`, msg.text.replace(/^[✓✗] \[[a-z]+\] /, ""));
      } else if (msg.role === "error") addMsg("error", "错误", msg.text);
    }
  }

  $("btnToken").addEventListener("click", () => {
    $("tokenInput").focus();
    $("tokenRow").scrollIntoView({ block: "nearest" });
  });
  $("btnTokenSave").addEventListener("click", () => {
    const t = $("tokenInput").value.trim();
    if (!t) return;
    vscode.postMessage({ type: "setToken", token: t });
    $("tokenInput").value = "";
  });

  window.addEventListener("message", (ev) => {
    const m = ev.data;
    switch (m.type) {
      case "needToken":
        $("tokenInput").focus();
        addMsg("error", "令牌", "还没令牌：在上方输入框粘贴 aor/aoa 后点「保存令牌」。已登录过 Kiro 桌面的会自动读 ~/.aws/sso/cache/kiro-auth-token.json。");
        break;
      case "sessions":
        renderSessions(m);
        break;
      case "history":
        renderHistory(m.messages);
        break;
      case "tokenState":
        $("tokenHint").textContent = "令牌：" + (m.source || (m.set ? "已就绪" : "未设置"));
        break;
      case "config":
        modelEl.innerHTML = "";
        for (const v of m.models) {
          const o = document.createElement("option");
          o.value = v;
          o.textContent = v;
          modelEl.appendChild(o);
        }
        modelEl.value = m.defaultModel || m.models[0];
        originEl.innerHTML = "";
        for (const v of m.origins) {
          const o = document.createElement("option");
          o.value = v;
          o.textContent = v;
          originEl.appendChild(o);
        }
        originEl.value = m.defaultOrigin || m.origins[0];
        if (m.thinkMode) $("thinkMode").value = m.thinkMode;
        break;
      case "setModel":
        if (m.model && modelEl.querySelector(`option[value="${m.model}"]`)) {
          modelEl.value = m.model;
        }
        break;
      case "setOrigin":
        if (m.origin && originEl.querySelector(`option[value="${m.origin}"]`)) {
          originEl.value = m.origin;
        }
        break;
      case "user": {
        const d = addMsg("user", m.agent ? "任务(Agent)" : "你", m.text);
        // 重发按钮
        const btn = document.createElement("button");
        btn.className = "act";
        btn.textContent = "重发";
        btn.addEventListener("click", () => {
          promptEl.value = m.text;
          send();
        });
        d.appendChild(btn);
        break;
      }
      case "agent-start":
        addMsg("system", "Agent", "任务开始 · " + (m.model || "") + " [" + (m.origin || "") + "]：\n" + m.task);
        break;
      case "agent-round":
        break; // 不再显示轮数
      case "agent-think":
        addMsg("assistant", "Q", m.text);
        break;
      case "tool": {
        const icons = { read: "📖", write: "✏️", run: "▶", agent: "🤖" };
        const labels = { read: "读", write: "写", run: "运行", agent: "子代理" };
        const icon = icons[m.kind] || "🔧";
        const label = labels[m.kind] || "工具";
        const d = addMsg(
          m.ok ? "system" : "error",
          `${icon} ${label} · ${m.name}${m.ok ? " ✓" : " ✗"}`,
          m.brief + "\n" + m.result
        );
        // 写工具加撤销按钮
        if (m.kind === "write" && m.ok) {
          let path = "";
          try {
            path = JSON.parse(m.brief).path || "";
          } catch (_) {}
          if (path) {
            const undo = document.createElement("button");
            undo.className = "act";
            undo.textContent = "↩ 撤销";
            undo.addEventListener("click", () => vscode.postMessage({ type: "undoWrite", path: path }));
            d.appendChild(undo);
          }
        }
        break;
      }
      case "agent-done":
        setSending(false);
        addMsg("meta", "Agent 完成", m.text || "(任务自动暂停)");
        break;
      case "prefill":
        promptEl.value = m.prompt;
        break;
      case "status":
        addMsg("system", "状态", m.text);
        break;
      case "assistant-start":
        currentAssistant = addMsg("assistant", "Q · " + (m.model || "") + " [" + (m.origin || "") + "]", "");
        assistantText = "";
        break;
      case "delta":
        if (currentAssistant) {
          const span = currentAssistant.querySelector("span") || currentAssistant;
          span.textContent += m.text;
          assistantText += m.text;
          log.scrollTop = log.scrollHeight;
        }
        break;
      case "assistant-done":
        setSending(false);
        if (currentAssistant && assistantText.trim()) {
          const row = document.createElement("div");
          row.className = "actions";
          const mk = (label, mode) => {
            const b = document.createElement("button");
            b.className = "act";
            b.textContent = label;
            b.addEventListener("click", () => {
              const snapshot = assistantText;
              vscode.postMessage({ type: "insertAnswer", mode: mode, text: snapshot });
            });
            return b;
          };
          row.appendChild(mk("插入", "cursor"));
          row.appendChild(mk("替换选中", "replace"));
          row.appendChild(mk("代码块插入", "codeblock"));
          currentAssistant.appendChild(row);
        }
        addMsg(
          "meta",
          "",
          "HTTP " + m.meta.http + " · " + m.meta.seconds + "s · 事件 " + m.meta.events +
            (m.meta.modelIds && m.meta.modelIds.length ? " · 流内 modelId: " + m.meta.modelIds.join(", ") : "") +
            (m.meta.requestId ? " · req " + m.meta.requestId : "")
        );
        break;
      case "error":
        setSending(false);
        addMsg("error", "错误", m.msg);
        break;
      case "usage":
        if (m.data && m.data.error) {
          usageEl.textContent = m.data.error.slice(0, 40);
        } else if (m.data) {
          usageEl.textContent =
            "额度 " + (m.data.usageP ?? m.data.usage ?? "?") + " / " + (m.data.limit ?? "?") +
            (m.data.title ? " · " + m.data.title : "");
        }
        break;
    }
  });

  vscode.postMessage({ type: "ready" });
})();
