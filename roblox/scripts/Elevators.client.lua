-- Draws every lift car at the height the server's timetable gives (Elevators.server), slides
-- the car and landing doors, carries you with the car when you stand in it, rings the chime,
-- plays the lift music, lights the floor indicators and shows a floor panel while you ride.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local Motion = require(ReplicatedStorage:WaitForChild("ElevatorMotion"))
local remote = ReplicatedStorage:WaitForChild("ElevatorRequest")

local player = Players.LocalPlayer
local DOOR_TIME = 1.0
local NEAR = 700 -- studs; lifts further than this from the camera are left as they are
local SOUND = {
	Chime = { "rbxassetid://9114302200", 0.8 },
	Doors = { "rbxassetid://9114305596", 0.35 },
	Music = { "rbxassetid://1841647093", 0.28 },
}
local ACCENT = Color3.fromRGB(120, 225, 245)

local lifts = {}

local function root()
	local c = player.Character
	return c and c:FindFirstChild("HumanoidRootPart")
end

-- ------------------------------------------------------------------ one lift
local function readStops(model)
	local folder = model:WaitForChild("Stops")
	local stops = {}
	for i = 1, #folder:GetChildren() do
		local v = folder:FindFirstChild(tostring(i))
		if not v then
			break
		end
		local label, title = v:FindFirstChild("Label"), v:FindFirstChild("Title")
		stops[i] = { y = v.Value, label = label and label.Value or tostring(i), title = title and title.Value or "" }
	end
	return stops
end

local function addLift(model)
	if lifts[model] then
		return
	end
	local stops = readStops(model)
	if #stops < 2 then
		return
	end
	local building = model:FindFirstChild("Building")
	local speed = model:FindFirstChild("MaxSpeed")
	local e = {
		model = model,
		stops = stops,
		name = building and building.Value or "Lift",
		vmax = speed and speed.Value or 14,
		y0 = stops[1].y,
		applied = stops[1].y,
		doorF = -1,
		landing = {},
		landingFloor = nil,
		pending = {},
		anchor = nil,
		active = false,
	}
	local function read()
		e.from = model:GetAttribute("From") or e.y0
		e.to = model:GetAttribute("To") or e.y0
		e.start = model:GetAttribute("Start") or 0
		e.plan = Motion.plan(e.from, e.to, e.vmax)
		e.floor = model:GetAttribute("Floor") or 1
		e.target = model:GetAttribute("Target") or e.floor
		e.doorOpen = model:GetAttribute("DoorOpen") or false
		e.doorT = model:GetAttribute("DoorT") or 0
	end
	read()
	model.AttributeChanged:Connect(function(name)
		read()
		if not e.car or not e.active then
			return
		end
		if name == "Arrivals" and e.sounds then
			e.sounds.Chime:Play()
			e.pending[e.floor] = nil
		elseif name == "DoorOpen" and e.sounds then
			e.sounds.Doors:Play()
		end
	end)
	lifts[model] = e
end

local function attachCar(e, car)
	e.car = car
	e.carFloor = nil
	e.sounds = nil
	e.doorRel = {}
	if not car then
		return
	end
	-- the server never moves the car, so whenever it streams in it is at the first stop
	e.base = car:GetPivot()
	e.applied = e.y0
	e.doorF = -1
	e.carFloor = car:FindFirstChild("Floor")
	e.anchor = e.carFloor and e.carFloor.Position
	local slide = car:FindFirstChild("Slide")
	for side, sign in pairs({ DoorL = -1, DoorR = 1 }) do
		local door = car:FindFirstChild(side)
		if door then
			e.doorRel[door] = { rel = e.base:ToObjectSpace(door.CFrame), shift = sign * (slide and slide.Value or 2) }
		end
	end
	if e.carFloor then
		e.sounds = {}
		for name, s in pairs(SOUND) do
			local sound = Instance.new("Sound")
			sound.Name = name
			sound.SoundId = s[1]
			sound.Volume = s[2]
			sound.RollOffMode = Enum.RollOffMode.InverseTapered
			sound.RollOffMinDistance = name == "Music" and 3 or 8
			sound.RollOffMaxDistance = name == "Music" and 16 or 60
			sound.Looped = name == "Music"
			sound.Parent = e.carFloor
			e.sounds[name] = sound
		end
	end
