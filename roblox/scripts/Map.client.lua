-- The city map: the Map button (or M) opens Glass City from above, drawn from CityData.MAP:
-- the bay, the ring highway and its streets, the districts, every building and house, and
-- you. Click a gold pin to travel there.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

local CityData = require(ReplicatedStorage:WaitForChild("CityData"))
local travel = ReplicatedStorage:WaitForChild("Travel")
local player = Players.LocalPlayer
local MAP = CityData.MAP
local PLACES = __PLACES__ -- name -> position in studs
local ACCENT = Color3.fromRGB(120, 225, 245)
local TINT = {
	Downtown = Color3.fromRGB(84, 92, 118), Midtown = Color3.fromRGB(96, 100, 110), Uptown = Color3.fromRGB(110, 98, 120),
	Suburbs = Color3.fromRGB(92, 120, 80), ["Central Park"] = Color3.fromRGB(70, 130, 70),
	["Stunt Park"] = Color3.fromRGB(90, 84, 80), ["VAYU Hotel"] = Color3.fromRGB(120, 104, 90),
	["Glass Mall"] = Color3.fromRGB(80, 120, 140), ["Glass Mall car park"] = Color3.fromRGB(70, 74, 80),
}

local gui = Instance.new("ScreenGui")
gui.Name = "CityMap"
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = true
gui.DisplayOrder = 10
gui.Parent = player:WaitForChild("PlayerGui")

local function corner(p, r)
	local c = Instance.new("UICorner")
	c.CornerRadius = UDim.new(0, r)
	c.Parent = p
end

-- the button lives with the other buttons, under the top bar; the map itself covers the screen
local dock = Instance.new("ScreenGui")
dock.Name = "MapButton"
dock.ResetOnSpawn = false
dock.Parent = player:WaitForChild("PlayerGui")
local button = Instance.new("TextButton")
button.AnchorPoint = Vector2.new(0, 0.5)
button.Size = UDim2.new(0, 120, 0, 42)
button.Position = UDim2.new(0, 16, 0.5, 50)
button.BackgroundColor3 = Color3.fromRGB(14, 20, 24)
button.BackgroundTransparency = 0.1
button.Font = Enum.Font.GothamBold
button.TextSize = 17
button.TextColor3 = ACCENT
button.Text = "Map"
button.Parent = dock
corner(button, 21)

local shade = Instance.new("Frame")
shade.Size = UDim2.fromScale(1, 1)
shade.BackgroundColor3 = Color3.fromRGB(6, 10, 14)
shade.BackgroundTransparency = 0.15
shade.Visible = false
shade.Parent = gui

local bx0, bz0, bx1, bz1 = MAP.bounds[1], MAP.bounds[2], MAP.bounds[3], MAP.bounds[4]
local W, H = bx1 - bx0, bz1 - bz0

local holder = Instance.new("Frame")
holder.AnchorPoint = Vector2.new(0.5, 0.5)
holder.Position = UDim2.fromScale(0.5, 0.52)
holder.Size = UDim2.fromScale(0.9, 0.84)
holder.BackgroundTransparency = 1
holder.Parent = shade
local canvas = Instance.new("Frame")
canvas.AnchorPoint = Vector2.new(0.5, 0.5)
canvas.Position = UDim2.fromScale(0.5, 0.5)
canvas.Size = UDim2.fromScale(1, 1)
canvas.BackgroundColor3 = Color3.fromRGB(86, 120, 70)
canvas.ClipsDescendants = true
canvas.Parent = holder
corner(canvas, 12)
local ratio = Instance.new("UIAspectRatioConstraint", canvas)
ratio.AspectRatio = W / H

local title = Instance.new("TextLabel")
title.Position = UDim2.new(0, 170, 0, 16)
title.Size = UDim2.new(1, -250, 0, 30)
title.BackgroundTransparency = 1
title.Font = Enum.Font.GothamBlack
title.TextSize = 20
title.TextTruncate = Enum.TextTruncate.AtEnd
title.TextXAlignment = Enum.TextXAlignment.Left
title.TextColor3 = ACCENT
title.Text = "GLASS CITY   ·   click a gold pin to go there   ·   M to close"
title.Parent = shade

local close = Instance.new("TextButton")
close.AnchorPoint = Vector2.new(1, 0)
close.Position = UDim2.new(1, -20, 0, 64)
close.Size = UDim2.fromOffset(40, 40)
close.BackgroundColor3 = Color3.fromRGB(32, 42, 48)
close.Font = Enum.Font.GothamBold
close.TextSize = 20
close.TextColor3 = Color3.new(1, 1, 1)
close.Text = "✕"
close.Parent = shade
corner(close, 20)

local function rect(r, color, z, transparency)
	local f = Instance.new("Frame")
	f.Position = UDim2.fromScale((r[1] - bx0) / W, (r[2] - bz0) / H)
	f.Size = UDim2.fromScale((r[3] - r[1]) / W, (r[4] - r[2]) / H)
	f.BackgroundColor3 = color
	f.BackgroundTransparency = transparency or 0
	f.BorderSizePixel = 0
	f.ZIndex = z
	f.Parent = canvas
	return f
end

