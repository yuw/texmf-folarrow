-- folarrow.lua：LuaLaTeXでOpenTypeの数式フォントを使うとき，矢印のグリフの外接矩形から
-- 矢頭の幅と線の太さを直接求める．
--
-- folarrow.extent(boxnum, vertical)
--   箱の中（入れ子の箱やリーダーも含む）のグリフのうち，矢印の向きに直交する方向の
--   広がりが最大のものを矢頭とみなし，その広がりを矢頭の幅とする．
--   線の太さは，同じフォントのマイナス記号（U+2212）の外接矩形の高さとする．
--   Computer Modernなどでは，これが矢印の軸の太さと一致する．
--   結果を「幅 太さ 鍵 中心」（幅と太さはpt単位の数，鍵はフォント名を小文字の英数字だけに
--   したもの，中心は矢頭の直交方向の中心（横向きならベースラインからの高さ，pt））として
--   TeXに返す．グリフの形の情報がない
--   フォント（TFMだけのType 1フォントなど）では何も返さない．
--
-- Copyright (c) 2026 Yuwsuke Kieda
-- This file is part of the folarrow package, released under the MIT License
-- (see the file LICENSE). The arrow fonts of the package keep the licenses of
-- their original fonts (see licenses/FONTS.md).
--

folarrow = folarrow or {}

local GLYPH = node.id('glyph')
local HLIST = node.id('hlist')
local VLIST = node.id('vlist')
local GLUE = node.id('glue')

-- マイナス記号の太さが矢印の軸の太さと異なるフォントの補正（実測：軸の太さ／マイナス記号の太さ）
-- horizontal：\rightarrowなど，vertical：\Big\downarrowなどの縦の字形
local thickness_correction = {
  horizontal = { asanamath = 1.058, gfsneohellenicmath = 0.815 },
  vertical = { minionmath = 1.16, kpmath = 1.087, gfsneohellenicmath = 0.79 },
}

local function fontdata(fid)
  local h = fonts and fonts.hashes and fonts.hashes.identifiers
  local tfm = h and h[fid]
  if not tfm then return nil end
  local desc = tfm.descriptions
    or (tfm.shared and tfm.shared.rawdata and tfm.shared.rawdata.descriptions)
  local p = tfm.parameters
  if not desc or not p or not p.factor then return nil end
  return tfm, desc, p.factor -- factor：フォント単位1あたりのsp
end

