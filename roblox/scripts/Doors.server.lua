-- Automatic sliding doors: they open when a player or a shopper comes close and
-- close again when nobody is near. Each door is a Model with panels L and R and
-- a NumberValue "Slide" (how far each panel moves, in studs).
local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")

local RANGE = 14
local INFO = TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)

local doors = {}
for _, model in ipairs(workspace.Mall.Doors:GetChildren()) do
	local l, r, slide = model:FindFirstChild("L"), model:FindFirstChild("R"), model:FindFirstChild("Slide")
	if l and r and slide then
		table.insert(doors, {
			l = l,
			r = r,
			lClosed = l.CFrame,
			rClosed = r.CFrame,
			lOpen = l.CFrame * CFrame.new(-slide.Value, 0, 0),
			rOpen = r.CFrame * CFrame.new(slide.Value, 0, 0),
			centre = (l.Position + r.Position) / 2,
			open = false,
		})
	end
end

local function walkers()
	local list = {}
	for _, player in ipairs(Players:GetPlayers()) do
		local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
		if root then
			table.insert(list, root.Position)
		end
	end
	local shoppers = workspace:FindFirstChild("Shoppers")
	if shoppers then
		for _, npc in ipairs(shoppers:GetChildren()) do
			local root = npc:FindFirstChild("HumanoidRootPart")
			if root then
				table.insert(list, root.Position)
			end
		end
	end
	return list
end

while true do
	local here = walkers()
	for _, door in ipairs(doors) do
		local near = false
		for _, p in ipairs(here) do
			if (p - door.centre).Magnitude < RANGE then
				near = true
				break
			end
		end
		if near ~= door.open then
			door.open = near
			TweenService:Create(door.l, INFO, { CFrame = near and door.lOpen or door.lClosed }):Play()
			TweenService:Create(door.r, INFO, { CFrame = near and door.rOpen or door.rClosed }):Play()
		end
	end
	task.wait(0.15)
end
