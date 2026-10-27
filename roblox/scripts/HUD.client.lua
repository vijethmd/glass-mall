-- Welcome card when you join, and a label showing which mall floor or city district you
-- are in.
local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")

local player = Players.LocalPlayer
local FLOORS = __FLOORS__ -- { y = floor top in studs, name, note }
local FOOTPRINTS = __FOOTPRINTS__ -- each floor's outline, { x, z } in studs
local TERRACE = __TERRACE__
local DISTRICTS = __DISTRICTS__ -- { name, x0, z0, x1, z1 } in studs, first match wins
local BLVD = __BLVD__ -- the boulevard: a point on its edge, its direction and the road's span across

local function inside(x, z, poly)
	local c = false
	local j = #poly
	for i = 1, #poly do
		local a, b = poly[i], poly[j]
		if (a[2] > z) ~= (b[2] > z) and x < (b[1] - a[1]) * (z - a[2]) / (b[2] - a[2]) + a[1] then
			c = not c
		end
		j = i
	end
	return c
end

local gui = Instance.new("ScreenGui")
gui.Name = "MallHUD"
gui.ResetOnSpawn = false
gui.Parent = player:WaitForChild("PlayerGui")

local function corner(parent, r)
	local c = Instance.new("UICorner")
	c.CornerRadius = UDim.new(0, r)
	c.Parent = parent
end

local card = Instance.new("Frame")
card.AnchorPoint = Vector2.new(0.5, 0)
card.Size = UDim2.new(0, 360, 0, 196)
card.Position = UDim2.new(0.5, 0, 0, 64)
card.BackgroundColor3 = Color3.fromRGB(14, 20, 24)
card.BackgroundTransparency = 0.15
card.Parent = gui
corner(card, 12)

local title = Instance.new("TextLabel")
title.Size = UDim2.new(1, -28, 0, 34)
title.Position = UDim2.new(0, 14, 0, 12)
title.BackgroundTransparency = 1
title.Font = Enum.Font.GothamBlack
title.TextSize = 26
title.TextXAlignment = Enum.TextXAlignment.Left
title.TextColor3 = Color3.fromRGB(120, 225, 245)
title.Text = "GLASS CITY"
title.Parent = card

local body = Instance.new("TextLabel")
body.Size = UDim2.new(1, -28, 1, -56)
body.Position = UDim2.new(0, 14, 0, 48)
body.BackgroundTransparency = 1
body.Font = Enum.Font.Gotham
body.TextSize = 15
body.TextWrapped = true
body.TextXAlignment = Enum.TextXAlignment.Left
body.TextYAlignment = Enum.TextYAlignment.Top
body.TextColor3 = Color3.fromRGB(225, 233, 236)
body.Text = "The Glass Mall now sits in a whole city.\n"
	.. "Get a car at a glowing pad, or press E by any parked car.\n"
	.. "Travel (left) jumps to any district. Collect the gold coins.\n"
	.. "Mall: 2F food court  ·  3F arcade  ·  4F cinemas"
body.Parent = card

task.delay(16, function()
	TweenService:Create(card, TweenInfo.new(1), { Position = UDim2.new(0.5, 0, 0, -260) }):Play()
end)

local pill = Instance.new("TextLabel")
pill.Size = UDim2.new(0, 330, 0, 40)
pill.Position = UDim2.new(0.5, 0, 0, 14)
pill.AnchorPoint = Vector2.new(0.5, 0)
pill.BackgroundColor3 = Color3.fromRGB(14, 20, 24)
pill.BackgroundTransparency = 0.2
pill.Font = Enum.Font.GothamMedium
pill.TextSize = 16
pill.TextColor3 = Color3.new(1, 1, 1)
pill.Text = ""
pill.Parent = gui
corner(pill, 20)

local function district(p)
	local rel = Vector3.new(p.X, 0, p.Z) - BLVD.a
	local d, t = rel:Dot(BLVD.out), rel:Dot(BLVD.dir)
	if d > BLVD.lo and d < BLVD.hi and t > BLVD.t0 and t < BLVD.t1 then
		return "Glass Boulevard"
	end
	for _, r in ipairs(DISTRICTS) do
		if p.X >= r[2] and p.X <= r[4] and p.Z >= r[3] and p.Z <= r[5] then
			return r[1]
		end
	end
	return "Glass Hills"
end

local function where()
	local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	if not root then
		return ""
	end
	local p = root.Position
	local idx = 1
	for i, f in ipairs(FLOORS) do
		if p.Y >= f.y + 1 then
			idx = i
		end
	end
	local f = FLOORS[idx]
	if inside(p.X, p.Z, FOOTPRINTS[idx]) then
		return f.name .. "  ·  " .. f.note
	end
	if idx == #FLOORS and inside(p.X, p.Z, TERRACE) then
		return "Roof terrace"
	end
	return district(p)
end

while true do
	local text = where()
	pill.Text = text
	pill.Visible = text ~= ""
	task.wait(0.25)
end
