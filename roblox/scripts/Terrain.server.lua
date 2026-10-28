-- Terrain that a place file of parts can't hold: the bay east of the highway with its
-- beach, the lake in Central Park and the grassy hills round the city.
local terrain = workspace.Terrain
local T = __TERRAIN__ -- boxes are { centre x, y, z, size x, y, z } in studs; balls { x, y, z, radius }

terrain:SetMaterialColor(Enum.Material.Grass, Color3.fromRGB(96, 140, 66))
local clouds = Instance.new("Clouds")
clouds.Cover = 0.55
clouds.Density = 0.65
clouds.Color = Color3.fromRGB(245, 245, 248)
clouds.Parent = terrain
terrain:SetMaterialColor(Enum.Material.Sand, Color3.fromRGB(226, 206, 160))
terrain.WaterColor = Color3.fromRGB(28, 116, 140)
terrain.WaterTransparency = 0.55
terrain.WaterReflectance = 0.5
terrain.WaterWaveSize = 0.12
terrain.WaterWaveSpeed = 8

-- big fills go in tiles of at most 512 studs
local function block(b, material)
	local nx, nz = math.ceil(b[4] / 512), math.ceil(b[6] / 512)
	local tx, tz = b[4] / nx, b[6] / nz
	for i = 0, nx - 1 do
		for j = 0, nz - 1 do
			local px = b[1] - b[4] / 2 + tx * (i + 0.5)
			local pz = b[3] - b[6] / 2 + tz * (j + 0.5)
			terrain:FillBlock(CFrame.new(px, b[2], pz), Vector3.new(tx, b[5], tz), material)
		end
		task.wait()
	end
end

-- the lake first, then let the rowing boats float on it
block(T.lakeBed, Enum.Material.Mud)
block(T.lake, Enum.Material.Water)
local floating = workspace.City.Park:FindFirstChild("Floating")
if floating then
	for _, boat in ipairs(floating:GetChildren()) do
		if boat:IsA("BasePart") then
			boat.Anchored = false
		end
	end
end

for _, b in ipairs(T.water) do
	block(b, Enum.Material.Water)
end
for _, b in ipairs(T.sand) do
	block(b, Enum.Material.Sand)
end
-- the beach shelving into the sea: a wedge whose high edge faces the city (west)
for _, b in ipairs(T.wedges) do
	local nz = math.ceil(b[6] / 512)
	local tz = b[6] / nz
	for j = 0, nz - 1 do
		local c = Vector3.new(b[1], b[2], b[3] - b[6] / 2 + tz * (j + 0.5))
		terrain:FillWedge(CFrame.lookAt(c, c + Vector3.new(1, 0, 0)), Vector3.new(tz, b[5], b[4]), Enum.Material.Sand)
	end
end
for _, h in ipairs(T.hills) do
	terrain:FillBall(Vector3.new(h[1], h[2], h[3]), h[4], Enum.Material.Grass)
	task.wait()
end
for _, r in ipairs(T.rocks) do
	terrain:FillBall(Vector3.new(r[1], r[2], r[3]), r[4], Enum.Material.Rock)
end
