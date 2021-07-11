-- cutitout: automatically cut silence from videos
-- Copyright (C) 2020 Wolf Clement

-- This program is free software: you can redistribute it and/or modify
-- it under the terms of the GNU Affero General Public License as published
-- by the Free Software Foundation, either version 3 of the License, or
-- (at your option) any later version.

-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU Affero General Public License for more details.

-- You should have received a copy of the GNU Affero General Public License
-- along with this program.  If not, see <https://www.gnu.org/licenses/>.


local enabled = false
local minutes = {}
local skips = {}

function load_minute(minute)
    local utils = require("mp.utils")
    local scripts_dir = mp.find_config_file("scripts")
    local cutitoutpy = utils.join_path(scripts_dir, "cutitout_shared/cutitout.py")
    local video_path = mp.get_property("path")

    minutes[minute] = "loading"

    mp.command_native_async({
        name = "subprocess",
        capture_stdout = true,
        playback_only = false,
        args = { "python3", cutitoutpy, video_path, tostring(minute - 1) }
    }, function(res, val, err)
        new_skips = loadstring(val.stdout)()

        for _, skip in pairs(new_skips) do table.insert(skips, skip) end
        minutes[minute] = "loaded"
        print(tostring(#new_skips) .. " skips loaded for minute " .. tostring(minute - 1))
    end)
end

-- Whenever time updates...
mp.observe_property("time-pos", "native", function (_, pos)
    if pos == nil then return end
    if not enabled then return end

    -- Check if we should load skips for the current minute
    local current_minute = math.floor(pos / 60.0) + 1
    if minutes[current_minute] == nil then
        load_minute(current_minute)
    end

    -- Check if we should load skips for the next minute
    local next_minute = math.ceil((pos + 1.0) / 60.0) + 1
    if minutes[current_minute] == "loaded" and minutes[next_minute] == nil then
        load_minute(next_minute)
    end

    -- Check if we should skip
    for _, t in pairs(skips) do
        -- t[1] == start time of the skip
        -- t[2] == end time of the skip
        if t[1] <= pos and t[2] > pos then
            print("Skipping to " .. t[2])
            mp.set_property("time-pos", t[2])
            return
        end
    end
end)

-- F12 toggles silence skipping (off by default)
mp.add_key_binding("F12", "toggle_silence_skip", function ()
    enabled = not enabled
    if enabled then
        mp.osd_message("Silence skipping enabled.")
    else
        mp.osd_message("Silence skipping disabled.")
    end
end)

-- Whenever we load another file, we reset skips
mp.register_event("file-loaded", function ()
    minutes = {}
    skips = {}
end)