end

local function insideCar(e, pos)
	local f = e.carFloor
	if not f or not f.Parent then
		return false
	end
	local rel = f.CFrame:PointToObjectSpace(pos)
	local s = f.Size
	return math.abs(rel.X) < s.X / 2 + 0.2 and math.abs(rel.Z) < s.Z / 2 + 0.2 and rel.Y > -1 and rel.Y < 11
end

local function landingDoors(e, i)
	local d = e.landing[i]
	if d and d.l.Parent and d.r.Parent then
		return d
	end
	local landings = e.model:FindFirstChild("Landings")
	local m = landings and landings:FindFirstChild("Door" .. i)
	local l, r, slide = m and m:FindFirstChild("L"), m and m:FindFirstChild("R"), m and m:FindFirstChild("Slide")
	if not (l and r and slide) then
		e.landing[i] = nil
		return nil
	end
	d = { l = l, r = r, lClosed = l.CFrame, rClosed = r.CFrame, slide = slide.Value, f = 0 }
	e.landing[i] = d
	return d
end

local function setLanding(d, f)
	if d and math.abs(d.f - f) > 1e-4 then
		d.f = f
		d.l.CFrame = d.lClosed * CFrame.new(-d.slide * f, 0, 0)
		d.r.CFrame = d.rClosed * CFrame.new(d.slide * f, 0, 0)
	end
end

local function step(e, t)
	local car = e.model:FindFirstChild("Car")
	if car ~= e.car then
		attachCar(e, car)
	end
	local y = Motion.height(e.plan, t - e.start)
	local s = math.clamp((t - e.doorT) / DOOR_TIME, 0, 1)
	local f = e.doorOpen and s or 1 - s
	f = f * f * (3 - 2 * f)

	if e.car and e.base and (math.abs(y - e.applied) > 1e-4 or math.abs(f - e.doorF) > 1e-4) then
		local delta = y - e.applied
		local cf = e.base + Vector3.new(0, y - e.y0, 0)
		if delta ~= 0 then
			local r = root()
			if r and insideCar(e, r.Position) then
				r.CFrame += Vector3.new(0, delta, 0)
			end
			e.car:PivotTo(cf)
			e.applied = y
		end
		for door, d in pairs(e.doorRel) do
			door.CFrame = cf * d.rel * CFrame.new(d.shift * f, 0, 0)
		end
		e.doorF = f
	end

	if e.landingFloor ~= e.floor then
		if e.landingFloor then
			setLanding(landingDoors(e, e.landingFloor), 0)
		end
		e.landingFloor = e.floor
	end
	setLanding(landingDoors(e, e.floor), f)
end

-- ------------------------------------------------------------------ indicators
local function indicator(part)
	local gui = part:FindFirstChild("Indicator")
	if gui then
		return gui:FindFirstChild("Text", true)
	end
	gui = Instance.new("SurfaceGui")
	gui.Name = "Indicator"
	gui.Face = Enum.NormalId.Back
	gui.LightInfluence = 0
	gui.Brightness = 2
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = 60
	local bg = Instance.new("Frame")
	bg.Size = UDim2.fromScale(1, 1)
	bg.BackgroundColor3 = Color3.fromRGB(8, 10, 14)
	bg.BorderSizePixel = 0
	bg.Parent = gui
	local text = Instance.new("TextLabel")
	text.Name = "Text"
	text.Size = UDim2.fromScale(0.92, 0.8)
	text.Position = UDim2.fromScale(0.04, 0.1)
	text.BackgroundTransparency = 1
	text.Font = Enum.Font.GothamBold
	text.TextScaled = true
	text.TextColor3 = Color3.fromRGB(255, 170, 60)
	text.Parent = bg
	gui.Parent = part
	return text
end

local function nearestStop(e, y)
	local best, bestD = 1, math.huge
	for i, s in ipairs(e.stops) do
		local d = math.abs(s.y - y)
		if d < bestD then
			best, bestD = i, d
		end
	end
	return best
end

local function readout(e, t)
	local y, v = Motion.height(e.plan, t - e.start)
	local i = nearestStop(e, y)
	local arrow = v > 0.05 and "▲ " or v < -0.05 and "▼ " or ""
	return arrow .. e.stops[i].label, i, v
