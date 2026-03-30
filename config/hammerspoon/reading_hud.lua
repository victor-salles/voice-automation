--- reading_hud.lua
--- Always-on-top floating reading bar using hs.canvas.
---
--- Single responsibility: render HUD state, emit user interactions as callbacks.
--- Does NOT know about sessions, TTS, or accessibility.

local M = {}

---------------------------------------------------------------------------
-- Config
---------------------------------------------------------------------------

local WIDTH         = 320
local HEIGHT        = 34
local CORNER_R      = 12
local MARGIN        = 16   -- from screen edge
local FONT_MAIN     = { name = ".AppleSystemUIFont", size = 13 }
local FONT_SMALL    = { name = ".AppleSystemUIFont", size = 11 }

local C = {
    bg      = { red = 0.11, green = 0.11, blue = 0.13, alpha = 0.88 },
    text    = { red = 0.88, green = 0.88, blue = 0.90, alpha = 1 },
    accent  = { red = 0.30, green = 0.78, blue = 0.52, alpha = 1 },
    dim     = { red = 0.50, green = 0.50, blue = 0.52, alpha = 0.70 },
    pause   = { red = 0.95, green = 0.75, blue = 0.20, alpha = 1 },
}

---------------------------------------------------------------------------
-- Callbacks — set by composition root
---------------------------------------------------------------------------

M.onPrev          = function() end
M.onPauseToggle   = function() end
M.onNext          = function() end
M.onStop          = function() end
M.onStartReading  = function() end

---------------------------------------------------------------------------
-- Internal state
---------------------------------------------------------------------------

local canvas = nil
local waveTimer = nil
local waveFrame = 0

local function screenBottomRight()
    local scr = hs.screen.mainScreen():frame()
    return {
        x = scr.w - WIDTH - MARGIN,
        y = scr.h - HEIGHT - MARGIN - 40,  -- above Dock
    }
end

---------------------------------------------------------------------------
-- Rendering helpers
---------------------------------------------------------------------------

local function bgRect()
    return {
        type = "rectangle",
        frame = { x = 0, y = 0, w = WIDTH, h = HEIGHT },
        roundedRectRadii = { xRadius = CORNER_R, yRadius = CORNER_R },
        fillColor = C.bg,
        action = "fill",
    }
end

local function textElement(frame, str, style)
    return {
        type = "text",
        frame = frame,
        text = hs.styledtext.new(str, style),
    }
end

---------------------------------------------------------------------------
-- Waveform animation
---------------------------------------------------------------------------

local WAVE_BARS    = 4
local WAVE_X       = 118        -- starting x of waveform area
local WAVE_BAR_W   = 3
local WAVE_GAP     = 2
local WAVE_MAX_H   = 14
local WAVE_MIN_H   = 3
local WAVE_Y       = 10        -- top baseline for bars

--- Generate bar heights for a given animation frame.
--- Uses simple sine offsets per bar for organic movement.
local function waveHeights(frame)
    local heights = {}
    for i = 1, WAVE_BARS do
        local phase = (frame * 0.3) + (i * 1.2)
        local h = WAVE_MIN_H + (WAVE_MAX_H - WAVE_MIN_H) * (0.5 + 0.5 * math.sin(phase))
        heights[i] = math.floor(h)
    end
    return heights
end

--- Return canvas elements for waveform bars at current frame.
local function waveElements(frame)
    local heights = waveHeights(frame)
    local elems = {}
    for i = 1, WAVE_BARS do
        local h = heights[i]
        local x = WAVE_X + (i - 1) * (WAVE_BAR_W + WAVE_GAP)
        local y = WAVE_Y + (WAVE_MAX_H - h) / 2  -- vertically centered
        elems[i] = {
            type = "rectangle",
            frame = { x = x, y = y, w = WAVE_BAR_W, h = h },
            roundedRectRadii = { xRadius = 1, yRadius = 1 },
            fillColor = C.accent,
            action = "fill",
        }
    end
    return elems
end

--- Return static (paused) waveform bars — all at minimum height.
local function wavePausedElements()
    local elems = {}
    for i = 1, WAVE_BARS do
        local x = WAVE_X + (i - 1) * (WAVE_BAR_W + WAVE_GAP)
        elems[i] = {
            type = "rectangle",
            frame = { x = x, y = WAVE_Y + (WAVE_MAX_H - WAVE_MIN_H) / 2, w = WAVE_BAR_W, h = WAVE_MIN_H },
            roundedRectRadii = { xRadius = 1, yRadius = 1 },
            fillColor = C.pause,
            action = "fill",
        }
    end
    return elems
