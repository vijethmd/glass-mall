-- Effects on each player's screen:
--   * parts with an FX StringValue: the plaza fountain, steam over the food stalls and the spa,
--     smoke from chimneys and barbecues, the pizza oven's fire, the sky club's haze and the
--     fireflies that come out in Central Park at night
--   * fireworks over Glass Bay every night
--   * rain when the server says it is raining (not indoors), with the odd thunderclap
--   * room lights far from you are switched off on your screen, so a city of a thousand
--     lamps stays smooth
local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Debris = game:GetService("Debris")

local CityData = require(ReplicatedStorage:WaitForChild("CityData"))
local player = Players.LocalPlayer
local P = "rbxasset://textures/particles/"

local function seq(a, b)
	return NumberSequence.new(a, b)
end
local function emitter(parent, props)
	local e = Instance.new("ParticleEmitter")
	for k, v in pairs(props) do
		e[k] = v
	end
	e.Parent = parent
	return e
end

local night = false
local fireflies = {}

local KINDS = {
	steam = function(part)
		emitter(part, { Texture = P .. "smoke_main.dds", Color = ColorSequence.new(Color3.fromRGB(250, 250, 250)),
			Size = seq(0.6, 2.2), Transparency = seq(0.55, 1), Lifetime = NumberRange.new(1.8, 2.8), Rate = 5,
			Speed = NumberRange.new(1, 2.5), SpreadAngle = Vector2.new(15, 15), Acceleration = Vector3.new(0, 1.5, 0),
			LightInfluence = 0.6 })
	end,
	smoke = function(part)
		emitter(part, { Texture = P .. "smoke_main.dds", Color = ColorSequence.new(Color3.fromRGB(200, 200, 204)),
			Size = seq(0.8, 3), Transparency = seq(0.5, 1), Lifetime = NumberRange.new(2.5, 4), Rate = 4,
			Speed = NumberRange.new(2, 3), SpreadAngle = Vector2.new(12, 12), Acceleration = Vector3.new(0.6, 1, 0) })
	end,
	chimney = function(part)
		emitter(part, { Texture = P .. "smoke_main.dds", Color = ColorSequence.new(Color3.fromRGB(220, 220, 224)),
			Size = seq(1.5, 6), Transparency = seq(0.6, 1), Lifetime = NumberRange.new(4, 6), Rate = 2,
			Speed = NumberRange.new(3, 4), SpreadAngle = Vector2.new(8, 8), Acceleration = Vector3.new(1.2, 0.5, 0),
			EmissionDirection = Enum.NormalId.Top })
	end,
	fire = function(part)
		local f = Instance.new("Fire")
		f.Size = 2
		f.Heat = 4
		f.Color = Color3.fromRGB(255, 140, 40)
		f.SecondaryColor = Color3.fromRGB(255, 220, 90)
		f.Parent = part
		local l = Instance.new("PointLight")
		l.Color = Color3.fromRGB(255, 150, 60)
		l.Range = 10
		l.Brightness = 1.2
		l.Parent = part
	end,
	fountain = function(part)
		emitter(part, { Texture = P .. "sparkles_main.dds", Color = ColorSequence.new(Color3.fromRGB(200, 235, 255)),
			Size = seq(0.5, 0.9), Transparency = seq(0.2, 1), Lifetime = NumberRange.new(1.3, 1.7), Rate = 160,
			Speed = NumberRange.new(26, 32), SpreadAngle = Vector2.new(9, 9), Acceleration = Vector3.new(0, -42, 0),
			EmissionDirection = Enum.NormalId.Top, LightEmission = 0.3 })
		emitter(part, { Texture = P .. "smoke_main.dds", Color = ColorSequence.new(Color3.fromRGB(230, 245, 255)),
			Size = seq(2, 5), Transparency = seq(0.75, 1), Lifetime = NumberRange.new(1.5, 2.5), Rate = 12,
			Speed = NumberRange.new(4, 8), SpreadAngle = Vector2.new(60, 60), EmissionDirection = Enum.NormalId.Top })
	end,
	haze = function(part)
		emitter(part, { Texture = P .. "smoke_main.dds",
			Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 60, 160)),
				ColorSequenceKeypoint.new(0.5, Color3.fromRGB(60, 200, 255)), ColorSequenceKeypoint.new(1, Color3.fromRGB(140, 80, 255)) }),
			Size = seq(6, 12), Transparency = seq(0.85, 1), Lifetime = NumberRange.new(5, 8), Rate = 3,
			Speed = NumberRange.new(0.5, 1.5), SpreadAngle = Vector2.new(180, 180), LightEmission = 1 })
	end,
	fireflies = function(part)
		local e = emitter(part, { Texture = P .. "sparkles_main.dds", Color = ColorSequence.new(Color3.fromRGB(220, 255, 120)),
			Size = seq(0.35, 0.2), Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1),
				NumberSequenceKeypoint.new(0.3, 0), NumberSequenceKeypoint.new(0.7, 0.2), NumberSequenceKeypoint.new(1, 1) }),
			Lifetime = NumberRange.new(4, 7), Rate = 40, Speed = NumberRange.new(0.3, 1.2), SpreadAngle = Vector2.new(180, 180),
			LightEmission = 1, LightInfluence = 0, Shape = Enum.ParticleEmitterShape.Box,
			ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume, RotSpeed = NumberRange.new(-60, 60) })
		e.Enabled = night
		table.insert(fireflies, e)
	end,
}

