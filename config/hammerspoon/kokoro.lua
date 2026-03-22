-- Kokoro TTS — Hammerspoon integration
-- ⌥S  → speak selected text
-- ⌥⇧S → stop speaking
-- Menu bar dot: green=ready, blue=speaking, red=server down
--
-- Install: add to ~/.hammerspoon/init.lua:
--   package.path = os.getenv("HOME") .. "/code/voice-automation/config/hammerspoon/?.lua;" .. package.path
--   require("kokoro")

local SCRIPT = os.getenv("HOME") .. "/code/voice-automation/scripts/speak.sh"
local HEALTH_URL = "http://localhost:8880/v1/audio/voices"

-- Menu bar indicator
local dot = hs.menubar.new()
local speakTask = nil

local colors = {
  ready    = { green = 0.6, red = 0.2, blue = 0.2, alpha = 1 },
  speaking = { green = 0.5, red = 0.3, blue = 1.0, alpha = 1 },
  down     = { green = 0.2, red = 0.8, blue = 0.2, alpha = 1 },
}

local currentState = "down"

local function setState(state)
  if state == currentState then return end
  currentState = state
  local styledText = hs.styledtext.new("●", {
    color = colors[state],
    font = { size = 14 },
  })
  dot:setTitle(styledText)
end

-- Health check (every 30s)
local function checkHealth()
  hs.http.asyncGet(HEALTH_URL, nil, function(code)
    if currentState ~= "speaking" then
      setState(code == 200 and "ready" or "down")
    end
  end)
end

local healthTimer = hs.timer.doEvery(30, checkHealth)
checkHealth()

-- Speak selected text
local function speakSelection()
  hs.eventtap.keyStroke({"cmd"}, "c")

  hs.timer.doAfter(0.3, function()
    local text = hs.pasteboard.getContents()

    if not text or text == "" then
      hs.notify.new({ title = "Kokoro TTS", informativeText = "No text selected" }):send()
      return
    end

    -- Kill any previous playback
    if speakTask and speakTask:isRunning() then
      os.execute("pkill -x ffplay 2>/dev/null; pkill -x afplay 2>/dev/null")
      speakTask:terminate()
    end

    setState("speaking")

    speakTask = hs.task.new("/bin/bash", function(exitCode)
      setState("ready")
      if exitCode ~= 0 then
        checkHealth()
      end
    end, { SCRIPT, text })

    speakTask:start()
  end)
end

-- Stop speaking
local function stopSpeaking()
  os.execute("pkill -x ffplay 2>/dev/null; pkill -x afplay 2>/dev/null")
  if speakTask and speakTask:isRunning() then
    speakTask:terminate()
  end
  setState("ready")
end

hs.hotkey.bind({"alt"}, "s", speakSelection)
hs.hotkey.bind({"alt", "shift"}, "s", stopSpeaking)