end

local function stopWaveTimer()
    if waveTimer then waveTimer:stop(); waveTimer = nil end
end

---------------------------------------------------------------------------
-- Draw states
---------------------------------------------------------------------------

local function drawIdle()
    if not canvas then return end
    canvas:replaceElements(
        bgRect(),
        textElement(
            { x = 12, y = 6, w = WIDTH - 24, h = 22 },
            "▶  Read from here                 ⌥R",
            { font = FONT_MAIN, color = C.accent }
        )
    )
    canvas:mouseCallback(function(_, _, _, x, _)
        M.onStartReading()
    end)
end

local function drawPlaying(session, paused)
    if not canvas then return end

    local idx   = session.currentIndex or 1
    local total = session.total or 0
    local para  = (session.paragraphs or {})[idx] or ""
    local preview = (#para > 22) and (para:sub(1, 22) .. "…") or para

    local pauseIcon = paused and "▶" or "⏸"
    local pauseColor = paused and C.pause or C.text

    -- Waveform bars (animated or static)
    local waveBars = paused and wavePausedElements() or waveElements(waveFrame)

    -- Build element list: bg + controls + waveform + progress + preview
    local elems = {
        bgRect(),
        textElement({ x = 10, y = 6, w = 22, h = 22 }, "◀", { font = FONT_MAIN, color = C.dim }),
        textElement({ x = 36, y = 6, w = 22, h = 22 }, pauseIcon, { font = FONT_MAIN, color = pauseColor }),
        textElement({ x = 62, y = 6, w = 28, h = 22 }, "▶▶", { font = FONT_MAIN, color = C.dim }),
        textElement({ x = 94, y = 6, w = 22, h = 22 }, "■", { font = FONT_MAIN, color = C.dim }),
    }
    -- Append waveform bars
    for _, bar in ipairs(waveBars) do
        elems[#elems + 1] = bar
    end
    -- Progress + preview (shifted right to make room for waveform)
    elems[#elems + 1] = textElement(
        { x = 142, y = 7, w = 55, h = 20 },
        string.format("§%d/%d", idx, total),
        { font = FONT_SMALL, color = C.accent }
    )
    elems[#elems + 1] = textElement(
        { x = 200, y = 7, w = WIDTH - 210, h = 20 },
        preview,
        { font = FONT_SMALL, color = C.dim }
    )

    canvas:replaceElements(table.unpack(elems))

    -- Click zones by x-coordinate ranges
    canvas:mouseCallback(function(_, _, _, x, _)
        if     x < 34  then M.onPrev()
        elseif x < 60  then M.onPauseToggle()
        elseif x < 92  then M.onNext()
        elseif x < 120 then M.onStop()
        end
    end)

    -- Start waveform animation timer if playing
    stopWaveTimer()
    if not paused then
        waveTimer = hs.timer.doEvery(0.15, function()
            waveFrame = waveFrame + 1
            if canvas and session and session.state ~= "idle" then
                -- Only update the waveform bars (elements 6–9), not the whole canvas
                local newBars = waveElements(waveFrame)
                for i, bar in ipairs(newBars) do
                    pcall(function() canvas[5 + i] = bar end)
                end
            end
        end)
    end
end

---------------------------------------------------------------------------
-- Public API
---------------------------------------------------------------------------

function M.create()
    if canvas then canvas:delete() end
    local pos = screenBottomRight()
    canvas = hs.canvas.new({ x = pos.x, y = pos.y, w = WIDTH, h = HEIGHT })
    canvas:level(hs.canvas.windowLevels.floating)
    canvas:behaviorAsLabels({ "canJoinAllSpaces", "stationary" })
    drawIdle()
    canvas:show()
end

--- Update HUD to reflect session state.
--- @param state string  "idle"|"playing"|"paused"
--- @param session table  session data from reading_session
function M.update(state, session)
    if not canvas then return end
    if state == "idle" then
        stopWaveTimer()
        drawIdle()
    else
        drawPlaying(session, state == "paused")
    end
end

function M.destroy()
    stopWaveTimer()
    if canvas then
        canvas:delete()
        canvas = nil
    end
end

return M