local function text(str, x, z, size, color, zi)
	local t = Instance.new("TextLabel")
	t.AnchorPoint = Vector2.new(0.5, 0.5)
	t.Position = UDim2.fromScale((x - bx0) / W, (z - bz0) / H)
	t.Size = UDim2.fromOffset(200, 20)
	t.BackgroundTransparency = 1
	t.Font = Enum.Font.GothamBold
	t.TextSize = size
	t.TextColor3 = color
	t.TextStrokeTransparency = 0.4
	t.Text = str
	t.ZIndex = zi or 8
	t.Parent = canvas
	return t
end

local drawn = false
local arrow
local function draw()
	if drawn then
		return
	end
	drawn = true
	for _, r in ipairs(MAP.water) do
		rect(r, Color3.fromRGB(40, 110, 150), 2)
	end
	rect(MAP.sand, Color3.fromRGB(226, 206, 160), 2)
	for _, d in ipairs(MAP.districts) do
		rect(d[2], TINT[d[1]] or Color3.fromRGB(96, 104, 110), 3, 0.15)
	end
	for _, r in ipairs(MAP.parks) do
		rect(r, Color3.fromRGB(80, 150, 76), 3)
	end
	rect(MAP.water[2], Color3.fromRGB(46, 130, 170), 4)
	for _, r in ipairs(MAP.roads) do
		rect(r, Color3.fromRGB(44, 46, 52), 5)
	end
	local b = MAP.blvd
	local blvd = Instance.new("Frame")
	blvd.AnchorPoint = Vector2.new(0.5, 0.5)
	blvd.Position = UDim2.fromScale((b.x - bx0) / W, (b.z - bz0) / H)
	blvd.Size = UDim2.fromScale(b.length / W, b.width / H)
	blvd.Rotation = b.angle
	blvd.BackgroundColor3 = Color3.fromRGB(44, 46, 52)
	blvd.BorderSizePixel = 0
	blvd.ZIndex = 5
	blvd.Parent = canvas
	for _, r in ipairs(MAP.houses) do
		rect(r, Color3.fromRGB(226, 214, 196), 6)
	end
	for _, bd in ipairs(MAP.buildings) do
		local f = rect(bd[2], Color3.fromRGB(214, 222, 228), 6)
		local s = Instance.new("UIStroke", f)
		s.Color = Color3.fromRGB(40, 50, 60)
		s.Thickness = 1
	end
	local mall = rect(MAP.mall, Color3.fromRGB(150, 220, 240), 6)
	Instance.new("UIStroke", mall).Color = ACCENT
	for _, d in ipairs(MAP.districts) do
		local r = d[2]
		text(string.upper(d[1]), (r[1] + r[3]) / 2, (r[2] + r[4]) / 2, 13, Color3.fromRGB(240, 244, 246), 7)
	end
	text("GLASS BAY", MAP.water[1][1] + 300, (MAP.water[1][2] + MAP.water[1][4]) / 2, 16, Color3.fromRGB(200, 230, 250), 7)
	for name, pos in pairs(PLACES) do
		local pin = Instance.new("TextButton")
		pin.AnchorPoint = Vector2.new(0.5, 1)
		pin.Position = UDim2.fromScale((pos.X - bx0) / W, (pos.Z - bz0) / H)
		pin.Size = UDim2.fromOffset(18, 18)
		pin.BackgroundColor3 = Color3.fromRGB(255, 200, 60)
		pin.Text = ""
		pin.ZIndex = 9
		pin.Parent = canvas
		corner(pin, 9)
		local st = Instance.new("UIStroke", pin)
		st.Color = Color3.fromRGB(40, 30, 10)
		st.Thickness = 2
		local tag = Instance.new("TextLabel")
		tag.AnchorPoint = Vector2.new(0.5, 1)
		tag.Position = UDim2.new(0.5, 0, 0, -2)
		tag.Size = UDim2.fromOffset(160, 16)
		tag.BackgroundTransparency = 1
		tag.Font = Enum.Font.GothamBold
		tag.TextSize = 12
		tag.TextColor3 = Color3.fromRGB(255, 236, 170)
		tag.TextStrokeTransparency = 0.3
		tag.Text = name
		tag.ZIndex = 9
		tag.Parent = pin
		pin.Activated:Connect(function()
			shade.Visible = false
			travel:FireServer(name)
		end)
	end
	arrow = Instance.new("TextLabel")
	arrow.AnchorPoint = Vector2.new(0.5, 0.5)
	arrow.Size = UDim2.fromOffset(30, 30)
	arrow.BackgroundTransparency = 1
	arrow.Font = Enum.Font.GothamBlack
	arrow.TextSize = 28
	arrow.TextColor3 = Color3.fromRGB(255, 70, 90)
	arrow.TextStrokeTransparency = 0
	arrow.Text = "▲"
	arrow.ZIndex = 10
	arrow.Parent = canvas
end

local function toggle()
	shade.Visible = not shade.Visible
	if shade.Visible then
		draw()
	end
end
button.Activated:Connect(toggle)
close.Activated:Connect(toggle)
UserInputService.InputBegan:Connect(function(input, processed)
	if not processed and input.KeyCode == Enum.KeyCode.M then
		toggle()
	end
end)

RunService.RenderStepped:Connect(function()
	if not shade.Visible or not arrow then
		return
	end
	local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	local cam = workspace.CurrentCamera
	if root then
		local p = root.Position
		arrow.Position = UDim2.fromScale(math.clamp((p.X - bx0) / W, 0, 1), math.clamp((p.Z - bz0) / H, 0, 1))
	end
	if cam then
		local look = cam.CFrame.LookVector
		arrow.Rotation = math.deg(math.atan2(look.X, -look.Z))
	end
end)
