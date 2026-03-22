-- Kokoro TTS — Hammerspoon integration
-- ⌥S  → toggle speak/stop (queues if already speaking)
-- ⌥⇧V → voice picker popup
-- Menu bar ● → dropdown with queue, history, voice selector
--
-- Install: add to ~/.hammerspoon/init.lua:
--   package.path = os.getenv("HOME") .. "/code/voice-automation/config/hammerspoon/?.lua;" .. package.path
--   require("kokoro")

local SCRIPT = os.getenv("HOME") .. "/code/voice-automation/scripts/speak.sh"
local DETECT = os.getenv("HOME") .. "/code/voice-automation/scripts/detect_lang.py"
local HEALTH_URL = "http://localhost:8880/v1/audio/voices"
local MAX_HISTORY = 20
local PREVIEW_LEN = 45

-- ── Voice catalog ──

local VOICES = {
  { id = "af_heart",   name = "Heart",   flag = "🇺🇸", gender = "F" },
  { id = "af_nova",    name = "Nova",    flag = "🇺🇸", gender = "F" },
  { id = "af_bella",   name = "Bella",   flag = "🇺🇸", gender = "F" },
  { id = "am_adam",    name = "Adam",    flag = "🇺🇸", gender = "M" },
  { id = "am_michael", name = "Michael", flag = "🇺🇸", gender = "M" },
  { id = "bf_emma",    name = "Emma",    flag = "🇬🇧", gender = "F" },
  { id = "bm_george",  name = "George",  flag = "🇬🇧", gender = "M" },
  { id = "pf_dora",    name = "Dora",    flag = "🇧🇷", gender = "F" },
  { id = "pm_alex",    name = "Alex",    flag = "🇧🇷", gender = "M" },
}

local function voiceById(id)
  for _, v in ipairs(VOICES) do
    if v.id == id then return v end
  end
  return nil
end

-- ── State ──

local speakTask = nil
local queue = {}        -- { text, lang, voice, status, addedAt }
local currentIdx = 0
local currentState = "down"
local selectedVoice = nil  -- nil = auto-detect

-- ── Language detection ──

local PT_WORDS = {
  "da", "do", "das", "dos", "na", "nas", "nos", "uma", "uns", "umas",
  "não", "são", "está", "isso", "também", "você", "ele", "ela",
  "esse", "essa", "este", "esta", "já", "muito", "pode", "seu", "sua",
  "ter", "foi", "havia", "mas", "ao", "aos", "até", "pelo", "pela",
}

local EN_WORDS = {
  "the", "is", "are", "was", "were", "have", "has", "had", "been",
  "will", "would", "could", "should", "can", "this", "that", "these",
  "those", "there", "their", "they", "them", "with", "from", "into",
  "which", "when", "where", "what", "while", "because", "then", "than",
  "being", "does", "did", "not", "but", "and", "for", "you", "your",
}

local function detectLang(text)
  local ptChars = select(2, text:gsub("[ãõçÃÕÇ]", "")) or 0
  local ptAccents = select(2, text:gsub("[àáâéêíóôúÀÁÂÉÊÍÓÔÚ]", "")) or 0

  local words = {}
  for w in text:lower():gmatch("%a+") do
    words[w] = (words[w] or 0) + 1
  end

  local ptScore = ptChars * 3 + ptAccents * 2
  for _, w in ipairs(PT_WORDS) do ptScore = ptScore + (words[w] or 0) end

  local enScore = 0
  for _, w in ipairs(EN_WORDS) do enScore = enScore + (words[w] or 0) end

  return (ptScore >= 2 and ptScore > enScore) and "pt" or "en"
end

local function flagForLang(lang)
  return lang == "pt" and "🇧🇷" or "🇺🇸"
end

-- ── Menu bar indicator ──

local dot = hs.menubar.new()

local colors = {
  ready    = { red = 0.30, green = 0.75, blue = 0.35, alpha = 1 },
  speaking = { red = 0.25, green = 0.50, blue = 1.00, alpha = 1 },
  down     = { red = 0.85, green = 0.25, blue = 0.25, alpha = 1 },
}

