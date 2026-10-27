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