end

local function updateDisplays(e, t)
	local text = readout(e, t)
	local landings = e.model:FindFirstChild("Landings")
	if landings then
		for i = 1, #e.stops do
			local part = landings:FindFirstChild("Display" .. i)
			if part then
				indicator(part).Text = text
			end
		end
	end
	local carDisplay = e.car and e.car:FindFirstChild("CarDisplay")
	if carDisplay then
		indicator(carDisplay).Text = text
	end
end

-- ------------------------------------------------------------------ the panel you see in a car
local gui = Instance.new("ScreenGui")
gui.Name = "ElevatorPanel"
gui.ResetOnSpawn = false
gui.Parent = player:WaitForChild("PlayerGui")

local panel = Instance.new("Frame")
panel.AnchorPoint = Vector2.new(1, 0.5)
panel.Size = UDim2.new(0, 250, 0, 120)
panel.Position = UDim2.new(1, 300, 0.5, 0)
panel.BackgroundColor3 = Color3.fromRGB(14, 20, 24)
panel.BackgroundTransparency = 0.08
panel.Parent = gui
Instance.new("UICorner", panel).CornerRadius = UDim.new(0, 14)
local stroke = Instance.new("UIStroke", panel)
stroke.Color = ACCENT
stroke.Transparency = 0.6
stroke.Thickness = 1.5

local header = Instance.new("TextLabel")
header.Size = UDim2.new(1, -24, 0, 20)
header.Position = UDim2.new(0, 12, 0, 10)
header.BackgroundTransparency = 1
header.Font = Enum.Font.GothamMedium
header.TextSize = 13
header.TextXAlignment = Enum.TextXAlignment.Left
header.TextColor3 = Color3.fromRGB(170, 186, 192)
header.Parent = panel

local big = Instance.new("TextLabel")
big.Size = UDim2.new(1, -24, 0, 46)
big.Position = UDim2.new(0, 12, 0, 30)
big.BackgroundTransparency = 1
big.Font = Enum.Font.GothamBlack
big.TextSize = 40
big.TextXAlignment = Enum.TextXAlignment.Left
big.TextColor3 = Color3.fromRGB(255, 170, 60)
big.Parent = panel

local sub = Instance.new("TextLabel")
sub.Size = UDim2.new(1, -24, 0, 18)
sub.Position = UDim2.new(0, 12, 0, 76)
sub.BackgroundTransparency = 1
sub.Font = Enum.Font.Gotham
sub.TextSize = 14
sub.TextXAlignment = Enum.TextXAlignment.Left
sub.TextColor3 = Color3.fromRGB(225, 233, 236)
sub.Parent = panel

local list = Instance.new("Frame")
list.Position = UDim2.new(0, 10, 0, 102)
list.Size = UDim2.new(1, -20, 0, 0)
list.BackgroundTransparency = 1
list.Parent = panel
local layout = Instance.new("UIListLayout", list)
layout.Padding = UDim.new(0, 6)
layout.SortOrder = Enum.SortOrder.LayoutOrder

local riding, buttons, extras, shown = nil, {}, {}, false

local function button(parent, text, order, onClick)
	local b = Instance.new("TextButton")
	b.LayoutOrder = order
	b.Size = UDim2.new(1, 0, 0, 38)
	b.BackgroundColor3 = Color3.fromRGB(32, 42, 48)
	b.AutoButtonColor = true
	b.Font = Enum.Font.GothamMedium
	b.TextSize = 15
	b.TextXAlignment = Enum.TextXAlignment.Left
	b.TextColor3 = Color3.new(1, 1, 1)
	b.Text = text
	b.Parent = parent
	Instance.new("UICorner", b).CornerRadius = UDim.new(0, 10)
	Instance.new("UIPadding", b).PaddingLeft = UDim.new(0, 12)
	b.Activated:Connect(onClick)
	return b
end

