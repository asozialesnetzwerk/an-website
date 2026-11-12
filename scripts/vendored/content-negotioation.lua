-- content-negotiation.lua
--
-- Summary: perform custom content negotiation via lighttpd mod_magnet
--
-- Notes: various filesystem naming conventions might be used to place
-- lang and/or encoding extensions prior to original file extension,
-- or afterwards.  This implementation places lang before and encoding after,
-- demonstrationg how to implement either.
--
--
-- Copyright (c) 2017, Glenn Strauss (gstrauss () gluelogic.com), incremental
-- All rights reserved.
--
-- License: 3-clause BSD
--
-- Redistribution and use in source and binary forms, with or without
-- modification, are permitted provided that the following conditions are met:
--
-- - Redistributions of source code must retain the above copyright notice, this
--   list of conditions and the following disclaimer.
--
-- - Redistributions in binary form must reproduce the above copyright notice,
--   this list of conditions and the following disclaimer in the documentation
--   and/or other materials provided with the distribution.
--
-- - Neither the name of the 'incremental' nor the names of its contributors may
--   be used to endorse or promote products derived from this software without
--   specific prior written permission.
--
-- THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
-- AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
-- IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
-- ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
-- LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
-- CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
-- SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
-- INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
-- CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
-- ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
-- THE POSSIBILITY OF SUCH DAMAGE.


function parse_HTTP_list (header)

    -- parse HTTP list from given request header
    -- There are *many* ways to parse strings in Lua, some more efficient than
    -- others, but none are a one-size-fits-all scenarios.  This is but one
    -- solution and has not been optimized.  Better solutions are welcomed.
    -- For HTTP list parsing with qvalues, the following assumes *no*
    -- quoted-strings containing the ',' or ';' delimiters, which is not fully
    -- RFC-compliant, but is also a reasonable simplification for headers
    -- including Accept-Language and Accept-Encoding, which generally have
    -- well-known sets of values.  Given that the following does not handle
    -- quoted-string, simplify string by removing all whitespace.  Then split
    -- on ',', and for each result, split on ';' and parse for qvalue.  Assume
    -- ';' is followed by "q=..." and nothing else, or ignore.  Ignore items
    -- with q=0 (or equivalent) since default content file will be provided if
    -- there is no better match.

    local tokens = {}, token
    if (not header) then return tokens end
    header = string.gsub(header, "%s+", "")
    for token in string.gmatch(header, "[^,]+") do
        local b, e = string.find(token, ";q=", 1, 1)
        local n = 1
        if b then
            n = tonumber(token:sub(e+1))
            token = (n ~= nil and n > 0) and token:sub(1, b-1) or ""
        else
            b = string.find(token, ";", 1, 1)
            if b then token = token:sub(1, b-1) end
        end
        if (token ~= "") then
            table.insert(tokens, { n, token })
        else
            -- ignore (skip) if invalid (e.g. empty token or invalid qvalue)
        end
    end

    -- sort on qvalue and return simple ordered, indexed list
    table.sort(tokens, function (v1,v2) return v1[1] > v2[1] end)
    local v
    local list = {}
    for _, v in ipairs(tokens) do
        table.insert(list, v[2])
    end
    return list

end


function negotiate_language (path)

    local langs = parse_HTTP_list(lighty.request["Accept-Language"])
    if not langs[1] then return 0 end

    -- split path into basepath and ext
    -- basepath ends in '.' for use below, and if present, ext begins with '.'
    local ext = string.match(path, "(%.[^/]+)$")
    local basepath
    if (ext) then
        basepath = path:sub(1, -#ext)
    else
        basepath = path .. "."
        ext = ""
    end

    -- check if basepath .. lang .. ext exists
    local lang
    for _, lang in ipairs(langs) do
        local attr = nil
        if (string.find(lang, "/", 1, 1)) then
            -- skip lang containing '/'
            -- security: avoid path traversal
            -- since lang is used in filenames, lang must not contain '/'
        else
        if (lang == "en-US" or lang == "en") then
            -- (optional optimization; remove condition if should not apply)
            -- skip if default file is for "en-US" and "en"
            -- (assumes Accept-Language contains only en-US and/or en,
            --  or they are last, i.e. other languages are preferred)
        else
            path = basepath .. lang .. ext
            attr = lighty.stat(path)
        end
        end
        if (attr and attr["is_file"]) then
            lighty.env["physical.path"] = path
            lighty.env["physical.rel-path"] = (#ext)
              and lighty.env["physical.rel-path"]:sub(1, -#ext) .. lang .. ext
              or lighty.env["physical.rel-path"] .. "." .. lang
            return 0
        end
    end

    return 0

end


local encoding_exts =
  {
    ["br"]    = ".br"                          -- brotli
   ,["gzip"]  = ".gz",  ["x-gzip"]  = ".gz"    -- gzip
-- ,["bzip2"] = ".bz2", ["x-bzip2"] = ".bz2"   -- bzip2
  }

function negotiate_encoding (path, content_type)

    local encs = parse_HTTP_list(lighty.request["Accept-Encoding"])
    if not encs[1] then return 0 end

    -- check if pre-encoded file exists with mapped extension
    local enc
    local basepath = path
    for _, enc in ipairs(encs) do
        local ext = encoding_exts[enc:gsub(".*", string.lower)]
        if (ext) then
            path = basepath .. ext
            local attr = lighty.stat(path)
            if (attr and attr["is_file"]) then
                lighty.env["physical.path"] = path
                lighty.env["physical.rel-path"] =
                  lighty.env["physical.rel-path"] .. ext
                lighty.header["Content-Encoding"] = enc
                if (content_type) then
                    lighty.header["Content-Type"] = content_type
                else
                    lighty.header["Content-Type"] = "application/octet-stream"
                end
                return 0
            end
        end
    end

    return 0

end


--
-- content negotiation
--

-- check that default content file exists (or index-file)
local attr = lighty.stat(lighty.env["physical.path"])
if (not attr) then return 0 end
if (not attr["is_file"]) then
    if (attr["is_dir"]) then
        -- check for index file (code below checks only for index.html)
        local path = lighty.env["physical.path"]
        local indexfile =
          string.sub(path, -1) == "/" and "index.html" or "/index.html"
        path = path .. indexfile
        attr = lighty.stat(path)
        if (not attr or not attr["is_file"]) then return 0 end
        -- (below assignments not required; merely shortcut mod_indexfile)
        lighty.env["physical.path"] = path
        lighty.env["physical.rel-path"] =
          lighty.env["physical.rel-path"] .. indexfile
    else
        return 0
    end
end

negotiate_language(lighty.env["physical.path"])

negotiate_encoding(lighty.env["physical.path"], attr["content-type"])

return 0
