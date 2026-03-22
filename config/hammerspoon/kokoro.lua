-- Kokoro TTS — Hammerspoon integration
-- ⌥S → toggle speak/stop (queues if already speaking)
-- Menu bar ● → dropdown with queue, history, controls
--
-- Install: add to ~/.hammerspoon/init.lua:
--   package.path = os.getenv("HOME") .. "/code/voice-automation/config/hammerspoon/?.lua;" .. package.path
--   require("kokoro")

local SCRIPT = os.getenv("HOME") .. "/code/voice-automation/scripts/speak.sh"
local HEALTH_URL = "http://localhost:8880/v1/audio/voices"
local MAX_HISTORY = 20
local PREVIEW_LEN = 50

-- ── State ──

local speakTask = nil
local queue = {}       -- { text, status, addedAt }  status: queued|playing|done|stopped
local currentIdx = 0
local currentState = "down"

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

-- Forward declaration
local playNext

local function playItem(idx)
  if speakTask and speakTask:isRunning() then stopSpeaking() end

  local item = queue[idx]
  if not item then return end

  currentIdx = idx
  item.status = "playing"
  setState("speaking")

  speakTask = hs.task.new("/bin/bash", function(exitCode)
    speakTask = nil
    if item.status == "playing" then item.status = "done" end
    setState("ready")
    playNext()
  end, { SCRIPT, item.text })

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

local function addToQueue(text)
  table.insert(queue, { text = text, status = "queued", addedAt = os.time() })

  -- Trim oldest finished items if over limit
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

  -- Start playing if idle
  if not speakTask or not speakTask:isRunning() then
    playNext()
  end
end

-- ── Menu bar dropdown ──

local function buildMenu()
  local menu = {}

  -- Now playing
  if currentIdx > 0 and queue[currentIdx] and queue[currentIdx].status == "playing" then
    table.insert(menu, { title = "▶  " .. preview(queue[currentIdx].text), disabled = true })
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
      table.insert(menu, {
        title = "    " .. preview(item.text),
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
      local icon = h.item.status == "stopped" and "⏸ " or "✓  "
      table.insert(menu, {
        title = icon .. preview(h.item.text),
        fn = function() addToQueue(h.item.text) end,
      })
    end
    table.insert(menu, { title = "-" })
  end

  -- Clear
  if #queue > 0 then
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

-- ── Toggle hotkey ──

local function toggleSpeak()
  -- If speaking, stop
  if speakTask and speakTask:isRunning() then
    stopSpeaking()
    return
  end

  -- Otherwise, copy selection and speak (or queue)
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
