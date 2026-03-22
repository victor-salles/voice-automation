-- Kokoro TTS — Hammerspoon integration
-- ⌥S  → speak selected text
-- ⌥⇧S → stop speaking
--
-- Install: copy or require() from ~/.hammerspoon/init.lua
--   require("kokoro")  -- if symlinked to ~/.hammerspoon/kokoro.lua

local speakTask = nil
local SCRIPT = os.getenv("HOME") .. "/code/voice-automation/scripts/speak.sh"

local function speakSelection()
  -- Copy whatever is currently selected
  hs.eventtap.keyStroke({"cmd"}, "c")

  hs.timer.doAfter(0.3, function()
    local text = hs.pasteboard.getContents()

    if not text or text == "" then
      hs.notify.new({ title = "Kokoro TTS", informativeText = "No text selected" }):send()
      return
    end

    -- Kill any previous playback
    if speakTask and speakTask:isRunning() then
      os.execute("pkill afplay 2>/dev/null")
      speakTask:terminate()
    end

    speakTask = hs.task.new("/bin/bash", function(exitCode, stdOut, stdErr)
      if exitCode ~= 0 then
        hs.notify.new({ title = "Kokoro TTS", informativeText = "Error: " .. (stdErr or "unknown") }):send()
      end
    end, { SCRIPT, text })

    speakTask:start()
  end)
end

local function stopSpeaking()
  os.execute("pkill afplay 2>/dev/null")
  if speakTask and speakTask:isRunning() then
    speakTask:terminate()
  end
  hs.notify.new({ title = "Kokoro TTS", informativeText = "Stopped" }):send()
end

hs.hotkey.bind({"alt"}, "s", speakSelection)
hs.hotkey.bind({"alt", "shift"}, "s", stopSpeaking)
