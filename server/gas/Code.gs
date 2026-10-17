/**
 * 平泉タヌキ侍: 順位表のサーバー（Google Apps Script の Web アプリ。スプレッドシートに、記録を残す）。
 *
 * 使い方は server/gas/README.md を見ること（スプレッドシートの「拡張機能 → Apps Script」に、このファイルを貼って、Web アプリとして公開する）。
 *
 * 呼び出し（ブラウザの JavaScript から。POST の本文は、JSON の文字列。ヘッダーは付けない = プリフライトを避ける）:
 *   GET  ?action=ranking&level=easy      → { ok: true, rows: [{ name, frames }, ...] }   上位 TOP_N 件（速い順）
 *   POST { action: "start", level }      → { ok: true, token }                           遊び始め。サーバーが、開始の時刻を覚える
 *   POST { action: "submit", token, level, name, frames } → { ok: true, rank }           通しをクリアした。記録を送る（トークンは、1回だけ使える）
 * 失敗したときは、{ ok: false, error: "理由" }。
 *
 * 不正への考え方（完全には防げない。遊びの順位表と割り切る）:
 *   - 「開始から、送信までの、実時間」が、送られたフレーム数（÷60）より短い記録は、弾く（偽造の記録を、直接送る手口を防ぐ）。
 *   - 人間には不可能な速さ（MIN_FRAMES 未満）も、弾く。
 *   - 名前は、半角英大文字と数字の3文字だけ。
 */

var LEVELS = ["easy", "normal", "hard"];
var SHEET = "scores";          // 記録を置くシートの名前（無ければ、自動で作る）
var TOP_N = 20;                // 順位表に出す件数
var KEEP = 200;                // 各難しさで、残す件数（これを超えたら、遅い記録から消す）
var MIN_FRAMES = 7200;         // これより速い（= 2分未満の）通しは、あり得ないとみなす（60 フレーム = 1 秒）。実際の最短を知ったら、見直す
var MAX_FRAMES = 216000;       // 60分より遅い記録は、受け付けない
var TOKEN_TTL = 21600;         // 開始の合図が有効な秒数（6時間）
var CACHE_SEC = 60;            // 順位表を、使い回す秒数（スプレッドシートの読み込みを減らす）
var NG_NAMES = ["ASS", "SEX", "FUK", "FCK", "SHT", "KKK", "NZI", "DIE"];   // 使えない3文字（必要なら足す）

/** 最初に1回だけ、エディタから実行する: 権限の許可を求め、記録のシート（scores）を作る（末尾が「_」の関数は、エディタの一覧に出ない） */
function setup() {
  sheet_();
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

function doGet(e) {
  var p = (e && e.parameter) || {};
  if (p.action === "ranking" && LEVELS.indexOf(p.level) >= 0) {
    return json_({ ok: true, rows: ranking_(p.level) });
  }
  return json_({ ok: false, error: "bad request" });
}

function doPost(e) {
  var p;
  try {
    p = JSON.parse(e.postData.contents);
  } catch (err) {
    return json_({ ok: false, error: "bad json" });
  }
  if (!p || LEVELS.indexOf(p.level) < 0) {
    return json_({ ok: false, error: "bad level" });
  }
  if (p.action === "start") {
    var token = Utilities.getUuid();
    CacheService.getScriptCache().put("t_" + token, String(Date.now()), TOKEN_TTL);
    return json_({ ok: true, token: token });
  }
  if (p.action === "submit") {
    var cache = CacheService.getScriptCache();
    var key = "t_" + String(p.token);
    var started = cache.get(key);
    var bad = checkSubmit_(p, started ? Number(started) : null, Date.now());
    if (bad) {
      return json_({ ok: false, error: bad });
    }
    cache.remove(key);          // 1回だけ使える
    var lock = LockService.getScriptLock();
    lock.waitLock(10000);       // 同時に書き込まれても、壊れないように
    try {
      var rank = add_(p.level, String(p.name), Math.floor(p.frames));
    } finally {
      lock.releaseLock();
    }
    CacheService.getScriptCache().remove("r_" + p.level);       // 順位表の使い回しを、捨てる
    return json_({ ok: true, rank: rank });
  }
  return json_({ ok: false, error: "bad action" });
}

/**
 * 送られた記録を確かめる。問題が無ければ null、あれば理由の文字列を返す（スプレッドシートに触らない純粋な処理）。
 * startedMs: 開始の時刻（ミリ秒。トークンが無い・期限切れなら null） / nowMs: いまの時刻
 */
function checkSubmit_(p, startedMs, nowMs) {
  if (startedMs === null) return "no token";
  if (typeof p.name !== "string" || !/^[A-Z0-9]{3}$/.test(p.name)) return "bad name";
  if (NG_NAMES.indexOf(p.name) >= 0) return "ng name";
  if (typeof p.frames !== "number" || !isFinite(p.frames) || Math.floor(p.frames) !== p.frames) return "bad frames";
  if (p.frames < MIN_FRAMES || p.frames > MAX_FRAMES) return "frames out of range";
  var elapsedSec = (nowMs - startedMs) / 1000;
  if (elapsedSec < (p.frames / 60) * 0.95 - 2) return "too fast";        // ゲームは、1秒に、60 フレームより速くは進まない（ゆらぎの分だけ、少し甘くする）
  return null;
}

function sheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(SHEET);
  if (!sh) {
    sh = ss.insertSheet(SHEET);
    sh.appendRow(["時刻", "難しさ", "名前", "フレーム数"]);
  }
  return sh;
}

/** 記録を足して、その難しさの中での順位（1から）を返す。残す件数を超えたら、遅い記録を消す */
function add_(level, name, frames) {
  var sh = sheet_();
  sh.appendRow([new Date(), level, name, frames]);
  var rows = readLevel_(sh, level);
  var rank = 1;
  for (var i = 0; i < rows.length; i++) {
    if (rows[i].frames < frames) rank++;
  }
  if (rows.length > KEEP) prune_(sh, level);
  return rank;
}

/** その難しさの、記録を全部読む: [{ row, name, frames }]（速い順） */
function readLevel_(sh, level) {
  var last = sh.getLastRow();
  if (last < 2) return [];
  var vals = sh.getRange(2, 1, last - 1, 4).getValues();
  var out = [];
  for (var i = 0; i < vals.length; i++) {
    if (vals[i][1] === level) out.push({ row: i + 2, name: String(vals[i][2]), frames: Number(vals[i][3]) });
  }
  out.sort(function (a, b) { return a.frames - b.frames; });
  return out;
}

/** KEEP 件を超えた分（遅い記録）を、シートから消す。行番号が崩れないように、下の行から消す */
function prune_(sh, level) {
  var rows = readLevel_(sh, level).slice(KEEP).map(function (r) { return r.row; });
  rows.sort(function (a, b) { return b - a; });
  rows.forEach(function (r) { sh.deleteRow(r); });
}

function ranking_(level) {
  var cache = CacheService.getScriptCache();
  var hit = cache.get("r_" + level);
  if (hit) return JSON.parse(hit);
  var rows = readLevel_(sheet_(), level).slice(0, TOP_N).map(function (r) { return { name: r.name, frames: r.frames }; });
  cache.put("r_" + level, JSON.stringify(rows), CACHE_SEC);
  return rows;
}
