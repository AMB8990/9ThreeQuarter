(() => {
  const LS = {
    userId: "nameboard:user_id",
    userName: "nameboard:user_name",
    apiBase: "nameboard:api_base",
  };

  const API_BASE_FIXED = "http://127.0.0.1:9943/api";
  function apiBase() {
    return API_BASE_FIXED.replace(/\/$/, "");
  }

  function clearAuthMsgs() {
    ["bind_msg", "reg_msg", "log_out_msg", "create_msg"].forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.textContent = "";
    });
  }

  function identity() {
    return {
      user_id: localStorage.getItem(LS.userId) || null,
      user_name: localStorage.getItem(LS.userName) || null,
    };
  }

  function setIdentity(user_id, user_name) {
    if (user_id) localStorage.setItem(LS.userId, user_id);
    if (user_name) localStorage.setItem(LS.userName, user_name);
    syncWhoAmI();
    clearAuthMsgs();
  }

  function clearIdentity() {
    localStorage.removeItem(LS.userId);
    localStorage.removeItem(LS.userName);
    syncWhoAmI();
    clearAuthMsgs();
    const m = document.getElementById("log_out_msg");
    if (m) {
      m.textContent = "已登出";
      setTimeout(() => (m.textContent = ""), 2000);
    }
  }

  function syncWhoAmI() {
    const me = identity();
    const who = document.getElementById("whoami");
    if (who)
      who.textContent = me.user_id
        ? `${me.user_name || "(未命名)"} · ${me.user_id}`
        : "沒登入 Nobody";

    const v = document.getElementById("viewer_name");
    if (v) v.value = me.user_name || "";

    const su = document.getElementById("show_user_name");
    if (su) su.value = me.user_name || "";

    const authSec = document.getElementById("auth_section");
    if (authSec) authSec.hidden = !!me.user_id;
  }

  async function api(path, opts = {}) {
    const url = apiBase() + path;
    const res = await fetch(url, opts);
    if (!res.ok) {
      const msg = await safeText(res);
      throw new Error(`${res.status} ${res.statusText} - ${msg}`);
    }
    const ct = res.headers.get("content-type") || "";
    return ct.includes("application/json") ? res.json() : res.text();
  }
  async function safeText(res) {
    try {
      return await res.text();
    } catch {
      return "";
    }
  }

  function toast(id, msg, type) {
    const el = document.getElementById(id);
    if (!el) return;
    el.className = type === "ok" ? "ok muted" : type === "err" ? "err muted" : "muted";
    el.textContent = msg;
  }
  function toastBox(id, msg, isErr) {
    const box = document.getElementById(id);
    box.innerHTML = "";
    box.append(el("div", { className: isErr ? "card err" : "card ok" }, [msg]));
  }
  function el(tag, attrs = {}, children = []) {
    const n = document.createElement(tag);
    Object.entries(attrs).forEach(([k, v]) => ((k in n) ? (n[k] = v) : n.setAttribute(k, v)));
    (children || []).forEach((c) => n.append(c));
    return n;
  }

  async function register() {
    const name = document.getElementById("register_name").value.trim();
    if (!name) return toast("reg_msg", "請輸入姓名再繼續QQ", "err");
    try {
      const data = await api("/users/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_name: name }),
      });
      setIdentity(data.user_id, data.user_name);
      toast("reg_msg", `^_^註冊成功！\n<重要重要重要!>請記下你的 user_id：${data.user_id}`, "ok");
    } catch (e) {
      toast("reg_msg", "註冊失敗QQ", "err");
    }
  }

  async function bindUserId() {
    const u = document.getElementById("bind_user_id").value.trim();
    if (!u) return toast("bind_msg", "請輸入你的user_id再繼續", "err");
    try {
      const data = await api(`/users/${encodeURIComponent(u)}`);
      setIdentity(data.user_id, data.user_name);
      toast("bind_msg", `成功!：${data.user_name}`, "ok");
    } catch (e) {
      toast("bind_msg", "失敗", "err");
    }
  }

  async function createShow() {
    const me = identity();
    const user_name = (document.getElementById("show_user_name").value || "").trim();
    const tix_name = (document.getElementById("tix_name").value || "").trim();
    const show_name = (document.getElementById("show_name").value || "").trim();

    if (!me.user_id) return toast("create_msg", "QQ 請先綁定或註冊 user_id", "err");
    if (!user_name || !tix_name || !show_name) return toast("create_msg", "QQ 請完整填寫欄位", "err");

    try {
      await api("/shows", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: me.user_id, user_name, tix_name, show_name }),
      });
      document.getElementById("tix_name").value = "";
      document.getElementById("show_name").value = "";
      toast("create_msg", "^_^ 建立成功！", "ok");
      refreshBoard();
    } catch (e) {
      toast("create_msg", "QQ 建立失敗：" + e.message, "err");
    }
  }

  async function listShows() {
    return api("/shows");
  }

  async function search() {
    const name = (document.getElementById("search_name").value || "").trim();
    const field = document.getElementById("search_field").value;
    const exact = document.getElementById("exact").checked;
    if (!name) return toastBox("search_results", "請輸入姓名", true);
    try {
      const data = await api(
        `/shows/search?name=${encodeURIComponent(name)}&field=${field}&exact=${exact}`
      );
      renderShows(data, document.getElementById("search_results"), true);
    } catch (e) {
      toastBox("search_results", "搜尋失敗：" + e.message, true);
    }
  }

  function resetSearch() {
    document.getElementById("search_name").value = "";
    document.getElementById("search_results").innerHTML = "";
  }

  async function loadComments(showId, container) {
    const viewerEl = document.getElementById("viewer_name");
    const me = identity();
    const viewerName = viewerEl ? (viewerEl.value || "").trim() : (me.user_name || "");

    const qs = new URLSearchParams();
    if (viewerName) qs.set("viewer_name", viewerName);
    if (me.user_id) qs.set("viewer_user_id", me.user_id); // ✅ 關鍵

    try {
      const arr = await api(`/shows/${showId}/comments${qs.toString() ? `?${qs}` : ''}`);
      container.innerHTML = '';
      if (arr.length === 0) {
        container.append(el('div', { className: 'muted' }, ['目前沒有您可見的留言']));
        return;
      }
      arr.forEach(c => {
        container.append(
          el('div', { className: 'muted' }, [
            el('span', { className: 'pill' }, [c.visibility]),
            ' ', el('b', {}, [c.author_name]), '：', c.content
          ])
        );
      });
    } catch (e) {
      container.innerHTML = '';
      container.append(el('div', { className: 'err' }, ['QQ 讀取留言失敗：', e.message]));
    }
  }

  async function submitComment(showId, formEl, commentsBox) {
    const me = identity();
    const author_name = formEl.querySelector('.author').value.trim() || me.user_name || '';
    const content = formEl.querySelector('.content').value.trim();
    const visibility = formEl.querySelector('.visibility').value;
    if (!author_name || !content) return alert('QQ 請填寫留言者與內容再繼續QQ');

    try {
      await api(`/shows/${showId}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          author_user_id: me.user_id || null,
          author_name, content, visibility
        })
      });
      formEl.querySelector('.content').value = '';
      await loadComments(showId, commentsBox);
    } catch (e) {
      alert('留言失敗，請確認是否有正確登入');
    }
  }


  function renderShows(list, mount, compact) {
    mount.innerHTML = "";
    if (!list || list.length === 0) {
      mount.append(el("div", { className: "muted" }, ["QQ 目前還沒有資料～逛逛再回來八"]));
      return;
    }
    list.forEach((s) => {
      const card = el("div", { className: "card" });
      card.append(
        el("div", {}, [
          el("div", { className: "mono" }, [`#${s.id}`]),
          el("div", {}, [el("b", {}, [s.show_name])]),
          el("div", { className: "muted" }, [`擁有者：${s.user_name}`]),
          el("div", { className: "muted" }, [`票券姓名：${s.tix_name}`]),
        ])
      );
      const commentsBox = el("div");
      const form = el("div", { className: "row", style: "margin-top:8px;" }, [
        el("input", { className: "author", placeholder: "留言者（預設身分）" }),
        el("input", { className: "content", placeholder: "留言內容", style: "min-width:220px;flex:1;" }),
        el("select", { className: "visibility" }, [
          el("option", { value: "public" }, ["公開"]),
          el("option", { value: "Private" }, ["只給門票擁有者看"]),
        ]),
        el("button", { onclick: () => submitComment(s.id, form, commentsBox) }, ["留言！"]),
      ]);
      card.append(el("div", { style: "margin:6px 0;" }, [el("span", { className: "muted" }, ["留言："])]), commentsBox);
      if (!compact) card.append(form);
      mount.append(card);
      loadComments(s.id, commentsBox);
    });
  }

  async function refreshBoard() {
    try {
      const data = await listShows();
      renderShows(data, document.getElementById("board"), false);
    } catch (e) {
      toastBox("board", "QQ 讀取失敗：" + e.message, true);
    }
  }

  function switchTab(which) {
    document.querySelectorAll(".tab").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.tab === which);
    });
    const boardPanel = document.getElementById("tab-board");
    const mentionsPanel = document.getElementById("tab-mentions");
    if (boardPanel) boardPanel.hidden = which !== "board";
    if (mentionsPanel) mentionsPanel.hidden = which !== "mentions";

    if (which === "board") refreshBoard();
    else if (which === "mentions") loadMentions();
  }

  function refreshCurrentTab() {
    const active = document.querySelector(".tab.active")?.dataset.tab || "board";
    if (active === "board") refreshBoard();
    else if (active === "mentions") loadMentions();
  }

  async function loadMentions() {
    const box = document.getElementById("mentions_list");
    box.innerHTML = "";
    const me = identity();
    if (!me.user_id) {
      box.append(el("div", { className: "card err" }, ["請先在上方登入/註冊以綁定 user_id"]));
      return;
    }

    let shows = [];
    try {
      shows = await listShows();
    } catch (e) {
      box.append(el("div", { className: "card err" }, ["讀取票券失敗：", e.message]));
      return;
    }

    const myShows = shows.filter((s) => s.user_id === me.user_id);
    if (myShows.length === 0) {
      box.append(el("div", { className: "muted" }, ["你目前沒有登記任何票券"]));
      return;
    }

    const results = await Promise.all(
      myShows.map(async (s) => {
        try {
          const cms = await api(`/shows/${s.id}/comments?viewer_name=${encodeURIComponent(s.user_name)}`);
          const external = cms.filter((c) => {
            if (c.author_user_id && me.user_id) return c.author_user_id !== me.user_id;
            return c.author_name !== s.user_name;
          });
          return { show: s, comments: external };
        } catch (e) {
          return { show: s, comments: [], error: e.message };
        }
      })
    );

    const hasExternal = results.filter((r) => r.comments.length > 0);
    if (hasExternal.length === 0) {
      box.append(el("div", { className: "muted" }, ["目前沒有任何票券被別人留言"]));
      return;
    }

    hasExternal.forEach(({ show, comments }) => {
      const card = el("div", { className: "card" });
      const header = el("div", {}, [
        el("div", { className: "mono" }, [`#${show.id}`]),
        el("div", {}, [el("b", {}, [show.show_name])]),
        el("div", { className: "muted" }, [`擁有者：${show.user_name}（${show.user_id}）`]),
        el("div", { className: "muted" }, [`票券姓名：${show.tix_name}`]),
        el("div", { className: "ok" }, [`有 ${comments.length} 則來自別人的留言`]),
      ]);
      const list = el("div", { style: "margin-top:8px;" });
      comments.slice(0, 5).forEach((c) => {
        list.append(
          el("div", { className: "muted" }, [
            el("span", { className: "pill" }, [c.visibility]),
            " ",
            el("b", {}, [c.author_name]),
            "：",
            c.content,
          ])
        );
      });
      card.append(header, list);
      box.append(card);
    });
  }

  Object.assign(window, {
    register,
    bindUserId,
    createShow,
    search,
    resetSearch,
    switchTab,
    refreshCurrentTab,
    submitComment,
    clearIdentity,
  });

  document.addEventListener("DOMContentLoaded", () => {
    syncWhoAmI();
    switchTab("board");
  });
})();
