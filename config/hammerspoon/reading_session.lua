--- reading_session.lua
--- State machine for paragraph-by-paragraph reading sessions.
---
--- Single responsibility: manage session state and transitions.
--- Does NOT know about Hammerspoon, TTS, or UI — communicates via callbacks.

local M = {}

---------------------------------------------------------------------------
-- State
---------------------------------------------------------------------------

--- @class Session
--- @field paragraphs string[]
--- @field currentIndex number  1-based Lua index
--- @field total number
--- @field state string  "idle"|"playing"|"paused"|"loading"
--- @field preSynthPath string|nil  path to pre-synthesized next paragraph

local function newSession()
    return {
        paragraphs   = {},
        currentIndex  = 1,
        total         = 0,
        state         = "idle",
    }
end

M._session = newSession()

---------------------------------------------------------------------------
-- Callbacks — set by the composition root (reading.lua)
---------------------------------------------------------------------------

--- Called when state or currentIndex changes.
--- @type fun(state: string, session: Session)
M.onStateChange = function() end

--- Speak text, call onDone when playback finishes.
--- @type fun(text: string, onDone: fun())
M.onSpeak = function() end

--- Play a pre-synthesized audio file, call onDone when finished.
--- @type fun(path: string, onDone: fun())
M.onSpeakCached = function() end

--- Pre-synthesize text to outputPath, call onReady(path) when file is written.
--- @type fun(text: string, outputPath: string, onReady: fun(path: string))
M.onPreSynth = function() end

--- Stop any active playback immediately.
--- @type fun()
M.onStopPlayback = function() end

---------------------------------------------------------------------------
-- Internal helpers
---------------------------------------------------------------------------

local function setState(state)
    M._session.state = state
    M.onStateChange(state, M._session)
end

local function currentParagraph()
    return M._session.paragraphs[M._session.currentIndex]
end

local function hasNext()
    return M._session.currentIndex < M._session.total
end

--- Pre-synthesis buffer: stores paths keyed by paragraph index.
--- Allows buffering N+1 and N+2 simultaneously.
local preCache = {}  -- { [index] = "/tmp/voice-cache/para_N.mp3" }

--- Queue pre-synthesis for paragraphs N+1 and N+2 (if they exist).
local function preSynthAhead()
    for offset = 1, 2 do
        local idx = M._session.currentIndex + offset
        if idx <= M._session.total and not preCache[idx] then
            local text = M._session.paragraphs[idx]
            local outPath = string.format("/tmp/voice-cache/para_%d.mp3", idx)
            M.onPreSynth(text, outPath, function(path)
                preCache[idx] = path
            end)
        end
    end
end

--- Get pre-cached audio for an index, or nil.
local function popCached(idx)
    local path = preCache[idx]
    preCache[idx] = nil
    return path
end

--- Clear all pre-cached files.
local function clearPreCache()
    preCache = {}
end

--- Advance to next paragraph after playback completes.
local function onPlaybackDone()
    if M._session.state ~= "playing" then return end

    if not hasNext() then
        M.stop()
        return
    end

    M._session.currentIndex = M._session.currentIndex + 1
    local cached = popCached(M._session.currentIndex)

    setState("playing")
    preSynthAhead()

    if cached then
        M.onSpeakCached(cached, onPlaybackDone)
    else
        M.onSpeak(currentParagraph(), onPlaybackDone)
    end
end

---------------------------------------------------------------------------
-- Public API
---------------------------------------------------------------------------

--- Start a reading session.
--- @param data table  {paragraphs: string[], currentIndex: number, total: number}
---                     currentIndex is 0-based (from Python); converted to 1-based internally.
function M.start(data)
    M._session = newSession()
    M._session.paragraphs   = data.paragraphs
    M._session.total         = data.total or #data.paragraphs

    local idx = (data.currentIndex or 0) + 1  -- 0-based → 1-based
    M._session.currentIndex  = math.max(1, math.min(idx, M._session.total))

    local para = currentParagraph()
    if not para then
        M.stop()
        return
    end

    clearPreCache()
    setState("playing")
    preSynthAhead()
    M.onSpeak(para, onPlaybackDone)
end

--- Toggle pause / resume.
function M.pauseToggle()
    local s = M._session.state
    if s == "playing" then
        setState("paused")
    elseif s == "paused" then
        setState("playing")
    end
    -- Actual SIGSTOP/SIGCONT is handled by the composition root
end

--- Skip to next paragraph.
function M.next()
    if M._session.state == "idle" then return end
    if not hasNext() then return end

    M.onStopPlayback()
    M._session.currentIndex = M._session.currentIndex + 1
    local cached = popCached(M._session.currentIndex)

    setState("playing")
    preSynthAhead()

    if cached then
        M.onSpeakCached(cached, onPlaybackDone)
    else
        M.onSpeak(currentParagraph(), onPlaybackDone)
    end
end

--- Go back to previous paragraph.
function M.prev()
    if M._session.state == "idle" then return end
    if M._session.currentIndex <= 1 then return end

    M.onStopPlayback()
    M._session.currentIndex = M._session.currentIndex - 1

    setState("playing")
    preSynthAhead()
    M.onSpeak(currentParagraph(), onPlaybackDone)
end

--- Stop reading, reset session.
function M.stop()
    M.onStopPlayback()
    clearPreCache()
    M._session = newSession()
    setState("idle")
end

--- Read-only access to current session state.
--- @return Session
function M.getSession()
    return M._session
end

return M
