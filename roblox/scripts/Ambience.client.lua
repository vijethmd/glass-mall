-- What Glass City sounds like. Two kinds of sound:
--   * in a place: every part with an Ambience StringValue plays its loop from where it is
--     (bossa nova in the cafés, jazz in the sky bars, the club, the fountain, the food court)
--   * all around you: the city by day or night, traffic near the big roads, waves and gulls
--     on the beach, birds or crickets in the park and the suburbs, wind high up, the mall's
--     hum inside it and the rain when it rains. These fade with where you are.
-- The Sound button mutes it all (the lifts' music too).
local Players = game:GetService("Players")
local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local SoundService = game:GetService("SoundService")
local TweenService = game:GetService("TweenService")

local CityData = require(ReplicatedStorage:WaitForChild("CityData"))
local player = Players.LocalPlayer
local MAP = CityData.MAP

-- id, volume, distance at full volume, distance where it fades out (studs)
local KEYS = {
	lobby = { 9112753321, 0.3, 12, 70 },
	office = { 9112838161, 0.25, 10, 60 },
	servers = { 9118747853, 0.18, 6, 40 },
	zen = { 9046862941, 0.3, 8, 50 },
	funk = { 1840434670, 0.35, 8, 50 },
	kids = { 9112811007, 0.25, 10, 55 },
	cafe = { 1837070127, 0.3, 8, 50 },
	restaurant = { 9112862817, 0.3, 10, 60 },
	bowling = { 9038367768, 0.32, 10, 60 },
	lounge = { 1845341094, 0.35, 10, 70 },
	club = { 1839239106, 0.6, 14, 110 },
	piano = { 9045766377, 0.35, 8, 55 },
	pool = { 9046863253, 0.35, 10, 70 },
	gym = { 1847680891, 0.32, 10, 60 },
	arcade = { 9112812430, 0.25, 12, 80 },
	mall = { 1847680839, 0.22, 30, 190 },
	foodcourt = { 9112862413, 0.35, 20, 120 },
	fountain = { 9120557315, 0.55, 12, 110 },
	playground = { 9112842611, 0.4, 12, 110 },
	marina = { 9112827718, 0.35, 10, 90 },
}
-- the sounds all around you
local BED = {
	cityDay = { 9112758786, 0.22 }, cityNight = { 9112759347, 0.22 }, traffic = { 9112784190, 0.3 },
	waves = { 9117143192, 0.6 }, gulls = { 9118858002, 0.3 }, birds = { 9112835056, 0.3 },
	crickets = { 9112764573, 0.3 }, wind = { 9114057128, 0.35 }, mallHum = { 9112787259, 0.28 },
	rain = { 9112853287, 0.5 },
}

local master = Instance.new("SoundGroup")
master.Name = "City"
master.Volume = 1
master.Parent = SoundService

local function sound(id, parent, volume, looped)
	local s = Instance.new("Sound")
	s.SoundId = "rbxassetid://" .. id
	s.Volume = volume
	s.Looped = looped ~= false
	s.SoundGroup = master
	s.Parent = parent
	return s
end

-- ------------------------------------------------------------------ sounds in places
local function hook(part, key)
	local k = KEYS[key]
	if not k or part:FindFirstChild("AmbienceSound") then
		return
	end
	local s = sound(k[1], part, k[2])
	s.Name = "AmbienceSound"
	s.RollOffMode = Enum.RollOffMode.InverseTapered
	s.RollOffMinDistance = k[3]
	s.RollOffMaxDistance = k[4]
	s.TimePosition = math.random() * 20
	s:Play()
end
for _, d in ipairs(workspace:GetDescendants()) do
	if d:IsA("StringValue") and d.Name == "Ambience" and d.Parent and d.Parent:IsA("BasePart") then
		hook(d.Parent, d.Value)
	end
end
workspace.DescendantAdded:Connect(function(d)
	if d:IsA("StringValue") and d.Name == "Ambience" then
		task.defer(function()
			if d.Parent and d.Parent:IsA("BasePart") then
				hook(d.Parent, d.Value)
			end
		end)
	end
end)

-- ------------------------------------------------------------------ sounds all around
local beds = {}
for name, b in pairs(BED) do
	local s = sound(b[1], SoundService, 0)
	s.Name = name
	s:Play()
	beds[name] = { sound = s, peak = b[2], level = 0 }
end

local function inRect(p, r, m)
	m = m or 0
	return p.X >= r[1] - m and p.X <= r[3] + m and p.Z >= r[2] - m and p.Z <= r[4] + m
end
local function distRect(p, r)
	local dx = math.max(r[1] - p.X, 0, p.X - r[3])
	local dz = math.max(r[2] - p.Z, 0, p.Z - r[4])
	return math.sqrt(dx * dx + dz * dz)
end

local params = RaycastParams.new()
params.FilterType = Enum.RaycastFilterType.Exclude
local function indoors(pos)
	local ignore = { player.Character }
	params.FilterDescendantsInstances = ignore
	local hit = workspace:Raycast(pos, Vector3.new(0, 90, 0), params)
	return hit ~= nil and hit.Instance.Transparency < 0.9
end

local parks = MAP.parks
local suburbs, district = nil, {}
for _, d in ipairs(MAP.districts) do
	district[d[1]] = d[2]
end
suburbs = district.Suburbs
local sand = MAP.sand

-- the Sound button
local gui = Instance.new("ScreenGui")
gui.Name = "SoundToggle"
gui.ResetOnSpawn = false
gui.Parent = player:WaitForChild("PlayerGui")
local button = Instance.new("TextButton")
button.AnchorPoint = Vector2.new(0, 0.5)
button.Size = UDim2.new(0, 120, 0, 42)
button.Position = UDim2.new(0, 16, 0.5, 150)
button.BackgroundColor3 = Color3.fromRGB(14, 20, 24)
button.BackgroundTransparency = 0.1
button.Font = Enum.Font.GothamBold
button.TextSize = 15
button.TextColor3 = Color3.fromRGB(120, 225, 245)
button.Text = "Sound: on"
button.Parent = gui
Instance.new("UICorner", button).CornerRadius = UDim.new(0, 21)
local muted = false
button.Activated:Connect(function()
	muted = not muted
	button.Text = muted and "Sound: off" or "Sound: on"
	master.Volume = muted and 0 or 1
	for _, d in ipairs(workspace:GetDescendants()) do
		if d:IsA("Sound") and not d.SoundGroup then
			if muted then
				d:SetAttribute("Volume", d.Volume)
				d.Volume = 0
			elseif d:GetAttribute("Volume") then
				d.Volume = d:GetAttribute("Volume")
			end
		end
	end
end)

while true do
	task.wait(0.35)
	local cam = workspace.CurrentCamera
	if cam then
		local p = cam.CFrame.Position
		local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
		local at = root and root.Position or p
		local t = Lighting.ClockTime
		local night = t < 6.2 or t > 18.2
		local inside = indoors(at)
		local inMall = inRect(at, MAP.mall) and at.Y < 75
		local raining = workspace:GetAttribute("Weather") == "Rain"
		local out = inside and 0.25 or 1
		local want = {}
		want.cityDay = (night and 0 or 1) * out
		want.cityNight = (night and 1 or 0) * out
		local road = math.huge
		for _, r in ipairs(MAP.roads) do
			road = math.min(road, distRect(at, r))
		end
		want.traffic = math.clamp(1 - road / 140, 0, 1) * out * (at.Y > 200 and 0.3 or 1)
		local beach = distRect(at, sand)
		want.waves = math.clamp(1 - beach / 260, 0, 1) * out
		want.gulls = night and 0 or math.clamp(1 - beach / 180, 0, 1) * out
		local green = 0
		for _, r in ipairs(parks) do
			if inRect(at, r, 20) then
				green = 1
			end
		end
		if suburbs and inRect(at, suburbs, 10) then
			green = math.max(green, 0.8)
		end
		want.birds = (night and 0 or green) * out
		want.crickets = (night and green or 0) * out
		want.wind = math.clamp((at.Y - 120) / 300, 0, 1) * (inside and 0.3 or 1)
		want.mallHum = inMall and inside and 1 or 0
		want.rain = raining and (inside and 0.35 or 1) or 0
		for name, b in pairs(beds) do
			local target = (want[name] or 0) * b.peak
			b.level = b.level + (target - b.level) * 0.25
			b.sound.Volume = b.level
		end
	end
end
