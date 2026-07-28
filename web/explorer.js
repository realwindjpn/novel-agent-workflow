/* Project file explorer: renders the live tree of demo/ (Pyodide FS or
 * replay snapshot), highlights files changed by the latest step, shows
 * file contents below, and shows file count + total size in the panel
 * header. releases/*.json renders as a punched-tape receipt. */
(function () {
  "use strict";

  var treeEl = document.getElementById("file-tree");
  var headEl = document.getElementById("file-viewer-head");
  var contentEl = document.getElementById("file-content");
  var statsEl = document.getElementById("files-stats");

  var prevTree = {};
  var currentTree = {};
  var selected = null;

  function fmtBytes(n) {
    if (n < 1024) return n + " B";
    if (n < 1024 * 1024) return (n / 1024).toFixed(1) + " KB";
    return (n / 1024 / 1024).toFixed(2) + " MB";
  }

  function buildNested(flat) {
    var root = { dirs: {}, files: [] };
    Object.keys(flat).forEach(function (path) {
      var parts = path.split("/");
      var node = root;
      for (var i = 0; i < parts.length - 1; i++) {
        node = node.dirs[parts[i]] || (node.dirs[parts[i]] = { dirs: {}, files: [] });
      }
      node.files.push({ name: parts[parts.length - 1], path: path });
    });
    return root;
  }

  function changedSet(next, prev) {
    var changed = {};
    Object.keys(next).forEach(function (k) {
      if (prev[k] !== next[k]) changed[k] = true;
    });
    return changed;
  }

  function renderNode(node, depth, changed, frag) {
    var self = window.NWX;
    Object.keys(node.dirs).sort().forEach(function (d) {
      var row = document.createElement("div");
      row.className = "f-row f-dir";
      row.style.paddingLeft = (6 + depth * 14) + "px";
      row.innerHTML = '<span class="ico">▸</span>' + window.NWA.escapeHtml(d) + "/";
      frag.appendChild(row);
      renderNode(node.dirs[d], depth + 1, changed, frag);
    });
    node.files.sort(function (a, b) { return a.name.localeCompare(b.name); })
      .forEach(function (f) {
        var row = document.createElement("div");
        row.className = "f-row" + (changed[f.path] ? " changed" : "") +
                        (selected === f.path ? " selected" : "");
        row.style.paddingLeft = (6 + depth * 14) + "px";
        row.innerHTML = '<span class="ico">·</span>' + window.NWA.escapeHtml(f.name);
        row.title = f.path;
        row.tabIndex = 0;
        row.setAttribute("role", "button");
        row.setAttribute("aria-label", f.path);
        row.addEventListener("click", function () { self.select(f.path); });
        row.addEventListener("keydown", function (e) {
          if (e.key === "Enter" || e.key === " " || e.key === "Spacebar") {
            e.preventDefault();
            self.select(f.path);
          }
        });
        frag.appendChild(row);
      });
  }

  function isReceipt(path) {
    return /^releases\/chapter-\d+\.json$/.test(path);
  }

  function updateStats() {
    if (!statsEl) return;
    var keys = Object.keys(currentTree);
    if (keys.length === 0) { statsEl.textContent = ""; return; }
    var total = 0;
    keys.forEach(function (k) { total += (currentTree[k] || "").length; });
    statsEl.textContent = keys.length + " files · " + fmtBytes(total);
  }

  window.NWX = {
    /* Replace the whole tree; animate rows whose content changed. */
    update: function (flatTree) {
      prevTree = currentTree;
      currentTree = flatTree || {};
      var changed = changedSet(currentTree, prevTree);
      treeEl.innerHTML = "";
      var keys = Object.keys(currentTree);
      updateStats();
      if (keys.length === 0) {
        treeEl.innerHTML = '<div class="empty-note">运行 ① init 后，这里会出现 workflow.json；流水线推进时，.novel-workflow/events.jsonl、releases/chapter-1.json 会逐个落盘。</div>';
        headEl.textContent = "未选择文件";
        contentEl.textContent = "";
        contentEl.className = "";
        contentEl.id = "file-content";
        selected = null;
        return;
      }
      var frag = document.createDocumentFragment();
      renderNode(buildNested(currentTree), 0, changed, frag);
      treeEl.appendChild(frag);
      // keep the viewer in sync if the selected file changed
      if (selected && currentTree[selected] !== undefined) {
        this.select(selected, true);
      } else if (selected) {
        selected = null;
        headEl.textContent = "未选择文件";
        contentEl.textContent = "";
      }
      // auto-select the most interesting changed file (receipt > events > workflow)
      var auto = Object.keys(changed).filter(function (k) { return isReceipt(k); })[0];
      if (auto) this.select(auto);
    },
    select: function (path, silent) {
      selected = path;
      headEl.textContent = "demo/" + path;
      var text = currentTree[path];
      if (text === undefined) { contentEl.textContent = "(文件已不存在)"; return; }
      var pretty = text;
      if (/\.json(l)?$/.test(path)) {
        if (/\.jsonl$/.test(path)) {
          pretty = text.split("\n").filter(Boolean).map(function (line) {
            try { return JSON.stringify(JSON.parse(line), null, 2); } catch (e) { return line; }
          }).join("\n");
        } else {
          try { pretty = JSON.stringify(JSON.parse(text), null, 2); } catch (e) { /* keep raw */ }
        }
      }
      contentEl.textContent = pretty;
      contentEl.className = isReceipt(path) ? "paper" : "";
      if (!silent) {
        Array.prototype.forEach.call(treeEl.children, function (row) {
          if (!row.title) return;
          row.classList.toggle("selected", row.title === path);
        });
      }
    },
    reset: function () {
      prevTree = {}; currentTree = {}; selected = null;
      this.update({});
    },
    current: function () { return currentTree; }
  };
})();
