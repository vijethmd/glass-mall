-- What the city's scripts share, written by build_place.py: every place the explorer passport
-- stamps and the shapes the map draws. All positions are in studs.
local CityData = {}

-- { name, where, x0, z0, x1, z1, y0, y1 }, most specific first
CityData.DISCOVERIES = __DISCOVERIES__

-- rectangles are { x0, z0, x1, z1 }
CityData.MAP = __MAP__

-- one stamp per name and place, however many rectangles it takes (the ring highway has four)
CityData.KEYS = {}
CityData.KEY_OF = {}
local seen = {}
for i, d in ipairs(CityData.DISCOVERIES) do
	local key = d[1] .. "|" .. d[2]
	if not seen[key] then
		seen[key] = true
		table.insert(CityData.KEYS, key)
	end
	CityData.KEY_OF[i] = key
end

-- the first (most specific) discovery a position is in, and its key
function CityData.find(p)
	for i, d in ipairs(CityData.DISCOVERIES) do
		if p.X >= d[3] and p.X <= d[5] and p.Z >= d[4] and p.Z <= d[6] and p.Y >= d[7] and p.Y <= d[8] then
			return i, d, CityData.KEY_OF[i]
		end
	end
	return nil
end

return CityData
