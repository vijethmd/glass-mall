-- Animates the LED wall, cinema screens and arcade marquees on each player's screen.
local RunService = game:GetService("RunService")

local gradients = {}
local function track(d)
	if d:IsA("UIGradient") and d.Name == "Anim" then
		table.insert(gradients, d)
	end
end
for _, d in ipairs(workspace:GetDescendants()) do
	track(d)
end
workspace.DescendantAdded:Connect(track)

local t = 0
RunService.RenderStepped:Connect(function(dt)
	t = t + dt
	for i = #gradients, 1, -1 do
		local g = gradients[i]
		if g.Parent then
			g.Rotation = (t * 18 + i * 40) % 360
			g.Offset = Vector2.new(math.sin(t * 0.5 + i) * 0.4, 0)
		else
			table.remove(gradients, i)
		end
	end
end)
