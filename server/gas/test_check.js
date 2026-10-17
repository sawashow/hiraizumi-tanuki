// checkSubmit_ の確認（GAS の外で、node で動かす: node server/gas/test_check.js）。スプレッドシートに触らない純粋な処理だけを試す
const fs = require("fs"), vm = require("vm"), path = require("path");
const ctx = {};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(__dirname, "Code.gs"), "utf8"), ctx);
let fail = 0;
const t = (name, got, want) => { const ok = got === want; if (!ok) fail++; console.log((ok ? "OK  " : "NG  ") + name + (ok ? "" : "  got=" + got + " want=" + want)); };
const now = 1_000_000_000_000, min = 60 * 1000;
const ok = { name: "ABC", frames: 18000 };                 // 5分
t("正しい記録は通る（開始から5分10秒後）", ctx.checkSubmit_(ok, now - 310 * 1000, now), null);
t("トークンが無い・期限切れは、弾く", ctx.checkSubmit_(ok, null, now), "no token");
t("実時間より速い記録（開始の1分後に5分の記録）は、弾く", ctx.checkSubmit_(ok, now - 1 * min, now), "too fast");
t("ゆらぎの分（5%）は、許す", ctx.checkSubmit_(ok, now - 290 * 1000, now), null);
t("名前が3文字でない", ctx.checkSubmit_({ name: "AB", frames: 18000 }, now - 400 * 1000, now), "bad name");
t("小文字は、使えない", ctx.checkSubmit_({ name: "abc", frames: 18000 }, now - 400 * 1000, now), "bad name");
t("使えない名前", ctx.checkSubmit_({ name: "ASS", frames: 18000 }, now - 400 * 1000, now), "ng name");
t("速すぎる記録（2分未満）は、弾く", ctx.checkSubmit_({ name: "ABC", frames: 3000 }, now - 400 * 1000, now), "frames out of range");
t("遅すぎる記録（60分超）は、弾く", ctx.checkSubmit_({ name: "ABC", frames: 300000 }, now - 9999 * 1000, now), "frames out of range");
t("小数は、弾く", ctx.checkSubmit_({ name: "ABC", frames: 18000.5 }, now - 400 * 1000, now), "bad frames");
t("文字列は、弾く", ctx.checkSubmit_({ name: "ABC", frames: "18000" }, now - 400 * 1000, now), "bad frames");
console.log(fail ? "失敗: " + fail : "失敗: なし");
process.exit(fail ? 1 : 0);
