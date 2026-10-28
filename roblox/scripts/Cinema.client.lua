-- The films. Every screen with a Film StringValue (the two 4F cinemas) plays a short animated
-- film when you are in the hall, with its own music, and the Sky Cinemas on top of the
-- towers play one too:
--   MONSOON SKIES        golden hour over the city, the monsoon rolls in, umbrellas, a rainbow
--   THE LAST METRO HOME  night, lit windows, the purple metro gliding home along the viaduct
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local player = Players.LocalPlayer
local NEAR = 75
local MUSIC = {
	["MONSOON SKIES"] = "rbxassetid://9046862941",
	["THE LAST METRO HOME"] = "rbxassetid://9046863579",
}

local screens = {}
local function track(d)
	if d:IsA("StringValue") and d.Name == "Film" and d.Parent and d.Parent:IsA("BasePart") then
		screens[d.Parent] = d.Value
	elseif d:IsA("BasePart") and d.Name == "Screen" then
		local sign = d:FindFirstChild("SignText")
		if sign and string.find(sign.Value, "NOW SHOWING") and string.find(sign.Value, "SKY CINEMA") then
			screens[d] = (#sign.Value % 2 == 0) and "MONSOON SKIES" or "THE LAST METRO HOME"
		end
	end
end
for _, d in ipairs(workspace:GetDescendants()) do
	track(d)
end
workspace.DescendantAdded:Connect(function(d)
	task.defer(track, d)
end)

-- ------------------------------------------------------------------ drawing helpers
local function frame(parent, x, y, w, h, color, z, round)
	local f = Instance.new("Frame")
	f.Position = UDim2.fromScale(x, y)
	f.Size = UDim2.fromScale(w, h)
	f.BackgroundColor3 = color
	f.BorderSizePixel = 0
	f.ZIndex = z or 1
	f.Parent = parent
	if round then
		Instance.new("UICorner", f).CornerRadius = UDim.new(round, 0)
	end
	return f
end

local function caption(parent, text, y, size, z)
	local t = Instance.new("TextLabel")
	t.Position = UDim2.fromScale(0.05, y)
	t.Size = UDim2.fromScale(0.9, size)
	t.BackgroundTransparency = 1
	t.Font = Enum.Font.GothamBlack
	t.TextScaled = true
	t.TextColor3 = Color3.new(1, 1, 1)
	t.TextStrokeTransparency = 0.5
	t.TextTransparency = 1
	t.Text = text
	t.ZIndex = z or 20
	t.Parent = parent
	return t
end

local function fadeIn(obj, prop, d)
	TweenService:Create(obj, TweenInfo.new(d or 1.2), { [prop] = 0 }):Play()
end
local function fadeOut(obj, prop, d)
	TweenService:Create(obj, TweenInfo.new(d or 1.2), { [prop] = 1 }):Play()
end

local function skyline(parent, z, base, lit)
	local x = 0
	local windows = {}
	while x < 1 do
		local w = 0.03 + math.random() * 0.05
		local h = 0.18 + math.random() * 0.45
		local b = frame(parent, x, 1 - h, w, h, base, z)
		if lit then
			for k = 1, math.random(2, 6) do
				local win = frame(b, 0.15 + math.random() * 0.6, math.random() * 0.85, 0.12, 0.04,
					Color3.fromRGB(255, 214, 140), z + 1)
				win.BackgroundTransparency = math.random() < 0.5 and 0 or 0.7
				table.insert(windows, win)
			end
		end
		x += w + 0.004
	end
	return windows
end

-- ------------------------------------------------------------------ the two films
local FILMS = {}

FILMS["MONSOON SKIES"] = function(canvas, alive)
	local sky = frame(canvas, 0, 0, 1, 1, Color3.new(1, 1, 1), 1)
	local grad = Instance.new("UIGradient", sky)
	grad.Rotation = 90
	grad.Color = ColorSequence.new(Color3.fromRGB(255, 150, 80), Color3.fromRGB(255, 220, 160))
	local sun = frame(canvas, 0.62, 0.25, 0.09, 0.42, Color3.fromRGB(255, 240, 180), 2, 1)
	Instance.new("UIAspectRatioConstraint", sun).AspectRatio = 1
	local city = Instance.new("Frame")
	city.Size = UDim2.fromScale(1, 0.75)
	city.Position = UDim2.fromScale(0, 0.6)
	city.BackgroundTransparency = 1
	city.ZIndex = 4
	city.Parent = canvas
	skyline(city, 4, Color3.fromRGB(70, 40, 60), false)
	local title = caption(canvas, "MONSOON SKIES", 0.3, 0.28)
	TweenService:Create(city, TweenInfo.new(4, Enum.EasingStyle.Quart), { Position = UDim2.fromScale(0, 0.25) }):Play()
	task.wait(2)
	fadeIn(title, "TextTransparency")
	task.wait(4)
	fadeOut(title, "TextTransparency")
	TweenService:Create(sun, TweenInfo.new(6), { Position = UDim2.fromScale(0.62, 0.9) }):Play()
	-- the clouds roll in
	local clouds = {}
	for k = 1, 9 do
		local c = frame(canvas, -0.4 - math.random() * 0.4, math.random() * 0.25, 0.2 + math.random() * 0.15, 0.25,
			Color3.fromRGB(90, 96, 110), 6, 0.5)
		c.BackgroundTransparency = 0.1
		table.insert(clouds, c)
		TweenService:Create(c, TweenInfo.new(5 + math.random() * 3), {
			Position = UDim2.fromScale(math.random() * 0.85, c.Position.Y.Scale) }):Play()
	end
	TweenService:Create(grad, TweenInfo.new(6), {}):Play()
	task.wait(3)
	grad.Color = ColorSequence.new(Color3.fromRGB(60, 70, 90), Color3.fromRGB(120, 130, 150))
	local line = caption(canvas, "Bengaluru, the first rain of July", 0.08, 0.12)
	fadeIn(line, "TextTransparency")
	-- rain and lightning
	local drops = {}
	for k = 1, 60 do
		local d = frame(canvas, math.random(), math.random(), 0.002, 0.06, Color3.fromRGB(200, 220, 240), 8)
		d.BackgroundTransparency = 0.3
		table.insert(drops, { f = d, v = 0.9 + math.random() * 0.6 })
	end
	local flash = frame(canvas, 0, 0, 1, 1, Color3.new(1, 1, 1), 15)
	flash.BackgroundTransparency = 1
	local t = 0
	while t < 11 and alive() do
		local dt = RunService.Heartbeat:Wait()
		t += dt
		for _, d in ipairs(drops) do
			local y = d.f.Position.Y.Scale + d.v * dt
			if y > 1 then
				y = -0.06
			end
			d.f.Position = UDim2.fromScale(d.f.Position.X.Scale, y)
		end
		if math.random() < 0.006 then
			flash.BackgroundTransparency = 0.2
			TweenService:Create(flash, TweenInfo.new(0.4), { BackgroundTransparency = 1 }):Play()
		end
	end
	fadeOut(line, "TextTransparency")
	-- umbrellas down the street
	local umbrellas = {}
	for k = 1, 6 do
		local u = frame(canvas, -0.15 * k, 0.62, 0.08, 0.16, ({ Color3.fromRGB(230, 60, 70), Color3.fromRGB(250, 200, 40),
			Color3.fromRGB(60, 140, 240), Color3.fromRGB(120, 210, 120) })[k % 4 + 1], 9, 1)
		frame(u, 0.48, 0.5, 0.04, 1.2, Color3.fromRGB(30, 30, 34), 9)
		table.insert(umbrellas, u)
		TweenService:Create(u, TweenInfo.new(9, Enum.EasingStyle.Linear), { Position = UDim2.fromScale(1.1 - 0.12 * k, 0.62) })
			:Play()
	end
	t = 0
	while t < 8 and alive() do
		local dt = RunService.Heartbeat:Wait()
		t += dt
		for _, d in ipairs(drops) do
			local y = d.f.Position.Y.Scale + d.v * dt * math.max(0, 1 - t / 8)
			if y > 1 then
				y = -0.06
			end
			d.f.Position = UDim2.fromScale(d.f.Position.X.Scale, y)
			d.f.BackgroundTransparency = 0.3 + 0.7 * t / 8
		end
	end
	-- the sky clears: a rainbow
	for _, c in ipairs(clouds) do
		TweenService:Create(c, TweenInfo.new(3), { BackgroundTransparency = 1 }):Play()
	end
	grad.Color = ColorSequence.new(Color3.fromRGB(120, 190, 240), Color3.fromRGB(220, 240, 250))
	local colours = { Color3.fromRGB(255, 60, 60), Color3.fromRGB(255, 160, 40), Color3.fromRGB(255, 230, 60),
		Color3.fromRGB(80, 210, 90), Color3.fromRGB(60, 140, 255), Color3.fromRGB(150, 80, 220) }
	for k, c in ipairs(colours) do
		local ring = frame(canvas, 0.5, 0.95, 0.9 - k * 0.07, 1.6 - k * 0.12, Color3.new(1, 1, 1), 3, 1)
		ring.AnchorPoint = Vector2.new(0.5, 0.5)
		ring.BackgroundTransparency = 1
		local s = Instance.new("UIStroke", ring)
		s.Color = c
		s.Thickness = 6
		s.Transparency = 1
		TweenService:Create(s, TweenInfo.new(2.5), { Transparency = 0.15 }):Play()
	end
	local fin = caption(canvas, "After the rain, the city shines.", 0.1, 0.14)
	fadeIn(fin, "TextTransparency")
	task.wait(6)
	local credits = caption(canvas, "A GLASS CITY STUDIOS PICTURE", 0.42, 0.14)
	fadeIn(credits, "TextTransparency")
	task.wait(4)
end

FILMS["THE LAST METRO HOME"] = function(canvas, alive)
	local sky = frame(canvas, 0, 0, 1, 1, Color3.new(1, 1, 1), 1)
	local grad = Instance.new("UIGradient", sky)
	grad.Rotation = 90
	grad.Color = ColorSequence.new(Color3.fromRGB(12, 14, 40), Color3.fromRGB(50, 40, 90))
	for k = 1, 40 do
		local s = frame(canvas, math.random(), math.random() * 0.5, 0.003, 0.012, Color3.new(1, 1, 1), 2)
		s.BackgroundTransparency = math.random() * 0.6
	end
	local moon = frame(canvas, 0.12, 0.1, 0.07, 0.33, Color3.fromRGB(250, 246, 220), 2, 1)
	Instance.new("UIAspectRatioConstraint", moon).AspectRatio = 1
	local city = Instance.new("Frame")
	city.Size = UDim2.fromScale(1, 0.8)
	city.Position = UDim2.fromScale(0, 0.25)
	city.BackgroundTransparency = 1
	city.ZIndex = 4
	city.Parent = canvas
	local windows = skyline(city, 4, Color3.fromRGB(26, 28, 46), true)
	local title = caption(canvas, "THE LAST METRO HOME", 0.12, 0.26)
	fadeIn(title, "TextTransparency")
	task.wait(4)
	fadeOut(title, "TextTransparency")
	-- the viaduct and its pillars
	frame(canvas, 0, 0.74, 1, 0.03, Color3.fromRGB(120, 120, 130), 6)
	for x = 0.05, 1, 0.16 do
		frame(canvas, x, 0.77, 0.015, 0.25, Color3.fromRGB(100, 100, 112), 6)
	end
	-- the train: purple, three cars, lit windows
	local train = Instance.new("Frame")
	train.Position = UDim2.fromScale(-0.7, 0.62)
	train.Size = UDim2.fromScale(0.6, 0.12)
	train.BackgroundTransparency = 1
	train.ZIndex = 7
	train.Parent = canvas
	for k = 0, 2 do
		local car = frame(train, k * 0.335, 0, 0.32, 1, Color3.fromRGB(130, 60, 170), 7, 0.25)
		for w = 0, 4 do
			frame(car, 0.08 + w * 0.18, 0.2, 0.12, 0.4, Color3.fromRGB(255, 236, 180), 8)
		end
		frame(car, 0, 0.75, 1, 0.08, Color3.fromRGB(250, 200, 40), 8)
	end
	local lines = { "Nine stops to go.", "The city is still awake.", "Almost home." }
	for i, text in ipairs(lines) do
		if not alive() then
			return
		end
		local c = caption(canvas, text, 0.86, 0.11)
		fadeIn(c, "TextTransparency", 0.8)
		train.Position = UDim2.fromScale(-0.7, 0.62)
		TweenService:Create(train, TweenInfo.new(7, Enum.EasingStyle.Sine), { Position = UDim2.fromScale(1.1, 0.62) }):Play()
		local t = 0
		while t < 7 and alive() do
			t += task.wait(0.25)
			local w = windows[math.random(math.max(1, #windows))]
			if w then
				w.BackgroundTransparency = w.BackgroundTransparency < 0.5 and 0.7 or 0
			end
		end
		fadeOut(c, "TextTransparency", 0.6)
	end
	grad.Color = ColorSequence.new(Color3.fromRGB(40, 30, 80), Color3.fromRGB(240, 140, 100))
	local fin = caption(canvas, "THE END", 0.3, 0.3)
	fadeIn(fin, "TextTransparency")
	task.wait(5)
end

-- ------------------------------------------------------------------ playing the nearest screen
local current, token = nil, 0

local function stop()
	if not current then
		return
	end
	token += 1
	local c = current
	current = nil
	if c.gui then
		c.gui:Destroy()
	end
	if c.music then
		c.music:Destroy()
	end
	local sign = c.part:FindFirstChild("Sign")
	if sign then
		sign.Enabled = true
	end
end

local function start(part, film)
	stop()
	token += 1
	local my = token
	local face = Enum.NormalId.Back
	local sign = part:FindFirstChild("Sign")
	if sign then
		face = sign.Face
		sign.Enabled = false
	end
	local gui = Instance.new("SurfaceGui")
	gui.Name = "Film"
	gui.Face = face
	gui.LightInfluence = 0
	gui.Brightness = 1.6
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = 16
	gui.Parent = part
	local canvas = Instance.new("Frame")
	canvas.Size = UDim2.fromScale(1, 1)
	canvas.BackgroundColor3 = Color3.new(0, 0, 0)
	canvas.ClipsDescendants = true
	canvas.Parent = gui
	local music = Instance.new("Sound")
	music.SoundId = MUSIC[film] or MUSIC["MONSOON SKIES"]
	music.Volume = 0.5
	music.Looped = true
	music.RollOffMode = Enum.RollOffMode.InverseTapered
	music.RollOffMinDistance = 20
	music.RollOffMaxDistance = 90
	music.Parent = part
	music:Play()
	current = { part = part, gui = gui, music = music }
	local alive = function()
		return token == my and gui.Parent ~= nil
	end
	task.spawn(function()
		while alive() do
			for _, c in ipairs(canvas:GetChildren()) do
				c:Destroy()
			end
			local ok, err = pcall(FILMS[film] or FILMS["MONSOON SKIES"], canvas, alive)
			if not ok then
				warn("Cinema: " .. tostring(err))
				task.wait(5)
			end
			task.wait(1)
		end
	end)
end

while true do
	task.wait(1)
	local cam = workspace.CurrentCamera
	if cam then
		local best, bestD = nil, NEAR
		for part, film in pairs(screens) do
			if part.Parent then
				local d = (part.Position - cam.CFrame.Position).Magnitude
				if d < bestD then
					best, bestD = part, d
				end
			else
				screens[part] = nil
			end
		end
		if best and (not current or current.part ~= best) then
			start(best, screens[best])
		elseif not best and current then
			stop()
		end
	end
end
