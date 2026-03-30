--- tts_engine.lua — Direct TTS via HTTP to Kokoro (replaces speak.sh chain).
--- Reduces latency from ~500-800ms to ~50-100ms by eliminating 6-process spawning.
--- Single responsibility: synthesis and playback. No session state, no HUD.

local M = {}

local KOKORO_HOST = os.getenv("KOKORO_HOST") or "localhost"
local KOKORO_PORT = os.getenv("KOKORO_PORT") or "8880"
local KOKORO_EN_VOICE = os.getenv("KOKORO_EN_VOICE") or "af_heart"
local KOKORO_PT_VOICE = os.getenv("KOKORO_PT_VOICE") or "pf_dora"

local FFPLAY = (function()
    for _, p in ipairs({ "/opt/homebrew/bin/ffplay", "/usr/local/bin/ffplay" }) do
        if hs.fs.attributes(p) then return p end
    end
    return "ffplay"
end)()

local activeTask, taskGen = nil, 0

--- Detect language: Portuguese if contains PT diacritics or PT-only words.
local function detectLanguage(text)
    -- Strong signal: Portuguese-specific diacritics
    if text:match("[ãçõÃÇÕ]") then return "pt" end
    -- Weaker signal: common PT words at word boundaries (2+ matches needed)
    local lower = text:lower()
    local hits = 0
    for _, w in ipairs({ "não", "também", "você", "então", "está", "isso", "ainda" }) do
        if lower:find(w, 1, true) then hits = hits + 1 end
    end
    if hits >= 1 then return "pt" end
    return "en"
end

--- Clean markdown headers, code blocks, URLs, excessive whitespace.
local function cleanText(text)
    text = text:gsub("^#+%s+", ""):gsub("```[^`]*```", ""):gsub("https?://[%S]+", "")
    text = text:gsub("%s+", " "):match("^%s*(.-)%s*$") or ""
    return text
end

--- Kill active playback and bump generation counter.
local function killActive()
    taskGen = taskGen + 1
    if activeTask then activeTask:terminate(); activeTask = nil end
    hs.execute("pkill -9 ffplay 2>/dev/null; true")
end

--- Synthesize text via HTTP. Write response to outputPath, call onDone(success).
local function synthesize(text, lang, outputPath, onDone)
    local voice = (lang == "pt") and KOKORO_PT_VOICE or KOKORO_EN_VOICE
    local url = string.format("http://%s:%s/v1/audio/speech", KOKORO_HOST, KOKORO_PORT)
    hs.http.asyncPost(url, hs.json.encode({ input = text, voice = voice }),
        { ["Content-Type"] = "application/json" },
        function(code, body, _)
            if code == 200 and body then
                local f = io.open(outputPath, "wb")
                if f then f:write(body); f:close(); if onDone then onDone(true) end; return end
            end
            if onDone then onDone(false) end
        end)
end

--- Play audio file via ffplay. Discard stale callbacks via gen.
local function playAudio(path, gen, onDone)
    activeTask = hs.task.new("/bin/bash", function(_, _, _)
        if taskGen == gen then activeTask = nil; if onDone then onDone() end end
    end, { "-c", string.format('"%s" -nodisp -autoexit "%s"', FFPLAY, path) })
    if activeTask then activeTask:start() end
end

--- Speak text: synthesize + play. Kills active playback first.
function M.speak(text, onDone)
    killActive()
    text = cleanText(text)
    if #text == 0 then if onDone then onDone() end return end
    local lang, tmpPath, gen = detectLanguage(text), "/tmp/voice-tts-" .. os.time() .. ".mp3", taskGen
    synthesize(text, lang, tmpPath, function(ok)
        if taskGen == gen and ok then playAudio(tmpPath, gen, onDone) end
    end)
end

--- Pre-synthesize to file (no playback).
function M.preSynth(text, outputPath, onReady)
    text = cleanText(text)
    if #text == 0 then if onReady then onReady(outputPath) end return end
    synthesize(text, detectLanguage(text), outputPath, function(ok)
        if ok and onReady then onReady(outputPath) end
    end)
end

--- Play pre-synthesized file. Kills active playback first.
function M.playCached(path, onDone)
    killActive()
    playAudio(path, taskGen, onDone)
end

--- Stop all playback.
function M.stop()
    killActive()
end

return M