local function setState(state)
  if state == currentState then return end
  currentState = state
  dot:setTitle(hs.styledtext.new("●", {
    color = colors[state],
    font = { size = 14 },
  }))
end

local function preview(text)
  local clean = text:gsub("\n", " "):gsub("%s+", " ")
  if #clean > PREVIEW_LEN then return clean:sub(1, PREVIEW_LEN) .. "…" end
  return clean
end

-- ── Core playback ──

local function stopSpeaking()
  os.execute("pkill -x ffplay 2>/dev/null; pkill -x afplay 2>/dev/null")
  if speakTask and speakTask:isRunning() then speakTask:terminate() end
  if currentIdx > 0 and queue[currentIdx] and queue[currentIdx].status == "playing" then
    queue[currentIdx].status = "stopped"
  end
  speakTask = nil
  currentIdx = 0
  setState("ready")
end

local playNext  -- forward declaration

local function playItem(idx)
  if speakTask and speakTask:isRunning() then stopSpeaking() end

  local item = queue[idx]
  if not item then return end

  currentIdx = idx
  item.status = "playing"
  setState("speaking")

  local args = { SCRIPT }
  if item.voice then
    table.insert(args, "--voice")
    table.insert(args, item.voice)
  end
  table.insert(args, item.text)

  speakTask = hs.task.new("/bin/bash", function(exitCode)
    speakTask = nil
    if item.status == "playing" then item.status = "done" end
    setState("ready")
    playNext()
  end, args)

  speakTask:start()
end

playNext = function()
  for i, item in ipairs(queue) do
    if item.status == "queued" then
      playItem(i)
      return
    end
  end
  currentIdx = 0
end

local function addToQueue(text, voice)
  local lang = detectLang(text)
  local resolvedVoice = voice or selectedVoice  -- nil = auto-detect in speak.sh

  table.insert(queue, {
    text = text,
    lang = lang,
    voice = resolvedVoice,
    status = "queued",
    addedAt = os.time(),
  })

  -- Trim oldest finished items
  while #queue > MAX_HISTORY do
    for i, item in ipairs(queue) do
      if item.status == "done" then
        table.remove(queue, i)
        if currentIdx >= i then currentIdx = currentIdx - 1 end
        break
      end
    end
    break
  end

  if not speakTask or not speakTask:isRunning() then
    playNext()
  end
end

-- ── Voice chooser ──

local voiceChooser = hs.chooser.new(function(choice)
  if not choice then return end
  selectedVoice = choice.id
  local v = voiceById(choice.id)
  hs.notify.new({
    title = "Kokoro TTS",
    informativeText = "Voice: " .. v.flag .. " " .. v.name,
  }):send()
end)

local function showVoiceChooser()
  local choices = {}
  for _, v in ipairs(VOICES) do
    local check = (selectedVoice == v.id) and " ✓" or ""
    table.insert(choices, {
      text = v.flag .. "  " .. v.name .. " (" .. v.gender .. ")" .. check,
      subText = v.id,
      id = v.id,
    })
  end
  -- Add auto-detect option
  local autoCheck = selectedVoice == nil and " ✓" or ""
  table.insert(choices, 1, {
    text = "🌐  Auto-detect" .. autoCheck,
    subText = "Detects PT/EN automatically",
    id = "__auto__",
  })
  voiceChooser:choices(choices)
  voiceChooser:show()
end

-- Handle auto-detect selection
local originalCallback = voiceChooser
voiceChooser = hs.chooser.new(function(choice)
  if not choice then return end
  if choice.id == "__auto__" then
    selectedVoice = nil
    hs.notify.new({ title = "Kokoro TTS", informativeText = "Voice: 🌐 Auto-detect" }):send()
  else
    selectedVoice = choice.id
    local v = voiceById(choice.id)
    hs.notify.new({
      title = "Kokoro TTS",
      informativeText = "Voice: " .. v.flag .. " " .. v.name,
    }):send()
  end
end)

-- ── Menu bar dropdown ──