-- 添字用の字形（OpenTypeのssty）：数式の添字の大きさのフォントにはsstyが指定されて
-- いて，最終的には置換後の字形が使われる．箱の中のグリフはまだ置換前なので，ここで
-- フォントの置換表（gsub_alternate）を引いて置換後の字形にする．
local ssty_cache = {}
local function ssty_glyph(fid, tfm, char)
  local sp = tfm.specification
  local n = sp and sp.features and sp.features.normal and sp.features.normal.ssty
  n = tonumber(n)
  if not n or n < 1 then return char end
  local key = fid .. ':' .. char
  if ssty_cache[key] then return ssty_cache[key] end
  local out = char
  local seqs = tfm.resources and tfm.resources.sequences
  for _, s in ipairs(seqs or {}) do
    if s.features and s.features.ssty and s.type == 'gsub_alternate' then
      for _, st in ipairs(s.steps or {}) do
        local alts = st.coverage and st.coverage[char]
        if type(alts) == 'table' and #alts > 0 then
          out = alts[math.min(n, #alts)]
        end
      end
    end
  end
  ssty_cache[key] = out
  return out
end

-- usessty：添字用の字形に置き換えて測るか（falseなら元の字形）
local function bbox_extent(fid, char, vertical, usessty)
  local tfm, desc, f = fontdata(fid)
  if not desc then return nil end
  local g = (usessty ~= false and desc[ssty_glyph(fid, tfm, char)]) or desc[char]
  local bb = g and g.boundingbox
  if not bb then return nil end
  -- 2つ目の値：直交方向の中心（横向きならベースラインからの高さ，縦向きなら左端からの位置）
  if vertical then return (bb[3] - bb[1]) * f, (bb[3] + bb[1]) / 2 * f
  else return (bb[4] - bb[2]) * f, (bb[4] + bb[2]) / 2 * f end
end

local function correction(tfm, vertical)
  local pr = tfm.properties or {}
  local nm = (pr.psname or pr.fontname or pr.fullname or pr.name or '')
  nm = nm:lower():gsub('[^%w]', '')
  -- 縦向きは縦向き用の補正を優先し，なければ横向きの補正を使う
  if vertical then
    for k, v in pairs(thickness_correction.vertical) do
      if nm:find(k, 1, true) then return v end
    end
  end
  for k, v in pairs(thickness_correction.horizontal) do
    if nm:find(k, 1, true) then return v end
  end
  return 1
end

function folarrow.extent(boxnum, vertical)
  local box = tex.getbox(boxnum)
  if not box then return end
  local best, bestfont, bestchar, bestmid
  local function walk(head)
    for n in node.traverse(head) do
      local id = n.id
      if id == GLYPH then
        local e, mid = bbox_extent(n.font, n.char, vertical)
        if e and (not best or e > best) then best, bestfont, bestchar, bestmid = e, n.font, n.char, mid end
      elseif id == HLIST or id == VLIST then
        walk(n.head)
      elseif id == GLUE and n.leader then
        walk(n.leader)
      end
    end
  end
  walk(box.head)
  if not best or best <= 0 then return end
  local tfm = fontdata(bestfont)
  -- 線の太さはマイナス記号から測る．矢印自体が添字用の字形に置き換わるときだけ，
  -- マイナス記号も添字用の字形で測る（矢印に添字用の字形がなく，マイナス記号にだけ
  -- 太めの添字用の字形があるフォント（New Computer Modern Math，KpMath）があるため）．
  local arrow_ssty = ssty_glyph(bestfont, tfm, bestchar) ~= bestchar
  local t = bbox_extent(bestfont, 0x2212, false, arrow_ssty)
  if not t or t <= 0 then return end
  t = t * correction(tfm, vertical)
  -- 3つ目はフォント名の鍵（尻の形の表を引くため．小文字の英数字だけにしたもの）
  local pr = tfm.properties or {}
  local key = (pr.psname or pr.fontname or pr.fullname or pr.name or ''):lower():gsub('[^%w]', '')
  -- 4つ目は矢頭の直交方向の中心（pt）．横向きの矢印の3本線の高さに使う
  tex.sprint(string.format('%.5f %.5f %s %.5f', best / 65536, t / 65536, key, (bestmid or 0) / 65536))
end

-- folarrow.hink(boxnum)
--   横向きの矢印の箱（\longrightarrowや，マイナス記号・リーダー・→からなる伸びる矢印）の
--   字面の左端と右端（箱の基準点からの位置，pt）を「左 右」としてTeXに返す．箱の直下の
--   最初のグリフの外接矩形の左端と，最後のグリフの外接矩形の右端から求める（添字用の字形にも
--   対応する）．グリフの形の情報がなければ何も返さない．
function folarrow.hink(boxnum)
  local box = tex.getbox(boxnum)
  if not box then return end
  local first, last
  for n in node.traverse_id(GLYPH, box.head) do
    first = first or n
    last = n
  end
  if not first then return end
  local function edge(n, right)
    local tfm, desc, f = fontdata(n.font)
    if not desc then return nil end
    local g = desc[ssty_glyph(n.font, tfm, n.char)] or desc[n.char]
    local bb = g and g.boundingbox
    if not bb then return nil end
    local x = node.dimensions(box.glue_set, box.glue_sign, box.glue_order, box.head, n)
    return x + (right and bb[3] or bb[1]) * f
  end
  local l, r = edge(first, false), edge(last, true)
  if not l or not r then return end
  tex.sprint(string.format('%.5f %.5f', l / 65536, r / 65536))
end

return folarrow
