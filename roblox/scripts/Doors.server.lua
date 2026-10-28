-- Automatic doors: they open when a player or a shopper comes close and close again when
-- nobody is near. Sliding glass doors (the mall, the hotel, every shop and lobby) are Models
-- named AutoDoor with panels L and R and a NumberValue "Slide" (how far each panel moves, in
-- studs). House doors are Models named SwingDoor whose Leaf swings in on its hinge.
local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")

local RANGE, SWING_RANGE = 14, 9
local INFO = TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
local SWING = CFrame.Angles(0, math.rad(95), 0)

local doors = {}
for _, model in ipairs(workspace:GetDescendants()) do
	if not model:IsA("Model") then
		continue
	end
	local l, r, slide = model:FindFirstChild("L"), model:FindFirstChild("R"), model:FindFirstChild("Slide")
	local leaf = model:FindFirstChild("Leaf")
	if model.Name == "AutoDoor" and l and r and slide then
		table.insert(doors, {
			parts = { l, r },
			closed = { l.CFrame, r.CFrame },
			opened = { l.CFrame * CFrame.new(-slide.Value, 0, 0), r.CFrame * CFrame.new(slide.Value, 0, 0) },
			centre = (l.Position + r.Position) / 2,
			range = RANGE,
			open = false,
		})
	elseif model.Name == "SwingDoor" and leaf then
		-- the leaf's -X end is its hinge; +95 degrees turns its free end towards -Z, into the house
		local hinge = leaf.CFrame * CFrame.new(-leaf.Size.X / 2, 0, 0)
		local turn = hinge * SWING * hinge:Inverse()
		local d = { parts = {}, closed = {}, opened = {}, centre = leaf.Position, range = SWING_RANGE, open = false }
		for _, part in ipairs(model:GetChildren()) do
			if part:IsA("BasePart") then
				table.insert(d.parts, part)
				table.insert(d.closed, part.CFrame)
				table.insert(d.opened, turn * part.CFrame)
			end
		end
		table.insert(doors, d)
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
			if (p - door.centre).Magnitude < door.range then
				near = true
				break
			end
		end
		if near ~= door.open then
			door.open = near
			for i, part in ipairs(door.parts) do
				TweenService:Create(part, INFO, { CFrame = near and door.opened[i] or door.closed[i] }):Play()
			end
		end
	end
	task.wait(0.15)
end
