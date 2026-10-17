// 通信の窓口（web_template.tmpl の HZ-BRIDGE）を、node で、本物のサーバー（GAS）に向けて確かめる。
// 使い方: node tools/test_hz_bridge.js   （記録は書き込まない。開始と、弾かれる送信と、順位の取得だけ）
const fs = require("fs"), vm = require("vm"), path = require("path");
const src = fs.readFileSync(path.join(__dirname, "web_template.tmpl"), "utf8");
const code = src.slice(src.indexOf("// HZ-BRIDGE-BEGIN"), src.indexOf("// HZ-BRIDGE-END"));
const m = (fs.readFileSync(path.join(__dirname, "..", "config.py"), "utf8").match(/ONLINE = dict\(url="([^"]+)"/) || [])[1];
const ctx = { fetch, JSON, encodeURIComponent, console, setTimeout };
ctx.window = ctx;      // ブラウザと同じ: window.HZ が、そのまま HZ として見える
const win = ctx;
vm.createContext(ctx);
vm.runInContext(code, ctx);
let fail = 0;
const t = (name, ok, detail) => { if (!ok) fail++; console.log((ok ? "OK  " : "NG  ") + name + (ok ? "" : "  " + detail)); };
(async () => {
  t("URL が config.py にある", !!m, m);
  await win.hzStart(m, "easy");
  const s = JSON.parse(win.HZ.start);
  t("開始: 合図（token）が返る", s.ok === true && typeof s.token === "string" && s.token.length > 10, win.HZ.start);
  await win.hzSubmit(m, s.token, "easy", "TST", 3000);
  const r = JSON.parse(win.HZ.submit);
  t("送信: あり得ない速さは、弾かれる（記録は書かれない）", r.ok === false && r.error === "frames out of range", win.HZ.submit);
  await win.hzRanking(m, "easy");
  const k = JSON.parse(win.HZ.rank.easy);
  t("順位の取得: 配列が返る", k.ok === true && Array.isArray(k.rows), win.HZ.rank.easy);
  // 「bad request」が2回続いたあとに成功する、偽のサーバーで、くり返しを確かめる
  let n = 0;
  const ctx2 = { JSON, encodeURIComponent, console, setTimeout: (f) => f() };   // 待ち時間は、飛ばす
  ctx2.window = ctx2;
  ctx2.fetch = async () => ({ text: async () => (++n < 3 ? '{"ok":false,"error":"bad request"}' : '{"ok":true,"token":"abc"}') });
  vm.createContext(ctx2);
  vm.runInContext(code, ctx2);
  await ctx2.hzStart("http://x", "easy");
  t("bad request が続いても、3回目で成功すれば、token が取れる", JSON.parse(ctx2.HZ.start).token === "abc" && n === 3, ctx2.HZ.start + " 回数 " + n);
  n = -10;
  await ctx2.hzSubmit("http://x", "abc", "easy", "TST", 9000);
  t("失敗が続いたら、3回で諦める（無限にくり返さない）", n === -7 && JSON.parse(ctx2.HZ.submit).ok === false, "回数 " + (n + 10));
  ctx2.fetch = async () => ({ text: async () => { n++; return '{"ok":false,"error":"too fast"}'; } });
  n = 0;
  await ctx2.hzSubmit("http://x", "abc", "easy", "TST", 9000);
  t("サーバーが理由つきで断ったときは、くり返さない（1回だけ）", n === 1, "回数 " + n);
  await win.hzStart("http://127.0.0.1:9/none", "easy");
  t("通信できないときも、例外を出さず、失敗として返る", JSON.parse(win.HZ.start).ok === false, win.HZ.start);
  console.log(fail ? "失敗: " + fail : "失敗: なし");
  process.exit(fail ? 1 : 0);
})();
