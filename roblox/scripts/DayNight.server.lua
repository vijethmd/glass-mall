-- A full day passes in MINUTES_PER_DAY real minutes. At dusk the street lights come on
-- and the city's windows light up; at dawn they go off again.
local Lighting = game:GetService("Lighting")

local MINUTES_PER_DAY = 16
local WARM = Color3.fromRGB(196, 158, 104)

local lamps, windows = {}, {}
for _, d in ipairs(workspace:GetDescendants()) do
	if d:IsA("Light") and d.Name == "NightLight" then
		table.insert(lamps, d)
	elseif d:IsA("BasePart") and d.Name == "Lit window" then
		table.insert(windows, { part = d, color = d.Color, material = d.Material })
	end
end

-- the monsoon: every few minutes it may rain for a couple of minutes. The server says so with
-- workspace's Weather attribute; FX.client and Ambience.client make the rain and its sound.
local TweenService = game:GetService("TweenService")
local atmosphere = Lighting:FindFirstChildOfClass("Atmosphere")
local grade = Lighting:FindFirstChild("Grade")
workspace:SetAttribute("Weather", "Clear")
local CLEAR = {
	atmosphere = atmosphere and { Density = atmosphere.Density, Haze = atmosphere.Haze, Color = atmosphere.Color },
	grade = grade and { Saturation = grade.Saturation, Brightness = grade.Brightness },
	clouds = { Cover = 0.55, Density = 0.65, Color = Color3.fromRGB(245, 245, 248) },
}
local WET = {
	atmosphere = { Density = 0.45, Haze = 2.6, Color = Color3.fromRGB(150, 156, 166) },
	grade = { Saturation = -0.15, Brightness = -0.05 },
	clouds = { Cover = 0.92, Density = 0.95, Color = Color3.fromRGB(120, 124, 134) },
}
local function weather(look, seconds)
	local info = TweenInfo.new(seconds)
	if atmosphere and look.atmosphere then
		TweenService:Create(atmosphere, info, look.atmosphere):Play()
	end
	if grade and look.grade then
		TweenService:Create(grade, info, look.grade):Play()
	end
	local clouds = workspace.Terrain:FindFirstChildOfClass("Clouds")
	if clouds then
		TweenService:Create(clouds, info, look.clouds):Play()
	end
end
task.spawn(function()
	while true do
		task.wait(math.random(200, 380))
		if math.random() < 0.4 then
			weather(WET, 20)
			task.wait(12)
			workspace:SetAttribute("Weather", "Rain")
			task.wait(math.random(90, 160))
			workspace:SetAttribute("Weather", "Clear")
			weather(CLEAR, 25)
		end
	end
end)

local wasNight = nil
while true do
	local dt = task.wait(0.1)
	Lighting.ClockTime = (Lighting.ClockTime + dt * 24 / (MINUTES_PER_DAY * 60)) % 24
	local t = Lighting.ClockTime
	local night = t < 6.3 or t > 17.8
	if night ~= wasNight then
		wasNight = night
		for _, lamp in ipairs(lamps) do
			lamp.Enabled = night
			if lamp.Parent:IsA("BasePart") then
				lamp.Parent.Material = night and Enum.Material.Neon or Enum.Material.SmoothPlastic
			end
		end
		for i, w in ipairs(windows) do
			w.part.Material = night and Enum.Material.Neon or w.material
			w.part.Color = night and WARM:Lerp(w.color, 0.3) or w.color
			if i % 250 == 0 then
				task.wait()
			end
		end
	end
end
