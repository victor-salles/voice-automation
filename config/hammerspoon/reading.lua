--- reading.lua
--- Composition root for Reading Mode v2.
---
--- Wires together: paragraph_extractor, reading_session, reading_hud, and tts_engine.
--- This is the only module that knows about all dependencies.
--- Loaded via init.lua: require("reading")

local extractor = require("paragraph_extractor")
local session   = require("reading_session")
local hud       = require("reading_hud")
local tts       = require("tts_engine")

---------------------------------------------------------------------------
-- Session callbacks → TTS engine
---------------------------------------------------------------------------

session.onSpeak = function(text, onDone)
    tts.speak(text, onDone)
end

session.onSpeakCached = function(path, onDone)
    tts.playCached(path, onDone)
end

session.onPreSynth = function(text, outputPath, onReady)
    tts.preSynth(text, outputPath, onReady)
end

session.onStopPlayback = function()
    tts.stop()
end

session.onStateChange = function(state, sess)
    hud.update(state, sess)

    -- Pause/resume ffplay via signals
    if state == "paused" then
        hs.execute("pkill -STOP ffplay 2>/dev/null; true")
    elseif state == "playing" then
        hs.execute("pkill -CONT ffplay 2>/dev/null; true")
    end
end

---------------------------------------------------------------------------
-- HUD callbacks → Session
---------------------------------------------------------------------------

hud.onPrev         = function() session.prev() end
hud.onNext         = function() session.next() end
hud.onPauseToggle  = function() session.pauseToggle() end
hud.onStop         = function() session.stop() end

---------------------------------------------------------------------------
-- Core action
---------------------------------------------------------------------------

local function startReading()
    -- Always stop any existing session before starting fresh
    if session.getSession().state ~= "idle" then
        session.stop()
    end

    local ok, data, err = pcall(function()
        return extractor.extract()
    end)

    if not ok then
        -- pcall caught a Lua error (e.g., AX crash in Electron apps)
        print("[reading] Extraction error: " .. tostring(data))
        hs.notify.new({
            title = "Voice Reading",
            informativeText = "Could not read text from this app",
        }):send()
        return
    end

    if not data then
        hs.notify.new({
            title = "Voice Reading",
            informativeText = err or "No text found",
        }):send()
        return
    end

    session.start(data)
end

hud.onStartReading = startReading

---------------------------------------------------------------------------
-- Hotkeys
---------------------------------------------------------------------------

--- Wrap all hotkey actions in pcall so a Lua error never kills the module.
local function safeCall(fn)
    return function()
        local ok, err = pcall(fn)
        if not ok then print("[reading] Error: " .. tostring(err)) end
    end
end

hs.hotkey.bind({ "alt" }, "R", safeCall(function()
    if session.getSession().state ~= "idle" then
        session.stop()
    else
        startReading()
    end
end))

hs.hotkey.bind({ "alt" }, "]", safeCall(function() session.next() end))
hs.hotkey.bind({ "alt" }, "[", safeCall(function() session.prev() end))
hs.hotkey.bind({ "alt" }, "P", safeCall(function() session.pauseToggle() end))

---------------------------------------------------------------------------
-- Suggestion mode — show HUD prompt when readable text is focused
---------------------------------------------------------------------------

local suggestionTimer = nil

local function checkSuggestion()
    if session.getSession().state ~= "idle" then return end
    -- hasReadableText is cheap — just reads one AX attribute
    -- pcall because AX can throw on some Electron apps
    local ok, readable = pcall(extractor.hasReadableText)
    if ok and readable then
        hud.update("idle", {})
    end
end

local wf = hs.window.filter.new():setDefaultFilter({})
wf:subscribe(hs.window.filter.windowFocused, function()
    if suggestionTimer then suggestionTimer:stop() end
    suggestionTimer = hs.timer.doAfter(0.3, checkSuggestion)
end)

---------------------------------------------------------------------------
-- Init
---------------------------------------------------------------------------

hs.fs.mkdir("/tmp/voice-cache")
hud.create()
print("[reading] Reading Mode v2 loaded — ⌥R to start")

return {
    start = startReading,
    stop  = function() session.stop() end,
}
