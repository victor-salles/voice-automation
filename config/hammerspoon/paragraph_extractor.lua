--- paragraph_extractor.lua
--- Extracts paragraphs from the focused app via macOS Accessibility API.
---
--- Single responsibility: read text + cursor from any app, return structured data.
--- Does NOT know about TTS, sessions, or HUD.

local M = {}

local SCRIPT_DIR = os.getenv("HOME") .. "/code/voice-automation/scripts"
local TMP_TEXT = "/tmp/voice-extract-text.txt"

--- Get the currently focused UI element via AX.
--- @return hs.axuielement|nil
local function focusedElement()
    local sys = hs.axuielement.systemWideElement()
    if not sys then return nil end
    return sys:attributeValue("AXFocusedUIElement")
end

--- Read AXValue (full text) from an element, with fallbacks.
--- @param el hs.axuielement
--- @return string|nil
local function readText(el)
    -- Direct AXValue (TextEdit, Notes, VS Code, etc.)
    local text = el:attributeValue("AXValue")
    if text and #text > 0 then return text end

    -- Some apps expose text via AXDescription or AXHelp
    text = el:attributeValue("AXDescription")
    if text and #text > 50 then return text end

    return nil
end

--- Read cursor offset from AXSelectedTextRange.
--- @param el hs.axuielement
--- @return number
local function readCursorOffset(el)
    local range = el:attributeValue("AXSelectedTextRange")
    if range and range.loc then
        return range.loc
    end
    return 0
end

--- Call Python segmenter on text, returns parsed JSON table.
--- @param text string
--- @param cursorOffset number
--- @return table|nil, string|nil
local function callSegmenter(text, cursorOffset)
    -- Write to temp file to avoid shell escaping
    local f = io.open(TMP_TEXT, "w")
    if not f then return nil, "Cannot write temp file" end
    f:write(text)
    f:close()

    local cmd = string.format(
        'python3 "%s/segment_paragraphs.py" --cursor-offset %d < "%s"',
        SCRIPT_DIR, cursorOffset, TMP_TEXT
    )
    local output, status = hs.execute(cmd)
    if not status then return nil, "Segmenter failed" end

    local ok, result = pcall(hs.json.decode, output)
    if not ok or not result then return nil, "Bad JSON from segmenter" end
    if not result.paragraphs or #result.paragraphs == 0 then
        return nil, "No paragraphs found"
    end

    return result, nil
end

--- Extract paragraphs from the focused app.
--- @return table|nil  {paragraphs: string[], currentIndex: number, total: number}
--- @return string|nil  error message
function M.extract()
    local el = focusedElement()
    if not el then return nil, "No focused element" end

    local text = readText(el)
    local cursorOffset = readCursorOffset(el)

    -- Fallback: use selected text as a single paragraph
    if not text then
        local selected = el:attributeValue("AXSelectedText")
        if selected and #selected > 0 then
            return { paragraphs = { selected }, currentIndex = 0, total = 1 }, nil
        end
        return nil, "No text accessible — select a paragraph first"
    end

    return callSegmenter(text, cursorOffset)
end

--- Quick probe: does the focused element have readable text?
--- Used by HUD suggestion mode. Cheap, no Python call.
--- @return boolean
function M.hasReadableText()
    local el = focusedElement()
    if not el then return false end
    local text = el:attributeValue("AXValue")
    return text ~= nil and #text > 50
end

return M