local function buildMenu()
  local menu = {}

  -- Server status
  local statusLabel = currentState == "down" and "● Server offline" or "● Server online"
  table.insert(menu, { title = statusLabel, disabled = true })
  table.insert(menu, { title = "-" })

  -- Now playing
  if currentIdx > 0 and queue[currentIdx] and queue[currentIdx].status == "playing" then
    local item = queue[currentIdx]
    local flag = flagForLang(item.lang)
    table.insert(menu, { title = "▶  " .. flag .. "  " .. preview(item.text), disabled = true })
    table.insert(menu, { title = "⏹  Stop", fn = stopSpeaking })
    table.insert(menu, { title = "-" })
  end

  -- Queued items
  local hasQueued = false
  for i, item in ipairs(queue) do
    if item.status == "queued" then
      if not hasQueued then
        table.insert(menu, { title = "Queue", disabled = true })
        hasQueued = true
      end
      local idx = i
      local flag = flagForLang(item.lang)
      table.insert(menu, {
        title = "    " .. flag .. "  " .. preview(item.text),
        fn = function()
          table.remove(queue, idx)
          if currentIdx > idx then currentIdx = currentIdx - 1 end
        end,
      })
    end
  end
  if hasQueued then table.insert(menu, { title = "-" }) end

  -- History (recent first, max 10)
  local historyItems = {}
  for i = #queue, 1, -1 do
    local s = queue[i].status
    if s == "done" or s == "stopped" then
      table.insert(historyItems, { idx = i, item = queue[i] })
      if #historyItems >= 10 then break end
    end
  end

  if #historyItems > 0 then
    table.insert(menu, { title = "History", disabled = true })
    for _, h in ipairs(historyItems) do
      local icon = h.item.status == "stopped" and "⏸" or "✓"
      local flag = flagForLang(h.item.lang)
      table.insert(menu, {
        title = icon .. " " .. flag .. "  " .. preview(h.item.text),
        fn = function() addToQueue(h.item.text) end,
      })
    end
    table.insert(menu, { title = "-" })
  end

  -- Voice selector submenu
  local voiceItems = {}
  table.insert(voiceItems, {
    title = "🌐  Auto-detect" .. (selectedVoice == nil and "  ✓" or ""),
    fn = function()
      selectedVoice = nil
      hs.notify.new({ title = "Kokoro TTS", informativeText = "Voice: 🌐 Auto-detect" }):send()
    end,
  })
  for _, v in ipairs(VOICES) do
    local check = (selectedVoice == v.id) and "  ✓" or ""
    table.insert(voiceItems, {
      title = v.flag .. "  " .. v.name .. " (" .. v.gender .. ")" .. check,
      fn = function()
        selectedVoice = v.id
        hs.notify.new({
          title = "Kokoro TTS",
          informativeText = "Voice: " .. v.flag .. " " .. v.name,
        }):send()
      end,
    })
  end
  table.insert(menu, { title = "Voice", menu = voiceItems })

  -- Clear
  if #queue > 0 then
    table.insert(menu, { title = "-" })
    table.insert(menu, {
      title = "Clear History",
      fn = function()
        if speakTask and speakTask:isRunning() then stopSpeaking() end
        queue = {}
        currentIdx = 0
      end,
    })
  end

  return menu
end

dot:setMenu(buildMenu)

-- ── Hotkeys ──

local function toggleSpeak()
  if speakTask and speakTask:isRunning() then
    stopSpeaking()
    return
  end

  hs.eventtap.keyStroke({"cmd"}, "c")
  hs.timer.doAfter(0.3, function()
    local text = hs.pasteboard.getContents()
    if not text or text == "" then
      hs.notify.new({ title = "Kokoro TTS", informativeText = "No text selected" }):send()
      return
    end
    addToQueue(text)
  end)
end

hs.hotkey.bind({"alt"}, "s", toggleSpeak)
hs.hotkey.bind({"alt", "shift"}, "v", function()
  showVoiceChooser()
end)

-- ── Health check ──

local function checkHealth()
  hs.http.asyncGet(HEALTH_URL, nil, function(code)
    if currentState ~= "speaking" then
      setState(code == 200 and "ready" or "down")
    end
  end)
end

hs.timer.doEvery(30, checkHealth)
checkHealth()