local function build(e)
	for _, b in pairs(buttons) do
		b:Destroy()
	end
	for _, b in ipairs(extras) do
		b:Destroy()
	end
	buttons, extras = {}, {}
	header.Text = string.upper(e.name)
	local n = #e.stops
	for i = n, 1, -1 do
		local s = e.stops[i]
		local b = button(list, string.format("%s   %s", s.label, s.title), n - i, function()
			e.pending[i] = true
			remote:FireServer(e.model, "go", i)
		end)
		buttons[i] = b
	end
	local row = Instance.new("Frame")
	row.LayoutOrder = n + 1
	row.Size = UDim2.new(1, 0, 0, 34)
	row.BackgroundTransparency = 1
	row.Parent = list
	table.insert(extras, row)
	for k, spec in ipairs({ { "◀ ▶  Open", "open" }, { "▶ ◀  Close", "close" } }) do
		local b = Instance.new("TextButton")
		b.Size = UDim2.new(0.5, -3, 1, 0)
		b.Position = UDim2.new((k - 1) * 0.5, (k - 1) * 3, 0, 0)
		b.BackgroundColor3 = Color3.fromRGB(24, 32, 38)
		b.Font = Enum.Font.GothamMedium
		b.TextSize = 13
		b.TextColor3 = Color3.fromRGB(200, 214, 220)
		b.Text = spec[1]
		b.Parent = row
		Instance.new("UICorner", b).CornerRadius = UDim.new(0, 8)
		b.Activated:Connect(function()
			remote:FireServer(e.model, spec[2])
		end)
	end
	local h = 102 + n * 44 + 34 + 14
	list.Size = UDim2.new(1, -20, 0, n * 44 + 34)
	panel.Size = UDim2.new(0, 250, 0, h)
end

local function show(on)
	if on == shown then
		return
	end
	shown = on
	TweenService:Create(panel, TweenInfo.new(0.35, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), {
		Position = on and UDim2.new(1, -18, 0.5, 0) or UDim2.new(1, 300, 0.5, 0),
	}):Play()
end

local function refreshPanel(e, t)
	local text, i, v = readout(e, t)
	big.Text = text
	local moving = math.abs(v) > 0.05
	sub.Text = moving and ("to " .. e.stops[e.target].title) or e.stops[i].title
	for k, b in pairs(buttons) do
		local here = k == i and not moving
		local wanted = e.pending[k] or (moving and k == e.target)
		b.BackgroundColor3 = here and Color3.fromRGB(40, 110, 130)
			or wanted and Color3.fromRGB(150, 96, 30)
			or Color3.fromRGB(32, 42, 48)
	end
end

-- ------------------------------------------------------------------ loops
for _, d in ipairs(workspace:GetDescendants()) do
	if d:IsA("Model") and d.Name == "Elevator" then
		task.spawn(addLift, d)
	end
end
workspace.DescendantAdded:Connect(function(d)
	if d:IsA("Model") and d.Name == "Elevator" then
		task.spawn(addLift, d)
	end
end)

RunService.PreSimulation:Connect(function()
	local t = workspace:GetServerTimeNow()
	for _, e in pairs(lifts) do
		if e.active or e == riding then
			step(e, t)
		end
	end
end)

task.spawn(function()
	while true do
		local t = workspace:GetServerTimeNow()
		local cam = workspace.CurrentCamera
		local r = root()
		local inCar = nil
		for _, e in pairs(lifts) do
			local car = e.model:FindFirstChild("Car")
			if car ~= e.car then
				attachCar(e, car)
			end
			local anchor = e.anchor
			e.active = anchor ~= nil
				and cam ~= nil
				and (Vector3.new(anchor.X, 0, anchor.Z) - Vector3.new(cam.CFrame.X, 0, cam.CFrame.Z)).Magnitude < NEAR
			if e.active then
				updateDisplays(e, t)
				if r and insideCar(e, r.Position) then
					inCar = e
				end
				local music = e.sounds and e.sounds.Music
				if music then
					local close = r and e.carFloor and (r.Position - e.carFloor.Position).Magnitude < 30
					if close and not music.IsPlaying then
						music:Play()
					elseif not close and music.IsPlaying then
						music:Stop()
					end
				end
			end
		end
		if inCar ~= riding then
			riding = inCar
			if riding then
				build(riding)
			end
			show(riding ~= nil)
		end
		if riding then
			refreshPanel(riding, t)
		end
		task.wait(0.1)
	end
end)