local function hook(part, kind)
	if part:FindFirstChild("FXDone") or not KINDS[kind] then
		return
	end
	local mark = Instance.new("BoolValue")
	mark.Name = "FXDone"
	mark.Parent = part
	KINDS[kind](part)
end
for _, d in ipairs(workspace:GetDescendants()) do
	if d:IsA("StringValue") and d.Name == "FX" and d.Parent and d.Parent:IsA("BasePart") then
		hook(d.Parent, d.Value)
	end
end
workspace.DescendantAdded:Connect(function(d)
	if d:IsA("StringValue") and d.Name == "FX" then
		task.defer(function()
			if d.Parent and d.Parent:IsA("BasePart") then
				hook(d.Parent, d.Value)
			end
		end)
	end
end)

-- ------------------------------------------------------------------ fireworks over the bay
local bay = CityData.MAP.water[1]
local PALETTE = { Color3.fromRGB(255, 70, 90), Color3.fromRGB(255, 200, 60), Color3.fromRGB(80, 220, 255),
	Color3.fromRGB(150, 90, 255), Color3.fromRGB(90, 255, 140), Color3.fromRGB(255, 255, 255) }
local BOOM = "rbxassetid://9114447096"

local function firework()
	local x = bay[1] + 80 + math.random() * 420
	local z = bay[2] + (bay[4] - bay[2]) * (0.25 + math.random() * 0.5)
	local top = 140 + math.random() * 120
	local shell = Instance.new("Part")
	shell.Anchored = true
	shell.CanCollide = false
	shell.CanQuery = false
	shell.CanTouch = false
	shell.Size = Vector3.new(0.6, 0.6, 0.6)
	shell.Material = Enum.Material.Neon
	shell.Color = Color3.fromRGB(255, 220, 160)
	shell.Position = Vector3.new(x, 2, z)
	shell.Parent = workspace.CurrentCamera
	local a0, a1 = Instance.new("Attachment", shell), Instance.new("Attachment", shell)
	a0.Position, a1.Position = Vector3.new(0, 0.3, 0), Vector3.new(0, -0.3, 0)
	local trail = Instance.new("Trail")
	trail.Attachment0, trail.Attachment1 = a0, a1
	trail.Lifetime = 0.6
	trail.Color = ColorSequence.new(Color3.fromRGB(255, 220, 160))
	trail.LightEmission = 1
	trail.Transparency = NumberSequence.new(0.2, 1)
	trail.Parent = shell
	local rise = TweenService:Create(shell, TweenInfo.new(1.6, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
		{ Position = Vector3.new(x + math.random(-10, 10), top, z) })
	rise:Play()
	rise.Completed:Wait()
	local colour = PALETTE[math.random(#PALETTE)]
	local burst = emitter(shell, { Texture = P .. "sparkles_main.dds", Color = ColorSequence.new(colour),
		Size = seq(1.6, 0.4), Transparency = seq(0, 1), Lifetime = NumberRange.new(1.6, 2.6), Rate = 0,
		Speed = NumberRange.new(40, 60), SpreadAngle = Vector2.new(180, 180), Drag = 1.8,
		Acceleration = Vector3.new(0, -12, 0), LightEmission = 1, LightInfluence = 0 })
	burst:Emit(140)
	local glow = Instance.new("PointLight")
	glow.Color = colour
	glow.Range = 60
	glow.Brightness = 6
	glow.Parent = shell
	TweenService:Create(glow, TweenInfo.new(1.4), { Brightness = 0 }):Play()
	shell.Transparency = 1
	trail.Enabled = false
	local boom = Instance.new("Sound")
	boom.SoundId = BOOM
	boom.Volume = 0.7
	boom.RollOffMaxDistance = 1400
	boom.RollOffMinDistance = 120
	boom.Parent = shell
	boom:Play()
	Debris:AddItem(shell, 4)
end

task.spawn(function()
	while true do
		local t = Lighting.ClockTime
		local show = t > 19.3 or t < 4.5
		local cam = workspace.CurrentCamera
		if show and cam and (cam.CFrame.Position - Vector3.new(bay[1], 0, (bay[2] + bay[4]) / 2)).Magnitude < 3500 then
			for _ = 1, math.random(1, 3) do
				task.spawn(firework)
				task.wait(0.25)
			end
			task.wait(1.5 + math.random() * 2.5)
		else
			task.wait(3)
		end
	end
end)

-- ------------------------------------------------------------------ rain
local cloud = Instance.new("Part")
cloud.Name = "RainCloud"
cloud.Anchored = true
cloud.CanCollide = false
cloud.CanQuery = false
cloud.CanTouch = false
cloud.Transparency = 1
cloud.Size = Vector3.new(180, 1, 180)
cloud.Parent = workspace.CurrentCamera
local rain = emitter(cloud, { Texture = P .. "sparkles_main.dds", Color = ColorSequence.new(Color3.fromRGB(190, 210, 230)),
	Size = seq(0.14, 0.14), Squash = NumberSequence.new(2.6), Transparency = seq(0.35, 0.5),
	Lifetime = NumberRange.new(0.8, 1), Rate = 0, Speed = NumberRange.new(90, 110), EmissionDirection = Enum.NormalId.Bottom,
	Orientation = Enum.ParticleOrientation.VelocityParallel, LightInfluence = 1, Shape = Enum.ParticleEmitterShape.Box })
local thunder = Instance.new("Sound")
thunder.SoundId = "rbxassetid://9120018172"
thunder.Volume = 0.6
thunder.Parent = workspace.CurrentCamera
local flash = Instance.new("ColorCorrectionEffect")
flash.Name = "Lightning"
flash.Brightness = 0
flash.Parent = Lighting

local rayParams = RaycastParams.new()
rayParams.FilterType = Enum.RaycastFilterType.Exclude

-- ------------------------------------------------------------------ lights you can't see from here
local lights = {}
local function trackLight(d)
	if (d:IsA("PointLight") or d:IsA("SpotLight") or d:IsA("SurfaceLight")) and d.Name == "Light" then
		lights[d] = d.Enabled
	end
end
for _, d in ipairs(workspace:GetDescendants()) do
	trackLight(d)
end
workspace.DescendantAdded:Connect(trackLight)

local acc = 0
RunService.Heartbeat:Connect(function(dt)
	local cam = workspace.CurrentCamera
	if not cam then
		return
	end
	local p = cam.CFrame.Position
	cloud.CFrame = CFrame.new(p.X, p.Y + 55, p.Z)
	acc += dt
	if acc < 0.5 then
		return
	end
	acc = 0
	local t = Lighting.ClockTime
	local isNight = t < 6.2 or t > 18.4
	if isNight ~= night then
		night = isNight
		for i = #fireflies, 1, -1 do
			if fireflies[i].Parent then
				fireflies[i].Enabled = night
			else
				table.remove(fireflies, i)
			end
		end
	end
	local raining = workspace:GetAttribute("Weather") == "Rain"
	rayParams.FilterDescendantsInstances = { player.Character, cam }
	local covered = workspace:Raycast(p, Vector3.new(0, 80, 0), rayParams) ~= nil
	rain.Rate = (raining and not covered) and 900 or 0
	if raining and math.random() < 0.03 then
		thunder:Play()
		flash.Brightness = 0.35
		TweenService:Create(flash, TweenInfo.new(0.5), { Brightness = 0 }):Play()
	end
	local n = 0
	for light, on in pairs(lights) do
		if light.Parent then
			local part = light.Parent
			local near = part:IsA("BasePart") and (part.Position - p).Magnitude < 170
			if light.Enabled ~= near then
				light.Enabled = near
			end
		else
			lights[light] = nil
		end
		n += 1
	end
end)
