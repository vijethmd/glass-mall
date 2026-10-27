-- A full day passes in MINUTES_PER_DAY real minutes. Street lights come on at dusk.
local Lighting = game:GetService("Lighting")

local MINUTES_PER_DAY = 16

local lamps = {}
for _, d in ipairs(workspace.Site.StreetLights:GetDescendants()) do
	if d:IsA("Light") then
		table.insert(lamps, d)
	end
end

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
	end
end
